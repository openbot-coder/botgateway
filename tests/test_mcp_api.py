"""Test MCP API endpoints"""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from botgateway.db import Database
from botgateway.main import create_app


@pytest.fixture
async def app(tmp_path):
    db_path = str(tmp_path / "test.db")
    Database._instance = None
    db = Database.get_database(db_path)
    await db.init_schema()
    application = create_app(management_token="test-token")
    yield application
    await db.close()
    Database._instance = None


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def admin_headers():
    return {"Authorization": "Bearer test-token"}


class TestMcpToolApi:
    """Test /admin/mcp-tools endpoints"""

    @pytest.mark.anyio
    async def test_create_tool(self, client, admin_headers):
        """正例: 创建 MCP 工具"""
        resp = await client.post(
            "/admin/mcp-tools",
            json={"name": "weather", "description": "Weather tool"},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "weather"
        assert data["description"] == "Weather tool"
        assert data["is_active"] is True

    @pytest.mark.anyio
    async def test_create_tool_duplicate_name(self, client, admin_headers):
        """反例: 创建同名工具返回 409"""
        await client.post(
            "/admin/mcp-tools",
            json={"name": "weather"},
            headers=admin_headers,
        )
        resp = await client.post(
            "/admin/mcp-tools",
            json={"name": "weather"},
            headers=admin_headers,
        )
        assert resp.status_code == 409

    @pytest.mark.anyio
    async def test_list_tools(self, client, admin_headers):
        """正例: 列出所有工具"""
        await client.post(
            "/admin/mcp-tools",
            json={"name": "tool1"},
            headers=admin_headers,
        )
        await client.post(
            "/admin/mcp-tools",
            json={"name": "tool2"},
            headers=admin_headers,
        )
        resp = await client.get("/admin/mcp-tools", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.anyio
    async def test_get_tool(self, client, admin_headers):
        """正例: 获取单个工具"""
        create_resp = await client.post(
            "/admin/mcp-tools",
            json={"name": "weather"},
            headers=admin_headers,
        )
        tool_id = create_resp.json()["id"]
        resp = await client.get(
            f"/admin/mcp-tools/{tool_id}", headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "weather"

    @pytest.mark.anyio
    async def test_get_tool_not_found(self, client, admin_headers):
        """反例: 获取不存在的工具返回 404"""
        resp = await client.get(
            "/admin/mcp-tools/nonexistent", headers=admin_headers
        )
        assert resp.status_code == 404


    @pytest.mark.anyio
    async def test_update_tool(self, client, admin_headers):
        """正例: 更新工具"""
        create_resp = await client.post(
            "/admin/mcp-tools",
            json={"name": "weather"},
            headers=admin_headers,
        )
        tool_id = create_resp.json()["id"]
        resp = await client.put(
            f"/admin/mcp-tools/{tool_id}",
            json={"name": "weather-v2", "description": "Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "weather-v2"
        assert resp.json()["description"] == "Updated"

    @pytest.mark.anyio
    async def test_update_tool_not_found(self, client, admin_headers):
        """反例: 更新不存在的工具返回 404"""
        resp = await client.put(
            "/admin/mcp-tools/nonexistent",
            json={"name": "test"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_tool(self, client, admin_headers):
        """正例: 删除工具"""
        create_resp = await client.post(
            "/admin/mcp-tools",
            json={"name": "weather"},
            headers=admin_headers,
        )
        tool_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/admin/mcp-tools/{tool_id}", headers=admin_headers
        )
        assert resp.status_code == 204

    @pytest.mark.anyio
    async def test_delete_tool_not_found(self, client, admin_headers):
        """反例: 删除不存在的工具返回 404"""
        resp = await client.delete(
            "/admin/mcp-tools/nonexistent", headers=admin_headers
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_import_mcp_json(self, client, admin_headers, tmp_path):
        """正例: 从 mcp.json 文件导入服务器"""
        mcp_config = {
            "weather-server": {"url": "http://localhost:8080/weather"},
            "calc-server": {"cmd": ["uv", "run", "calculator"]},
        }
        json_file = tmp_path / "mcp.json"
        json_file.write_text(json.dumps(mcp_config), encoding="utf-8")

        with open(json_file, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("mcp.json", f, "application/json")},
                headers=admin_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 2
        assert len(data["errors"]) == 0

    @pytest.mark.anyio
    async def test_import_mcp_json_duplicate(self, client, admin_headers, tmp_path):
        """反例: 导入重复名称的服务器"""
        mcp_config = {"weather-server": {"url": "http://localhost:8080/weather"}}
        json_file = tmp_path / "mcp.json"
        json_file.write_text(json.dumps(mcp_config), encoding="utf-8")

        with open(json_file, "rb") as f:
            await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("mcp.json", f, "application/json")},
                headers=admin_headers,
            )

        with open(json_file, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("mcp.json", f, "application/json")},
                headers=admin_headers,
            )

        data = resp.json()
        assert len(data["success"]) == 0
        assert len(data["errors"]) == 1

    @pytest.mark.anyio
    async def test_import_invalid_json(self, client, admin_headers, tmp_path):
        """反例: 导入无效 JSON 文件"""
        json_file = tmp_path / "bad.json"
        json_file.write_text("not json", encoding="utf-8")

        with open(json_file, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("bad.json", f, "application/json")},
                headers=admin_headers,
            )

        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_import_non_json_file(self, client, admin_headers, tmp_path):
        """反例: 导入非 .json 文件"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("{}", encoding="utf-8")

        with open(txt_file, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("test.txt", f, "text/plain")},
                headers=admin_headers,
            )

        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_import_non_object_json(self, client, admin_headers, tmp_path):
        """反例: 导入非对象 JSON"""
        json_file = tmp_path / "array.json"
        json_file.write_text('[{"name": "test"}]', encoding="utf-8")

        with open(json_file, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("array.json", f, "application/json")},
                headers=admin_headers,
            )

        assert resp.status_code == 400


class TestMcpServerApi:
    """Test /admin/mcp-tools/servers endpoints"""

    @pytest.mark.anyio
    async def test_create_server(self, client, admin_headers):
        """正例: 创建 MCP 服务器"""
        resp = await client.post(
            "/admin/mcp-tools/servers",
            json={
                "name": "weather-server",
                "transport": "stdio",
                "command": "uv",
                "args": ["run", "weather"],
            },
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "weather-server"
        assert data["transport"] == "stdio"
        assert data["command"] == "uv"
        assert data["args"] == ["run", "weather"]

    @pytest.mark.anyio
    async def test_create_server_duplicate_name(self, client, admin_headers):
        """反例: 创建同名服务器返回 409"""
        await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server1"},
            headers=admin_headers,
        )
        resp = await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server1"},
            headers=admin_headers,
        )
        assert resp.status_code == 409

    @pytest.mark.anyio
    async def test_list_servers(self, client, admin_headers):
        """正例: 列出所有服务器"""
        await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server1"},
            headers=admin_headers,
        )
        await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server2"},
            headers=admin_headers,
        )
        resp = await client.get(
            "/admin/mcp-tools/servers", headers=admin_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.anyio
    async def test_get_server(self, client, admin_headers):
        """正例: 获取单个服务器"""
        create_resp = await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server1"},
            headers=admin_headers,
        )
        server_id = create_resp.json()["id"]
        resp = await client.get(
            f"/admin/mcp-tools/servers/{server_id}", headers=admin_headers
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "server1"

    @pytest.mark.anyio
    async def test_get_server_not_found(self, client, admin_headers):
        """反例: 获取不存在的服务器返回 404"""
        resp = await client.get(
            "/admin/mcp-tools/servers/nonexistent", headers=admin_headers
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_update_server(self, client, admin_headers):
        """正例: 更新服务器"""
        create_resp = await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server1"},
            headers=admin_headers,
        )
        server_id = create_resp.json()["id"]
        resp = await client.put(
            f"/admin/mcp-tools/servers/{server_id}",
            json={"name": "server1-v2", "description": "Updated"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "server1-v2"
        assert resp.json()["description"] == "Updated"

    @pytest.mark.anyio
    async def test_update_server_not_found(self, client, admin_headers):
        """反例: 更新不存在的服务器返回 404"""
        resp = await client.put(
            "/admin/mcp-tools/servers/nonexistent",
            json={"name": "test"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_server(self, client, admin_headers):
        """正例: 删除服务器"""
        create_resp = await client.post(
            "/admin/mcp-tools/servers",
            json={"name": "server1"},
            headers=admin_headers,
        )
        server_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/admin/mcp-tools/servers/{server_id}", headers=admin_headers
        )
        assert resp.status_code == 204

    @pytest.mark.anyio
    async def test_delete_server_not_found(self, client, admin_headers):
        """反例: 删除不存在的服务器返回 404"""
        resp = await client.delete(
            "/admin/mcp-tools/servers/nonexistent", headers=admin_headers
        )
        assert resp.status_code == 404


class TestMcpClientApi:
    """Test /v1/mcp endpoints (client-facing with API key)"""

    async def _create_api_key(self, client, admin_headers):
        resp = await client.post(
            "/admin/api-keys",
            json={"name": "test-key"},
            headers=admin_headers,
        )
        return resp.json()["api_key"]

    @pytest.mark.anyio
    async def test_list_tools_with_valid_api_key(self, client, admin_headers):
        """正例: 使用有效 API Key 列出工具"""
        api_key = await self._create_api_key(client, admin_headers)
        await client.post(
            "/admin/mcp-tools",
            json={"name": "weather"},
            headers=admin_headers,
        )

        resp = await client.get(
            "/v1/mcp/tools",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1

    @pytest.mark.anyio
    async def test_list_tools_with_invalid_api_key(self, client):
        """反例: 使用无效 API Key 返回 401"""
        resp = await client.get(
            "/v1/mcp/tools",
            headers={"Authorization": "Bearer invalid_key"},
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_list_tools_without_auth(self, client):
        """反例: 不提供认证头返回 401"""
        resp = await client.get("/v1/mcp/tools")
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_get_tool_info(self, client, admin_headers):
        """正例: 获取工具详情"""
        api_key = await self._create_api_key(client, admin_headers)
        await client.post(
            "/admin/mcp-tools",
            json={"name": "weather", "description": "Weather tool"},
            headers=admin_headers,
        )

        resp = await client.get(
            "/v1/mcp/tools/weather",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "weather"

    @pytest.mark.anyio
    async def test_get_tool_info_not_found(self, client, admin_headers):
        """反例: 获取不存在的工具返回 404"""
        api_key = await self._create_api_key(client, admin_headers)

        resp = await client.get(
            "/v1/mcp/tools/nonexistent",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 404
