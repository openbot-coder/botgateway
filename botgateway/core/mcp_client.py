from __future__ import annotations

import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class McpClient:
    def __init__(self, server_config: dict):
        self.server_config = server_config
        self.transport = server_config.get("transport", "stdio")

    async def list_tools(self) -> list[dict[str, Any]]:
        if self.transport == "stdio":
            return await self._list_tools_stdio()
        elif self.transport == "sse":
            return await self._list_tools_sse()
        else:
            raise ValueError(f"Unsupported transport: {self.transport}")

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        if self.transport == "stdio":
            return await self._call_tool_stdio(tool_name, arguments)
        elif self.transport == "sse":
            return await self._call_tool_sse(tool_name, arguments)
        else:
            raise ValueError(f"Unsupported transport: {self.transport}")

    async def _list_tools_stdio(self) -> list[dict[str, Any]]:
        command = self.server_config.get("command")
        args = self.server_config.get("args", [])
        env = self.server_config.get("env")

        if not command:
            raise ValueError("Command is required for stdio transport")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in tools
                ]

    async def _list_tools_sse(self) -> list[dict[str, Any]]:
        url = self.server_config.get("url")
        if not url:
            raise ValueError("URL is required for SSE transport")

        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in tools
                ]

    async def _call_tool_stdio(self, tool_name: str, arguments: dict) -> Any:
        command = self.server_config.get("command")
        args = self.server_config.get("args", [])
        env = self.server_config.get("env")

        if not command:
            raise ValueError("Command is required for stdio transport")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result

    async def _call_tool_sse(self, tool_name: str, arguments: dict) -> Any:
        url = self.server_config.get("url")
        if not url:
            raise ValueError("URL is required for SSE transport")

        async with sse_client(url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result
