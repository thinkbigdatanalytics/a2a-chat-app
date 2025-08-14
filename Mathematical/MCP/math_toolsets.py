from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams, StdioServerParameters

addition_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\New folder\ADK_2\MCP\addition_server.py"]
        )
    )
)

subtraction_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\New folder\ADK_2\MCP\subtraction_server.py"]
        )
    )
)

multiplication_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\New folder\ADK_2\MCP\multiplication_server.py"]
        )
    )
)

division_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\New folder\ADK_2\MCP\division_server.py"]
        )
    )
)
