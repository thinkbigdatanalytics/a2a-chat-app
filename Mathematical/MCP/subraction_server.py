import asyncio

from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Subtraction MCP Server")

@mcp.tool(name="mcp.sub")
async def subtraction(a: float, b: float) -> float:
    """Subtraction two numbers"""
    log_line = f"[{datetime.now()}] Main_agent to subtraction_agent.subtraction called with a={a}, b={b}"
    print(log_line)
    with open("math_trace.log", "a") as f:
        f.write(log_line + "\n")
    await asyncio.sleep(1)
    return a - b

if __name__ == "__main__":
    mcp.run(transport="stdio")
