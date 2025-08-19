from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import (
    StdioConnectionParams,
    StdioServerParameters
)


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



addition_toolset = TimeoutMCPToolset(
    tool_name="mcp.add",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\addition_server.py"]
        ),
        timeout=3000,
    ),
    timeout=3000,
)

subtraction_toolset = TimeoutMCPToolset(
    tool_name="mcp.sub",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\subraction_server.py"]
        ),
        timeout=3000,
    ),
    timeout=3000,
)

multiplication_toolset = TimeoutMCPToolset(
    tool_name="mcp.mul",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\multiplication_server.py"]
        ),
        timeout=3000,
    ),
    timeout=3000,
)

division_toolset = TimeoutMCPToolset(
    tool_name="mcp.div",
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\division_server.py"]
        ),
        timeout=3000,
    ),
    timeout=3000,
)
