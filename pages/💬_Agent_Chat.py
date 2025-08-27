import io
import json
import os
import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from mcp import StdioServerParameters
from openai import AsyncAzureOpenAI, AsyncOpenAI
from agents import Agent, set_default_openai_client, ItemHelpers, OpenAIChatCompletionsModel,Model
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from Mathematical.MCP.math_toolsets import TimeoutMCPToolset
from db import get_all_agents, get_all_tools_by_id, Agents, get_session, get_agent_config
from dotenv import load_dotenv
import anyio
from agents.run import Runner
from agents import trace
load_dotenv()

api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

if not all([api_key, api_version, endpoint, deployment]):
    st.error("Azure OpenAI API credentials are not fully set in .env!")
    st.stop()

client = AsyncAzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=endpoint,
    azure_deployment=deployment,
)
set_default_openai_client(client)

def export_to_pdf(qas):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    textobject = c.beginText(50, 750)
    textobject.setFont("Helvetica", 12)
    for i, (q, a) in enumerate(qas, 1):
        textobject.textLine(f"Q{i}: {q}")
        textobject.textLine(f"A{i}: {a}")
        textobject.textLine("")
    c.drawText(textobject)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

def export_to_csv(data_list):
    if not data_list:
        return None
    df = pd.DataFrame(data_list, columns=["Question", "Answer"])
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.getvalue()

def export_to_excel(data_list):
    if not data_list:
        return None
    df = pd.DataFrame(data_list, columns=["Question", "Answer"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Q&A")
    buf.seek(0)
    return buf.getvalue()

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PdfReader(uploaded_file)
        return "\n".join([p.extract_text() for p in pdf_reader.pages if p.extract_text()])
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=0, usecols=[0])
        return "\n".join(df.iloc[:, 0].dropna().tolist())
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file, header=0, usecols=[0])
        return "\n".join(df.iloc[:, 0].dropna().tolist())
    return ""

class NamedMCPToolset(MCPToolset):
    def __init__(self, name: str, connection_params, **kwargs):
        super().__init__(connection_params=connection_params, **kwargs)
        self._name = name

    @property
    def name(self):
        return self._name


def initiate_toolset(tool_name: str, command: str, timeout: int = 3000, env: dict = None, **kwargs) -> NamedMCPToolset:
    env = env or {}

    if command == "npx":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="npx", args=[kwargs.get("npx_command", "")]),
            timeout=timeout,
            env=env
        )
    elif command == "http":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="curl", args=[kwargs.get("url", "")]),
            timeout=timeout,
            env=env
        )
    elif command == "sse":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="sse-client", args=[kwargs.get("sse_url", "")]),
            timeout=timeout,
            env=env
        )
    elif command == "stdio":
        script_cmd = kwargs.get("command")
        script_args = kwargs.get("args", [])
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command=script_cmd, args=script_args),
            timeout=timeout,
            env=env
        )
    elif command == "python":
        script_path = kwargs.get("script_path", "").replace("\\", "/")
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="python", args=[script_path]),
            timeout=timeout,
            env=env
        )
    else:
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command=command, args=[kwargs.get("path", "")]),
            timeout=timeout,
            env=env
        )

    print(f"[DEBUG] Initiating MCP toolset '{tool_name}' with command '{command}', args {kwargs}, env {env}")
    return NamedMCPToolset(name=tool_name, connection_params=conn_params)


def load_agent_from_db(agent_id: int, provider: str = None):
    with get_session() as session:
        row = get_agent_config(agent_id, provider)
        print(f"[DEBUG] Loading agent '{row}'")
        if not row:
            print(f"[load_agent_from_db] Agent {agent_id} not found for provider={provider}")
            return None

        tool_rows = get_all_tools_by_id(agent_id)
        print(f"tool_rows:{tool_rows}")
        toolsets = []
        for t_name, command, args, env_json in tool_rows:
            env_vars = json.loads(env_json) if env_json else {}
            kwargs = {}
            if command == "npx":
                kwargs = {"npx_command": args}
            elif command == "http":
                kwargs = {"url": args}
            elif command == "sse":
                kwargs = {"sse_url": args}
            elif command == "stdio":
                parts = args.split()
                kwargs = {"command": parts[0], "args": parts[1:]}
            elif command == "python":
                kwargs = {"script_path": args}
            else:
                kwargs = {"path": args}

            toolsets.append(
                initiate_toolset(t_name, command, timeout=3000, env=env_vars, **kwargs)
            )

        scope = (row.scope or "All Agents").strip()
        provider_name = (provider or row.provider).lower()

        print(f"[Agent Config] agent_id={agent_id}, provider={provider_name}, model={row.model}, scope={scope}")

        if provider_name == "azure_openai":
            client = AsyncAzureOpenAI(
                api_key=row.api_key,
                api_version=row.AZURE_OPENAI_API_VERSION,
                azure_endpoint=row.AZURE_OPENAI_ENDPOINT,
                azure_deployment=row.AZURE_OPENAI_DEPLOYMENT,
            )
            model_name = row.model or row.AZURE_OPENAI_DEPLOYMENT

        elif provider_name == "google":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=row.api_key)
            model_name = row.model or "gemini-2.0-pro"

        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

        agent = Agent(
            name=row.provider or f"agent_{agent_id}",
            model=OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=client,
            ),
            instructions=row.instruction or "No instruction.",
            tools=toolsets ,
        )
        print(agent)
        print(f"[Agent Ready] {agent.name} with provider={provider_name}, model={model_name}, scope={scope}")
        return agent, scope


st.title("Math + File Assistant")
st.sidebar.header("Agent Settings")

agents = get_all_agents()
print(f"all_agents: {agents}")
agent_dict = {a[1]: a[0] for a in agents}
selected_agent_names = st.sidebar.multiselect(
    "Choose Agents", list(agent_dict.keys()) if agents else []
)
selected_agent_ids = [agent_dict[name] for name in selected_agent_names]
print(f"selected_agent")
sub_agents = []
for aid in selected_agent_ids:
    res = load_agent_from_db(aid)
    if res:
        agent, scope = res
        sub_agents.append(agent)

main_res = load_agent_from_db(1)
if not main_res:
    st.error("Main agent not found in DB. Please configure it.")
    st.stop()

main_agent, main_scope = main_res
main_agent.handoffs = sub_agents

print(f"sub_agent : {sub_agents}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "questions_list" not in st.session_state:
    st.session_state.questions_list = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_msg = st.chat_input("Ask me anything about Math or upload a file...", accept_file=True)
if user_msg:
    user_text = getattr(user_msg, "text", "")
    if getattr(user_msg, "files", None):
        file_text = "\n".join(extract_text_from_file(f) for f in user_msg.files)
        if file_text:
            st.session_state.questions_list = [q.strip() for q in file_text.split("\n") if q.strip()]
            st.session_state.current_q = 0
    elif user_text:
        st.session_state.questions_list = [user_text]
        st.session_state.current_q = 0


async def get_openai_response(agent, query, context=None):
    with trace(workflow_name="Math + File Assistant Workflow", group_id="session-001"):
        result = await Runner.run(
            starting_agent=agent,
            input=query,
            context=context or {},
        )
    return ItemHelpers.text_message_outputs(result.new_items)


if st.session_state.questions_list and st.session_state.current_q < len(st.session_state.questions_list):
    q = st.session_state.questions_list[st.session_state.current_q]
    q_num = st.session_state.current_q + 1
    st.session_state.messages.append({"role": "user", "content": q})
    st.chat_message("user").markdown(f"**Q{q_num}:** {q}")

    answer = anyio.run(get_openai_response, main_agent, q)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").markdown(f"**A{q_num}:** {answer}")

    st.session_state.current_q += 1
    st.rerun()