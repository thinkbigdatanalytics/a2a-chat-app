from google.adk.agents import Agent
from MCP.math_toolsets import multiplication_toolset

multiplicaion_agent = Agent(
    name="multiplicaion_agent",
    model="gemini-2.5-pro",
    instruction="You are an multiplicaion assistant. Use the MCP tool for all multiplicaion operations.",
    tools=[multiplication_toolset]
)
