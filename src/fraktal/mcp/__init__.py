"""MCP server — exposes Fraktál tools to any MCP-compatible AI agent.

Start with: fraktal mcp --workspace /path/to/project
This runs a stdio MCP server that Reasonix and other agents can connect to.
"""

from __future__ import annotations

from fraktal.config import FraktalConfig
from fraktal.tools.base import default_registry


def build_server(config: FraktalConfig):
    """Build an MCP server exposing Fraktál's tool suite.

    Requires: pip install mcp
    """
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
    except ImportError:
        raise ImportError(
            "MCP support requires the 'mcp' package. Install with: pip install fraktal[mcp]"
        )

    server = Server("fraktal")
    registry = default_registry(str(config.workspace))

    @server.list_tools()
    async def list_tools():
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.parameters,
            }
            for t in registry.list_tools()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        tool = registry.get(name)
        if tool is None:
            return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}]}
        try:
            result = tool.execute(**arguments)
            return {"content": [{"type": "text", "text": result.output}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Tool error: {e}"}]}

    return server


def run_mcp_server(config: FraktalConfig):
    """Run the MCP server on stdio (blocking)."""
    import asyncio
    from mcp.server.stdio import stdio_server

    server = build_server(config)

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(main())
