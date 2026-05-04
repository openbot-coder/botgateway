"""Test MCP models (McpTool and McpServer)"""

from botgateway.db.models import McpServer, McpTool


class TestMcpTool:
    """Test McpTool model"""

    def test_create_generates_id_and_timestamps(self):
        """正例: create 方法生成 id 和时间戳"""
        tool = McpTool.create(name="weather")
        assert tool.id is not None
        assert tool.name == "weather"
        assert tool.is_active is True
        assert tool.created_at is not None
        assert tool.updated_at is not None

    def test_create_with_all_fields(self):
        """正例: create 方法支持所有字段"""
        tool = McpTool.create(
            name="calculator",
            description="A calculator tool",
            endpoint_url="http://localhost:8080/calc",
            tool_schema={"type": "function", "parameters": {"type": "object"}},
        )
        assert tool.name == "calculator"
        assert tool.description == "A calculator tool"
        assert tool.endpoint_url == "http://localhost:8080/calc"
        assert tool.tool_schema is not None

    def test_create_with_defaults(self):
        """边界值: create 使用默认值"""
        tool = McpTool.create(name="test")
        assert tool.description is None
        assert tool.endpoint_url is None
        assert tool.tool_schema is None

    def test_get_tool_schema_returns_dict(self):
        """正例: get_tool_schema 返回字典"""
        schema = {"type": "function", "parameters": {"type": "object"}}
        tool = McpTool.create(name="test", tool_schema=schema)
        result = tool.get_tool_schema()
        assert result == schema

    def test_get_tool_schema_returns_none_when_empty(self):
        """边界值: get_tool_schema 返回 None"""
        tool = McpTool.create(name="test")
        assert tool.get_tool_schema() is None

    def test_to_dict_contains_all_fields(self):
        """正例: to_dict 返回所有字段"""
        tool = McpTool.create(name="test", description="desc")
        data = tool.to_dict()
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "endpoint_url" in data
        assert "tool_schema" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_to_dict_tool_schema_is_parsed(self):
        """正例: to_dict 中 tool_schema 已解析为字典"""
        schema = {"type": "object"}
        tool = McpTool.create(name="test", tool_schema=schema)
        data = tool.to_dict()
        assert data["tool_schema"] == schema

    def test_from_dict_creates_valid_instance(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "tool-1",
            "name": "weather",
            "description": "Weather tool",
            "endpoint_url": "http://localhost:8080/weather",
            "tool_schema": '{"type": "object"}',
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        tool = McpTool.from_dict(data)
        assert tool.id == "tool-1"
        assert tool.name == "weather"
        assert tool.description == "Weather tool"
        assert tool.endpoint_url == "http://localhost:8080/weather"
        assert tool.is_active is True

    def test_from_dict_with_inactive_status(self):
        """边界值: from_dict 正确处理 is_active=0"""
        data = {
            "id": "tool-1",
            "name": "test",
            "is_active": 0,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        tool = McpTool.from_dict(data)
        assert tool.is_active is False

    def test_from_dict_with_string_false(self):
        """边界值: from_dict 正确处理 is_active='false'"""
        data = {
            "id": "tool-1",
            "name": "test",
            "is_active": "false",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        tool = McpTool.from_dict(data)
        assert tool.is_active is False


class TestMcpServer:
    """Test McpServer model"""

    def test_create_generates_id_and_timestamps(self):
        """正例: create 方法生成 id 和时间戳"""
        server = McpServer.create(name="weather-server")
        assert server.id is not None
        assert server.name == "weather-server"
        assert server.transport == "stdio"
        assert server.is_active is True
        assert server.created_at is not None
        assert server.updated_at is not None

    def test_create_stdio_server(self):
        """正例: create 创建 stdio 类型服务器"""
        server = McpServer.create(
            name="calc-server",
            transport="stdio",
            command="uv",
            args=["run", "calculator"],
        )
        assert server.transport == "stdio"
        assert server.command == "uv"
        assert server.args is not None

    def test_create_sse_server(self):
        """正例: create 创建 sse 类型服务器"""
        server = McpServer.create(
            name="remote-server",
            transport="sse",
            url="http://localhost:8080/sse",
        )
        assert server.transport == "sse"
        assert server.url == "http://localhost:8080/sse"


    def test_create_with_env(self):
        """正例: create 支持环境变量"""
        env = {"API_KEY": "test-key"}
        server = McpServer.create(name="test", env=env)
        assert server.env is not None

    def test_get_args_returns_list(self):
        """正例: get_args 返回列表"""
        server = McpServer.create(
            name="test", command="uv", args=["run", "test"]
        )
        args = server.get_args()
        assert args == ["run", "test"]

    def test_get_args_returns_none_when_empty(self):
        """边界值: get_args 返回 None"""
        server = McpServer.create(name="test")
        assert server.get_args() is None

    def test_get_env_returns_dict(self):
        """正例: get_env 返回字典"""
        env = {"KEY": "value"}
        server = McpServer.create(name="test", env=env)
        result = server.get_env()
        assert result == env

    def test_get_env_returns_none_when_empty(self):
        """边界值: get_env 返回 None"""
        server = McpServer.create(name="test")
        assert server.get_env() is None

    def test_to_dict_contains_all_fields(self):
        """正例: to_dict 返回所有字段"""
        server = McpServer.create(
            name="test",
            transport="stdio",
            command="uv",
            args=["run", "test"],
            description="Test server",
        )
        data = server.to_dict()
        assert "id" in data
        assert "name" in data
        assert "transport" in data
        assert "command" in data
        assert "args" in data
        assert "url" in data
        assert "env" in data
        assert "description" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_to_dict_args_is_parsed(self):
        """正例: to_dict 中 args 已解析为列表"""
        server = McpServer.create(name="test", command="uv", args=["run", "test"])
        data = server.to_dict()
        assert data["args"] == ["run", "test"]

    def test_to_dict_env_is_parsed(self):
        """正例: to_dict 中 env 已解析为字典"""
        env = {"KEY": "value"}
        server = McpServer.create(name="test", env=env)
        data = server.to_dict()
        assert data["env"] == env

    def test_from_dict_creates_valid_instance(self):
        """正例: from_dict 创建有效实例"""
        data = {
            "id": "server-1",
            "name": "weather-server",
            "transport": "stdio",
            "command": "uv",
            'args': '["run", "weather"]',
            "url": None,
            "env": None,
            "description": "Weather server",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        server = McpServer.from_dict(data)
        assert server.id == "server-1"
        assert server.name == "weather-server"
        assert server.transport == "stdio"
        assert server.command == "uv"
        assert server.description == "Weather server"

    def test_from_dict_with_inactive_status(self):
        """边界值: from_dict 正确处理 is_active=0"""
        data = {
            "id": "server-1",
            "name": "test",
            "transport": "stdio",
            "is_active": 0,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        server = McpServer.from_dict(data)
        assert server.is_active is False

    def test_from_dict_with_string_false(self):
        """边界值: from_dict 正确处理 is_active='false'"""
        data = {
            "id": "server-1",
            "name": "test",
            "transport": "stdio",
            "is_active": "false",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        server = McpServer.from_dict(data)
        assert server.is_active is False

    def test_from_dict_with_sse_transport(self):
        """正例: from_dict 正确解析 sse 传输"""
        data = {
            "id": "server-1",
            "name": "remote",
            "transport": "sse",
            "url": "http://localhost:8080/sse",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        }
        server = McpServer.from_dict(data)
        assert server.transport == "sse"
        assert server.url == "http://localhost:8080/sse"
