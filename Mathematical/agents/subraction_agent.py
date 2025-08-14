from google.adk.agents import Agent
from MCP.math_toolsets import subtraction_toolset

subtraction_agent = Agent(
    name="subtraction_agent",
    model="gemini-2.5-pro",
    instruction="You are an subtraction assistant. Use the MCP tool for all subtraction operations.",
    tools=[subtraction_toolset]
)
