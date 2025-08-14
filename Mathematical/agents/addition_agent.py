from google.adk.agents import Agent
from MCP.math_toolsets import addition_toolset

import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
addition_agent = Agent(
    name="addition_agent",
    model="gemini-2.5-pro",
    instruction="You are an addition assistant. Use the MCP tool for all addition operations.",
    tools=[addition_toolset]
)
