# custom_http.py
import aiohttp
import asyncio
from google.adk.tools.mcp_tool import MCPToolset

class HttpMCPToolset(MCPToolset):
    def __init__(self, url: str):
        self.url = url
        self.session = None
        self.connected = False
        self._tools = []

    async def connect(self):
        if self.connected:
            return
        self.session = aiohttp.ClientSession()
        # For now assume server lists tools at /tools
        async with self.session.get(f"{self.url}/tools", headers={"Accept": "application/json"}) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to connect: {resp.status}")
            data = await resp.json()
            self._tools = data.get("tools", [])
        self.connected = True

    async def call_tool(self, name: str, args: dict):
        if not self.connected:
            await self.connect()
        async with self.session.post(f"{self.url}/call/{name}", json=args) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Tool {name} failed: {resp.status}")
            return await resp.json()

    def list_tools(self):
        return self._tools
