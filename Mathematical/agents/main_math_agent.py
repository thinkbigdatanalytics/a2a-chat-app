from google.adk.agents import Agent
import os

from Mathematical.agents.addition_agent import addition_agent
from Mathematical.agents.division_agent import division_agent
from Mathematical.agents.multiplication_agent import multiplicaion_agent
from Mathematical.agents.subraction_agent import subtraction_agent

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
main_math_agent = Agent(
    name="math_agent",
    model="gemini-2.5-pro",
    instruction="You are a math assistant. Use MCP tools for calculations.",
    sub_agents=[addition_agent,subtraction_agent,multiplicaion_agent,division_agent]
)
