# All_Agent.py
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import (
    StdioConnectionParams,
    StdioServerParameters)
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"



def initiate_toolset(tool_name: str, command: str, path: str, timeout: int = 3000):
    class TimeoutMCPToolset(MCPToolset):
        def __init__(self, *, tool_name: str, connection_params, timeout=30, **kwargs):
            self.tool_name = tool_name

            # Inject timeout into StdioConnectionParams
            if isinstance(connection_params, StdioConnectionParams):
                connection_params = StdioConnectionParams(
                    server_params=connection_params.server_params,
                    timeout=timeout,
                )
            super().__init__(connection_params=connection_params, **kwargs)

    toolset_instance = TimeoutMCPToolset(
        tool_name=tool_name,
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=command,
                args=[path]
            ),
            timeout=timeout,
        ),
        timeout=timeout,
    )

    return toolset_instance

def initiate_agent()



# No need for asyncio.run(toolset.connect()) — ADK handles it

add_agent = Agent(
    name="add_agent",
    model="gemini-2.5-pro",
    instruction="You are an addition assistant. Always use the MCP `add` tool.",
    tools=[toolset]
)

sub_agent = Agent(
    name="sub_agent",
    model="gemini-2.5-pro",
    instruction="You are a subtraction assistant. Always use the MCP `sub` tool.",
    tools=[toolset]
)

mul_agent = Agent(
    name="mul_agent",
    model="gemini-2.5-pro",
    instruction="You are a multiplication assistant. Always use the MCP `mul` tool.",
    tools=[toolset]
)

div_agent = Agent(
    name="div_agent",
    model="gemini-2.5-pro",
    instruction="You are a division assistant. Always use the MCP `div` tool.",
    tools=[toolset]
)

all_agents = [add_agent, sub_agent, mul_agent, div_agent]
