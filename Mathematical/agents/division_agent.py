from google.adk.agents import Agent
from MCP.math_toolsets import division_toolset

division_agent = Agent(
    name="division_agent",
    model="gemini-2.5-pro",
    instruction="You are an division assistant. Use the MCP tool for all division operations.",
    tools=[division_toolset]
)
