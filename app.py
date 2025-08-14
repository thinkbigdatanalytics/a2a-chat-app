import os
import streamlit as st
import asyncio
import nest_asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters

nest_asyncio.apply()

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
APP_NAME = "streamlit_adk"
USER_ID = "user"
SESSION_ID = "session_1"

github_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={
                "GITHUB_PERSONAL_ACCESS_TOKEN": "GITHUB API"
            }
        )
    )
)

math_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\main_app.py"]
        )
    ),
)


math_agent = Agent(
    name="math_agent",
    model="gemini-2.5-pro",
    instruction="You are a math assistant. Use MCP tools for mathematical operations.",
    tools=[math_toolset]
)

github_agent = Agent(
    name="github_agent",
    model="gemini-2.5-pro",
    instruction="""
You are a GitHub assistant. Use the MCP tool for all GitHub actions.
Default to using 'AnishkumarRose' for repositories, branches, pull requests, issues, commits, and other actions unless I say otherwise.
""",
    tools=[github_toolset]
)

session_service = InMemorySessionService()
session_service.create_session_sync(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)

runner_github = Runner(
    app_name=APP_NAME,
    agent=github_agent,
    session_service=session_service
)

runner_math = Runner(
    app_name=APP_NAME,
    agent=math_agent,
    session_service=session_service
)

def choose_agent_and_runner(user_text: str):
    text_lower = user_text.lower()
    math_keywords = ["add", "sum", "subtract", "minus", "multiply", "times", "divide", "+", "-", "*", "/"]

    if any(keyword in text_lower for keyword in math_keywords):
        return runner_math
    return runner_github

async def get_ai_response(runner, user_msg):
    content = types.Content(role="user", parts=[types.Part(text=user_msg)])
    events = runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    )
    async for ev in events:
        if ev.is_final_response() and ev.content and getattr(ev.content, "parts", None):
            text_parts = [p.text for p in ev.content.parts if getattr(p, "text", None)]
            return "\n".join(text_parts) if text_parts else "[No text in final response]"
    return "[No final response received]"

st.title("Multi-Agent Assistant (GitHub + Math)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_msg := st.chat_input("Ask me about GitHub or math..."):
    # Save & show user message
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.chat_message("user").markdown(user_msg)

    runner = choose_agent_and_runner(user_msg)

    assistant_reply = asyncio.get_event_loop().run_until_complete(
        get_ai_response(runner, user_msg)
    )

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.chat_message("assistant").markdown(assistant_reply)
