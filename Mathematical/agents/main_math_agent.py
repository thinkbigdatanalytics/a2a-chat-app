from google.adk.agents import Agent
from agents.addition_agent import addition_agent
from agents.subraction_agent import subtraction_agent
from agents.multiplication_agent import multiplicaion_agent
from agents.division_agent import division_agent
import os
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
all_tools = (
    addition_agent.tools +
    subtraction_agent.tools +
    multiplicaion_agent.tools +
    division_agent.tools
)

main_math_agent = Agent(
    name="main_math_agent",
    model="gemini-2.5-pro",
    instruction=(
        "You are a math assistant that can perform addition, subtraction, "
        "multiplication, and division. Select the correct tool based on the user's request."
    ),
    tools=all_tools
)
