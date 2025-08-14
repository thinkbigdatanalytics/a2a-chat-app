import asyncio
import os
import streamlit as st
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from Mathematical.agents.main_math_agent import main_math_agent

APP_NAME = "math_app"
USER_ID = "user1"
SESSION_ID = "session_1"
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"

# Create session
session_service = InMemorySessionService()
session_service.create_session_sync(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)

# Create runner
runner = Runner(
    app_name=APP_NAME,
    agent=main_math_agent,
    session_service=session_service
)

def choose_agent_and_runner(user_text):
    return runner

async def get_ai_response(runner, user_msg):
    content = types.Content(role="user", parts=[types.Part(text=user_msg)])
    if hasattr(runner, "run_async"):
        async for ev in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if ev.is_final_response() and ev.content and getattr(ev.content, "parts", None):
                text_parts = [p.text for p in ev.content.parts if getattr(p, "text", None)]
                return "\n".join(text_parts) if text_parts else "[No text in final response]"
    else:
        for ev in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if ev.is_final_response() and ev.content and getattr(ev.content, "parts", None):
                text_parts = [p.text for p in ev.content.parts if getattr(p, "text", None)]
                return "\n".join(text_parts) if text_parts else "[No text in final response]"
    return "[No final response received]"

def run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

st.title("MATH Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_msg := st.chat_input("Ask me anything about Math function..."):
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.chat_message("user").markdown(user_msg)

    runner = choose_agent_and_runner(user_msg)
    assistant_reply = run_async(get_ai_response(runner, user_msg))

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.chat_message("assistant").markdown(assistant_reply)
