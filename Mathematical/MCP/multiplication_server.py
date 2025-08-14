from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Multiply MCP Server")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b

if __name__ == "__main__":
    mcp.run(transport="stdio")
