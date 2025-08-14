from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Multiply MCP Server")

@mcp.tool()
def multiplication(a: float, b: float) -> float:
    """Multiply two numbers"""
    log_line = f"[{datetime.now()}] multiplication_agent.multiplication called with a={a}, b={b}"
    print(log_line)
    with open("math_trace.log", "a") as f:
        f.write(log_line + "\n")
    return a * b

if __name__ == "__main__":
    mcp.run(transport="stdio")
