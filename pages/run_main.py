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
    class TimeoutMCPToolset(MCPToolset):
        def __init__(self, *, tool_name: str, connection_params, timeout=30, **kwargs):
            self.tool_name = tool_name
            if isinstance(connection_params, StdioConnectionParams):
                connection_params = StdioConnectionParams(
                    server_params=connection_params.server_params,
                    timeout=timeout,
                )
            super().__init__(connection_params=connection_params, **kwargs)

    if command == "npx":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="npx", args=[kwargs["npx_command"]]),
            timeout=timeout,
        )
    elif command == "http":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="curl", args=[kwargs["url"]]),
            timeout=timeout,
        )
    elif command == "sse":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="sse-client", args=[kwargs["sse_url"]]),
            timeout=timeout,
        )
    elif command == "stdio":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command=kwargs["command"], args=kwargs["args"]),
            timeout=timeout,
        )
    elif command == "python":
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command="python", args=[kwargs["script_path"]]),
            timeout=timeout,
        )
    else:
        conn_params = StdioConnectionParams(
            server_params=StdioServerParameters(command=command, args=[kwargs.get("path", "")]),
            timeout=timeout,
        )

    return TimeoutMCPToolset(tool_name=tool_name, connection_params=conn_params, timeout=timeout)


def load_agent_from_db(agent_id):
    from db import get_session, Agent
    with get_session() as session:
        agent = session.query(Agent).filter(Agent.id == agent_id).first()
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

    return {
        "id": agent.id,
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

os.environ["GOOGLE_API_KEY"] = "YOUR_KEY_HERE"

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
        instruction="""You are the math supervisor agent. 
        Delegate addition → `add_agent`, subtraction → `sub_agent`.
        Split mixed queries and combine answers.""",
        sub_agents=sub_agents
    )
    runner = Runner(app_name=APP_NAME, agent=main_agent, session_service=session_service)

st.sidebar.header("Upload File (PDF, CSV, Excel)")
uploaded_file = st.sidebar.file_uploader("Upload", type=["pdf", "csv", "xlsx"])
file_context = ""
if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        pdf_reader = PdfReader(uploaded_file)
        file_context = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        st.success("PDF processed")
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file); file_context = df.to_string(); st.success("CSV processed")
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file); file_context = df.to_string(); st.success("Excel processed")

if "messages" not in st.session_state:
    st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def save_to_pdf(filename, question_text, answer_text):
    c = canvas.Canvas(filename, pagesize=letter)
    textobject = c.beginText(50, 750)
    textobject.setFont("Helvetica", 12)
    textobject.textLine("Question:"); [textobject.textLine(l) for l in question_text.splitlines()]
    textobject.textLine(""); textobject.textLine("Answer:"); [textobject.textLine(l) for l in answer_text.splitlines()]
    c.drawText(textobject); c.showPage(); c.save()

if user_msg := st.chat_input("Ask me about Math or uploaded file..."):
    if not runner:
        st.error("Select an agent first")
    else:
        user_text = str(user_msg)
        st.session_state.messages.append({"role": "user", "content": user_text})
        st.chat_message("user").markdown(user_text)

        content = types.Content(role="user", parts=[types.Part(text=user_text)])
        assistant_reply = run_async(get_ai_response(runner, content))

        output_file = "assistant_reply.pdf"
        save_to_pdf(output_file, user_text, assistant_reply)

        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        st.chat_message("assistant").markdown(assistant_reply)

        with open(output_file, "rb") as f:
            st.download_button("Download Reply as PDF", data=f, file_name="assistant_reply.pdf", mime="application/pdf")
