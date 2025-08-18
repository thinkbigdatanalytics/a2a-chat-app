import asyncio
import streamlit as st

# Import your MCPToolsets
from Mathematical.MCP.math_toolsets import (
    addition_toolset,
    subtraction_toolset,
    multiplication_toolset,
    division_toolset
)

async def start_mcp_servers():
    """Connect all MCP toolsets in the background."""
    await asyncio.gather(
        addition_toolset.connect(),
        subtraction_toolset.connect(),
        multiplication_toolset.connect(),
        division_toolset.connect()
    )
    print("✅ All MCP servers started and connected.")

# Streamlit will run this only once per session
if "mcp_started" not in st.session_state:
    asyncio.get_event_loop().run_until_complete(start_mcp_servers())
    st.session_state["mcp_started"] = True
