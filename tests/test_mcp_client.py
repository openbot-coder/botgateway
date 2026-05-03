"""Test MCP client"""

import pytest

from botgateway.core.mcp_client import McpClient


class TestMcpClientInit:
    """Test McpClient initialization"""

    def test_default_transport_is_stdio(self):
        """正例: 默认传输类型为 stdio"""
        client = McpClient({"command": "uv"})
        assert client.transport == "stdio"

    def test_custom_transport(self):
        """正例: 支持自定义传输类型"""
        client = McpClient({"transport": "sse", "url": "http://localhost"})
        assert client.transport == "sse"

    def test_server_config_stored(self):
        """正例: 服务器配置被正确存储"""
        config = {"command": "uv", "args": ["run", "test"]}
        client = McpClient(config)
        assert client.server_config == config


class TestMcpClientTransport:
    """Test McpClient transport validation"""

    @pytest.mark.anyio
    async def test_unsupported_transport_list_tools(self):
        """反例: 不支持的传输类型抛出异常"""
        client = McpClient({"transport": "unknown"})
        with pytest.raises(ValueError, match="Unsupported transport"):
            await client.list_tools()

    @pytest.mark.anyio
    async def test_unsupported_transport_call_tool(self):
        """反例: 不支持的传输类型抛出异常"""
        client = McpClient({"transport": "unknown"})
        with pytest.raises(ValueError, match="Unsupported transport"):
            await client.call_tool("test", {})


    @pytest.mark.anyio
    async def test_stdio_missing_command_list_tools(self):
        """反例: stdio 传输缺少 command 抛出异常"""
        client = McpClient({"transport": "stdio"})
        with pytest.raises(ValueError, match="Command is required"):
            await client.list_tools()

    @pytest.mark.anyio
    async def test_stdio_missing_command_call_tool(self):
        """反例: stdio 传输缺少 command 抛出异常"""
        client = McpClient({"transport": "stdio"})
        with pytest.raises(ValueError, match="Command is required"):
            await client.call_tool("test", {})

    @pytest.mark.anyio
    async def test_sse_missing_url_list_tools(self):
        """反例: sse 传输缺少 url 抛出异常"""
        client = McpClient({"transport": "sse"})
        with pytest.raises(ValueError, match="URL is required"):
            await client.list_tools()

    @pytest.mark.anyio
    async def test_sse_missing_url_call_tool(self):
        """反例: sse 传输缺少 url 抛出异常"""
        client = McpClient({"transport": "sse"})
        with pytest.raises(ValueError, match="URL is required"):
            await client.call_tool("test", {})
