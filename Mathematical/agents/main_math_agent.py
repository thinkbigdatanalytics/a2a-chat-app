from datetime import datetime

from google.adk.agents import Agent
import os

from Mathematical.agents.All_Agent import all_agents

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"
main_math_agent = Agent(
    name="main_math_agent",
    model="gemini-2.5-pro",
    instruction="""
    You are the main math coordinator.
    - If the user asks for addition, delegate to `add_agent`.
    - If the user asks for subtraction, delegate to `sub_agent`.
    - If the user asks for multiplication, delegate to `mul_agent`.
    - If the user asks for division, delegate to `div_agent`.
    You MUST not solve the problem yourself. Always route to the correct sub-agent.
    """,
    sub_agents=all_agents
)

print(f"[{datetime.now()}] Main agent initialized with sub-agents: {[a.name for a in all_agents]}")
