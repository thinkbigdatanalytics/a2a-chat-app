import streamlit as st
import subprocess
import json
import asyncio
from google.adk.agents import Agent
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

if not GOOGLE_API_KEY or not GITHUB_TOKEN:
    st.error("Missing API keys. Please set GOOGLE_API_KEY and GITHUB_PERSONAL_ACCESS_TOKEN in .env")
    st.stop()

os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

gemini_agent = Agent(
    name="geminiagent",
    model="gemini-2.5-pro",
    instruction="You are a helpful assistant. If the user wants to perform GitHub actions, tell the app to call the MCP server."
)

MCP_CONFIG = {
    "command": "docker",
    "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
    ],
    "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN
    }
}

async def call_gemini(prompt: str):
    response = await gemini_agent.run(prompt)
    return getattr(response, "output_text", str(response))

def call_mcp_server(prompt: str):
    try:
        proc = subprocess.Popen(
            [MCP_CONFIG["command"]] + MCP_CONFIG["args"],
            env={**MCP_CONFIG["env"], **os.environ},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        proc.stdin.write(prompt + "\n")
        proc.stdin.close()

        output, error = proc.communicate()
        if error:
            return f"MCP Error: {error}"
        return output.strip()
    except Exception as e:
        return f"MCP Exception: {str(e)}"

def is_github_related(text: str) -> bool:
    keywords = ["repo", "repository", "github", "pull request", "issue"]
    return any(word in text.lower() for word in keywords)

st.set_page_config(page_title="Gemini + GitHub MCP")
st.title("Gemini + GitHub MCP Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if is_github_related(prompt):
        with st.chat_message("assistant"):
            st.markdown("Sending to GitHub MCP server...")
        mcp_response = call_mcp_server(prompt)
        st.session_state.messages.append({"role": "assistant", "content": mcp_response})
        with st.chat_message("assistant"):
            st.markdown(mcp_response)
    else:
        with st.chat_message("assistant"):
            st.markdown("Asking Gemini...")
        gemini_response = asyncio.run(call_gemini(prompt))
        st.session_state.messages.append({"role": "assistant", "content": gemini_response})
        with st.chat_message("assistant"):
            st.markdown(gemini_response)
