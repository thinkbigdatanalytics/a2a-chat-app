import asyncio

from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Division MCP Server")

@mcp.tool(name="mcp.div")
async def division(a: float, b: float) -> float:
    log_line = f"[{datetime.now()}] Main_agent to  division_agent.division called with a={a}, b={b}"
    print(log_line)
    with open("math_trace.log", "a") as f:
        f.write(log_line + "\n")
    """Divide two numbers"""
    await asyncio.sleep(1)
    return a / b

if __name__ == "__main__":
   mcp.run(transport="stdio")
