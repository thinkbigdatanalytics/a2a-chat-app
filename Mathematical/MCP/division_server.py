from fastmcp import Client
import asyncio

async def main():
    async with Client("http://localhost:8001/mcp") as client:
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])
        result = await client.call_tool("add", {"a": 5, "b": 7})
        print("Result:", result.data)
asyncio.run(main())
