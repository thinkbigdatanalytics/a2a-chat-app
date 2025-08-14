from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Subtraction MCP Server")

@mcp.tool()
def subtraction(a: float, b: float) -> float:
    """Subtraction two numbers"""
    log_line = f"[{datetime.now()}] subtraction_agent.subtraction called with a={a}, b={b}"
    print(log_line)
    with open("math_trace.log", "a") as f:
        f.write(log_line + "\n")
    return a - b

if __name__ == "__main__":
    mcp.run(transport="stdio")
