import io

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams, StdioServerParameters
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

import os, asyncio, streamlit as st, pandas as pd
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from db import get_all_agents, get_all_tools_by_id


def initiate_toolset(tool_name: str, command: str, timeout: int = 3000, **kwargs) -> MCPToolset:
    """
    Initiates an MCPToolset with different connection types.

    Args:
        tool_name: Name of the toolset
        command: Type of command (npx, http, sse, stdio, python, or custom)
        timeout: Connection timeout in seconds
        **kwargs: Additional parameters depending on command type
            - npx: npx_command
            - http: url
            - sse: sse_url
            - stdio: command, args (list)
            - python: script_path
            - custom: path (optional)

    Returns:
        MCPToolset instance
    """

    class TimeoutMCPToolset(MCPToolset):
        def __init__(self, *, tool_name: str, connection_params, timeout=30, **kwargs):
            self.tool_name = tool_name
            # Wrap StdioConnectionParams with timeout
            if isinstance(connection_params, StdioConnectionParams):
                connection_params = StdioConnectionParams(
                    server_params=connection_params.server_params,
                    timeout=timeout,
                )
            super().__init__(connection_params=connection_params, **kwargs)

    # Determine connection parameters based on command
    if command == "npx":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="npx", args=[kwargs.get("npx_command", "")]),
            timeout=timeout,
        )
    elif command == "http":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="curl", args=[kwargs.get("url", "")]),
            timeout=timeout,
        )
    elif command == "sse":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="sse-client", args=[kwargs.get("sse_url", "")]),
            timeout=timeout,
        )
    elif command == "stdio":
        script_cmd = kwargs.get("command")
        script_args = kwargs.get("args", [])
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command=script_cmd, args=script_args),
            timeout=timeout,
        )
    elif command == "python":
        script_path = kwargs.get("script_path", "")
        # Ensure path works in Linux/Windows
        script_path = script_path.replace("\\", "/")
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="python", args=[script_path]),
            timeout=timeout,
        )
    else:
        # Fallback for custom commands
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command=command, args=[kwargs.get("path", "")]),
            timeout=timeout,
        )

    print(f"[DEBUG] Initiating toolset '{tool_name}' with command '{command}' and args {kwargs}")
    return TimeoutMCPToolset(tool_name=tool_name, connection_params=conn_params, timeout=timeout)
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
    df = pd.DataFrame(data_list)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.getvalue()  # return str for CSV

def export_to_excel(data_list):
    if not data_list:
        return None
    df = pd.DataFrame(data_list)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    buf.seek(0)
    return buf.getvalue()  # return bytes for Excel


def load_agent_from_db(agent_id):
    from db import get_session, Agents
    with get_session() as session:
        agent = session.query(Agents).filter(Agents.id == agent_id).first()
        if not agent:
            return None

    tool_rows = get_all_tools_by_id(agent_id)
    toolsets = []

    for t_name, command, args in tool_rows:
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
            initiate_toolset(tool_name=t_name, command=command, timeout=3000, **kwargs)
        )

    if agent.api_key:
        if agent.provider.lower() == "google":
            os.environ["GOOGLE_API_KEY"] = agent.api_key
        elif agent.provider.lower() == "openai":
            os.environ["OPENAI_API_KEY"] = agent.api_key
        elif agent.provider.lower() == "azure_openai":
            os.environ["AZURE_OPENAI_API_KEY"] = agent.api_key
        elif agent.provider.lower() == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = agent.api_key
        elif agent.provider.lower() == "mistral":
            os.environ["MISTRAL_API_KEY"] = agent.api_key
        elif agent.provider.lower() == "local":
            os.environ["LOCAL_MODEL_PATH"] = agent.api_key

    return {
        "id": agent.id,
        "provider": agent.provider,
        "agent": Agent(
            name=agent.name,
            model=agent.model,
            instruction=agent.instruction,
            tools=toolsets
        )
    }

APP_NAME = "math_app"
USER_ID = "user1"
SESSION_ID = "session_1"

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"

session_service = InMemorySessionService()
session_service.create_session_sync(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)

async def get_ai_response(runner, content: types.Content) -> str:
    async for ev in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
        if ev.is_final_response() and ev.content and getattr(ev.content, "parts", None):
            text_parts = [p.text for p in ev.content.parts if getattr(p, "text", None)]
            return "\n".join(text_parts) if text_parts else "[No text in final response]"
    return "[No final response]"

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    if loop.is_running():
        return asyncio.ensure_future(coro)
    else:
        return loop.run_until_complete(coro)

st.title("Math + File Assistant")

st.sidebar.header("Agent Settings")
agents = get_all_agents()
agent_dict = {a[1]: a[0] for a in agents}
selected_agent_names = st.sidebar.multiselect("Choose Agents", list(agent_dict.keys()) if agents else [])
selected_agent_ids = [agent_dict[name] for name in selected_agent_names]

sub_agents = []
for agent_id in selected_agent_ids:
    agent_data = load_agent_from_db(agent_id)
    if agent_data:
        sub_agents.append(agent_data["agent"])

main_agent, runner = None, None
if sub_agents:
    main_agent = Agent(
        name="main_math_agent",
        model="gemini-2.5-pro",
        instruction="""
        You are the main math agent.
        - Always reply in proper grammar, using a full sentence.
        - Keep the response short and generic, like: 
          "The answer is 14." or "That comes out to 20."
        - Do not just return the number.
        - Use sub-agents for solving problems.
        - If the operation is not supported, reply: "I don’t have knowledge in this."
        """,
    sub_agents=sub_agents
    )
    runner = Runner(app_name=APP_NAME, agent=main_agent, session_service=session_service)

# st.sidebar.header("Upload File (PDF, CSV, Excel)")
# uploaded_file = st.sidebar.file_uploader("Upload", type=["pdf", "csv", "xlsx"])
# file_context = ""
# if uploaded_file:
#     if uploaded_file.name.endswith(".pdf"):
#         pdf_reader = PdfReader(uploaded_file)
#         file_context = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
#         st.success("PDF processed")
#     elif uploaded_file.name.endswith(".csv"):
#         df = pd.read_csv(uploaded_file); file_context = df.to_string(); st.success("CSV processed")
#     elif uploaded_file.name.endswith(".xlsx"):
#         df = pd.read_excel(uploaded_file); file_context = df.to_string(); st.success("Excel processed")

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])

    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=0, usecols=[0])   # only first column, skip header
        questions = df.iloc[:, 0].dropna().tolist()
        return "\n".join(questions)

    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file, header=0, usecols=[0]) # only first column, skip header
        questions = df.iloc[:, 0].dropna().tolist()
        return "\n".join(questions)

    else:
        return ""

if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "content" in msg:
            if isinstance(msg["content"], str):
                st.markdown(msg["content"])
            elif hasattr(msg["content"], "parts"):
                text_parts = [p.text for p in msg["content"].parts if getattr(p, "text", None)]
                st.markdown("\n".join(text_parts))

def save_to_pdf(filename, question_text, answer_text):
    c = canvas.Canvas(filename, pagesize=letter)
    textobject = c.beginText(50, 750)
    textobject.setFont("Helvetica", 12)
    textobject.textLine("Question:"); [textobject.textLine(l) for l in question_text.splitlines()]
    textobject.textLine(""); textobject.textLine("Answer:"); [textobject.textLine(l) for l in answer_text.splitlines()]
    c.drawText(textobject); c.showPage(); c.save()


if "questions_list" not in st.session_state:
    st.session_state.questions_list = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0

if user_msg := st.chat_input(
    placeholder="Ask me anything about Math or upload a file...", accept_file=True
):
    user_text = user_msg.text if hasattr(user_msg, "text") else ""

    if any(fmt in user_text.lower() for fmt in ["pdf", "csv", "excel", "xlsx"]):
        qas = []
        questions = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
        answers = [m["content"] for m in st.session_state.messages if m["role"] == "assistant"]

        for i, q in enumerate(questions):
            a = answers[i] if i < len(answers) else ""
            qas.append((q, a))

        if qas:
            if "pdf" in user_text.lower():
                buf = export_to_pdf(qas)
                st.download_button("Download PDF", buf, file_name="qa_output.pdf")

            elif "csv" in user_text.lower():
                csv_data = export_to_csv(qas)
                st.download_button(
                    "Download CSV",
                    data=csv_data,
                    file_name="qa_output.csv",
                    mime="text/csv"
                )

            elif "excel" in user_text.lower() or "xlsx" in user_text.lower():
                excel_data = export_to_excel(qas)
                st.download_button(
                    "Download Excel",
                    data=excel_data,
                    file_name="qa_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("No Q&A pairs available to export yet.")


    else:
        file_context = ""
        if getattr(user_msg, "files", None):
            for f in user_msg.files:
                file_context += extract_text_from_file(f)

            if file_context:
                st.success("File processed successfully!")
                st.session_state.questions_list = [
                    q.strip() for q in file_context.split("\n") if q.strip()
                ]
                st.session_state.current_q = 0
        else:
            if user_text:
                st.session_state.questions_list = [user_text]
                st.session_state.current_q = 0


if runner and st.session_state.questions_list:
    if st.session_state.current_q < len(st.session_state.questions_list):
        q = st.session_state.questions_list[st.session_state.current_q]
        q_num = st.session_state.current_q + 1

        st.session_state.messages.append({"role": "user", "content": q})
        st.chat_message("user").markdown(f"**Q{q_num}:** {q}")

        parts = [types.Part(text=q)]
        content = types.Content(role="user", parts=parts)
        answer = run_async(get_ai_response(runner, content))

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.chat_message("assistant").markdown(f"**A{q_num}:** {answer}")

        st.session_state.current_q += 1
        st.rerun()