# run_main.py
import asyncio
import os
import uuid
import streamlit as st

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from Mathematical.agents.main_math_agent import main_math_agent

# ---------------- CONFIG ----------------
APP_NAME = "math_app"
USER_ID = "user1"   # could be dynamic later
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"

# ---------------- SESSION SETUP ----------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())  # unique per browser session

SESSION_ID = st.session_state.session_id

session_service = InMemorySessionService()
session_service.create_session_sync(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)

runner = Runner(
    app_name=APP_NAME,
    agent=main_math_agent,
    session_service=session_service
)

# ---------------- HELPER FUNCTIONS ----------------
async def get_ai_response(runner, user_msg):
    """Send user_msg to agent and capture delegation trace + final response."""
    content = types.Content(role="user", parts=[types.Part(text=user_msg)])
    trace = []

    if hasattr(runner, "run_async"):
        async for ev in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            # Capture delegation info
            if hasattr(ev, "sender") and hasattr(ev, "receiver"):
                trace.append(f"{ev.sender} → {ev.receiver}")

            # Capture final response
            if ev.is_final_response() and ev.content and getattr(ev.content, "parts", None):
                text_parts = [p.text for p in ev.content.parts if getattr(p, "text", None)]
                reply = "\n".join(text_parts) if text_parts else "[No text in final response]"
                return reply + ("\n\nTrace: " + " → ".join(trace) if trace else "")
    else:
        for ev in runner.run(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if hasattr(ev, "sender") and hasattr(ev, "receiver"):
                trace.append(f"{ev.sender} → {ev.receiver}")

            if ev.is_final_response() and ev.content and getattr(ev.content, "parts", None):
                text_parts = [p.text for p in ev.content.parts if getattr(p, "text", None)]
                reply = "\n".join(text_parts) if text_parts else "[No text in final response]"
                return reply + ("\n\nTrace: " + " → ".join(trace) if trace else "")

    return "[No final response received]"


def run_async(coro):
    """Run async function safely inside Streamlit."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)

# ---------------- STREAMLIT UI ----------------
st.title("🤖 Math Multi-Agent Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
if user_msg := st.chat_input("Ask me anything about Math (add, sub, mul, div)..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.chat_message("user").markdown(user_msg)

    try:
        assistant_reply = asyncio.run(get_ai_response(runner, user_msg))
    except Exception as e:
        assistant_reply = f"⚠️ Error: {str(e)}"

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.chat_message("assistant").markdown(assistant_reply)
