from google.adk.agents import Agent
from Mathematical.MCP.math_toolsets import division_toolset
import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
division_agent = Agent(
    name="division_agent",
    model="gemini-2.5-pro",
    instruction="You are an division assistant. Use the MCP tool for all division operations.",
    tools=[division_toolset]
)
