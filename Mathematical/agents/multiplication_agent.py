from google.adk.agents import Agent
from Mathematical.MCP.math_toolsets import multiplication_toolset
import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
multiplicaion_agent = Agent(
    name="multiplicaion_agent",
    model="gemini-2.5-pro",
    instruction="You are an multiplicaion assistant. Use the MCP tool for all multiplicaion operations.",
    tools=[multiplication_toolset]
)
