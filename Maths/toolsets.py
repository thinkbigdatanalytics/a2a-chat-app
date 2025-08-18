# toolsets.py
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams, StdioServerParameters

# One MCP server, but multiple toolsets can reuse it
server_params = StdioServerParameters(
    command="python",
    args=["math_server.py"]
)

connection_params = StdioConnectionParams(server_params=server_params)

add_toolset = MCPToolset(connection_params=connection_params, tool_filter=["add"])
sub_toolset = MCPToolset(connection_params=connection_params, tool_filter=["sub"])
mul_toolset = MCPToolset(connection_params=connection_params, tool_filter=["mul"])
div_toolset = MCPToolset(connection_params=connection_params, tool_filter=["div"])
