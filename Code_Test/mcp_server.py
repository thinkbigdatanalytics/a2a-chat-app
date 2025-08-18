# mcp_server.py
from fastapi import FastAPI
from fastmcp import FastMCP

mcp = FastMCP("Math MCP Server")

@mcp.tool
async def add(a: int, b: int) -> int:
    """Add two numbers asynchronously"""
    return a + b

@mcp.tool
async def sub(a: int, b: int) -> int:
    """Subtract two numbers asynchronously"""
    return a - b

# Wrap MCP inside FastAPI
app = FastAPI()
app.include_router(mcp.router)  # mount MCP tool routes

# Run with: uvicorn mcp_server:app --reload --port 8000
