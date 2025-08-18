# All_Agent.py
import os
import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"

# ✅ Define bare agents (no tools yet)
add_agent = Agent(
    name="add_agent",
    model="gemini-2.5-pro",
    instruction="You are an addition assistant. Always use the MCP `add` tool."
)

sub_agent = Agent(
    name="sub_agent",
    model="gemini-2.5-pro",
    instruction="You are a subtraction assistant. Always use the MCP `sub` tool."
)

mul_agent = Agent(
    name="mul_agent",
    model="gemini-2.5-pro",
    instruction="You are a multiplication assistant. Always use the MCP `mul` tool."
)

div_agent = Agent(
    name="div_agent",
    model="gemini-2.5-pro",
    instruction="You are a division assistant. Always use the MCP `div` tool."
)

all_agents = [add_agent, sub_agent, mul_agent, div_agent]


# ✅ Attach tools dynamically inside the test function
async def test_mcp_agents():
    # Create MCP toolset once
    toolset = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="http://localhost:8001/mcp",
            headers={"Accept": "text/event-stream"}
        )
    )

    # Attach the toolset to each agent here
    for agent in all_agents:
        agent.tools = [toolset]

    session_service = InMemorySessionService()
    runner = Runner(session_service=session_service)

    test_inputs = {
        "add_agent": "Add 5 and 7",
        "sub_agent": "Subtract 4 from 10",
        "mul_agent": "Multiply 3 and 6",
        "div_agent": "Divide 20 by 5"
    }

    for agent in all_agents:
        print(f"\n🔹 Running {agent.name} ...")
        response = await runner.run(agent, test_inputs[agent.name])
        print(f"{agent.name} response: {response.output_text}")


if __name__ == "__main__":
    asyncio.run(test_mcp_agents())
