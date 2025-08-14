from Mathematical.MCP.math_toolsets import addition_toolset, subtraction_toolset, multiplication_toolset, division_toolset
from google.adk.agents import Agent
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
main_math_agent = Agent(
    name="math_agent",
    model="gemini-2.5-pro",
    instruction="You are a math assistant. Use MCP tools for calculations.",
    tools=[
        addition_toolset,
        subtraction_toolset,
        multiplication_toolset,
        division_toolset
    ]
)
