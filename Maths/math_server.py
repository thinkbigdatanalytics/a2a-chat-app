# math_server.py
import asyncio
from fastmcp import FastMCP

mcp = FastMCP("Math MCP Server 🚀")

@mcp.tool()
async def add(a: float, b: float) -> float:
    """Add two numbers"""
    await asyncio.sleep(0)  # simulate async
    return a + b

@mcp.tool()
async def sub(a: float, b: float) -> float:
    """Subtract two numbers"""
    await asyncio.sleep(0)
    return a - b

@mcp.tool()
async def mul(a: float, b: float) -> float:
    """Multiply two numbers"""
    await asyncio.sleep(0)
    return a * b

@mcp.tool()
async def div(a: float, b: float) -> float:
    """Divide two numbers"""
    await asyncio.sleep(0)
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

if __name__ == "__main__":
    mcp.run()
