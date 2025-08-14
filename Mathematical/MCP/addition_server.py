from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Addition MCP Server")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    log_line = f"[{datetime.now()}] addition_agent.add called with a={a}, b={b}"
    print(log_line)
    with open("math_trace.log", "a") as f:
        f.write(log_line + "\n")
    return a + b

if __name__ == "__main__":
    mcp.run()
