from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams, StdioServerParameters

addition_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\addition_server.py"]
        )
    )
    

)

subtraction_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\subraction_server.py"]
        )
    )
    
)

multiplication_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\multiplication_server.py"]
        )
    )
    
)

division_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[r"D:\Anish\TLQ\a2a-chat-app\Mathematical\MCP\division_server.py"]
        )
    )
    
)
