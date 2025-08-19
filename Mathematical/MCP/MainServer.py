# math_server.py
from fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP("Math MCP Server")


@mcp.tool()
def add(a: float, b: float) -> float:
    return a + b

@mcp.tool()
def sub(a: float, b: float) -> float:
    return a - b

@mcp.tool()
def mul(a: float, b: float) -> float:
    return a * b

@mcp.tool()
def div(a: float, b: float) -> float:
    return a / b if b != 0 else float("inf")

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8001,
        path="/mcp"
    )
