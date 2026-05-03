import json
import os
import tempfile

import pytest
from httpx import ASGITransport, AsyncClient

from botgateway.db import Database
from botgateway.main import create_app


@pytest.fixture
async def e2e_app(tmp_path):
    db_path = str(tmp_path / "e2e_test.db")
    Database._instance = None
    db = Database.get_database(db_path)
    await db.init_schema()
    application = create_app(management_token="e2e-test-token")
    yield application
    await db.close()
    Database._instance = None


@pytest.fixture
async def e2e_client(e2e_app):
    transport = ASGITransport(app=e2e_app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


ADMIN_HEADERS = {"Authorization": "Bearer e2e-test-token"}


class TestE2EMcpToolLifecycle:
    async def _create_api_key(self, client):
        resp = await client.post(
            "/admin/api-keys",
            json={"name": "e2e-client-key"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201
        return resp.json()["api_key"]

    @pytest.mark.anyio
    async def test_full_mcp_tool_crud_lifecycle(self, e2e_client):
        client = e2e_client

        schema = {
            "type": "function",
            "function": {
                "name": "weather",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                },
            },
        }
        resp = await client.post(
            "/admin/mcp-tools",
            json={
                "name": "weather",
                "description": "Weather lookup tool",
                "endpoint_url": "http://weather-svc/tools/weather",
                "tool_schema": schema,
            },
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201
        tool_id = resp.json()["id"]
        assert resp.json()["name"] == "weather"

        resp = await client.get("/admin/mcp-tools", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = await client.get(
            f"/admin/mcp-tools/{tool_id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Weather lookup tool"
        assert resp.json()["tool_schema"] == schema

        resp = await client.put(
            f"/admin/mcp-tools/{tool_id}",
            json={"description": "Updated weather tool"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated weather tool"

        resp = await client.put(
            f"/admin/mcp-tools/{tool_id}",
            json={"is_active": False},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        resp = await client.delete(
            f"/admin/mcp-tools/{tool_id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 204

        resp = await client.get(
            f"/admin/mcp-tools/{tool_id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_full_mcp_server_crud_lifecycle(self, e2e_client):
        client = e2e_client

        resp = await client.post(
            "/admin/mcp-tools/servers",
            json={
                "name": "math-server",
                "transport": "stdio",
                "command": "python",
                "args": ["-m", "math_server"],
                "description": "Math operations server",
            },
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201
        server_id = resp.json()["id"]
        assert resp.json()["name"] == "math-server"
        assert resp.json()["command"] == "python"
        assert resp.json()["args"] == ["-m", "math_server"]

        resp = await client.get(
            "/admin/mcp-tools/servers", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        resp = await client.get(
            f"/admin/mcp-tools/servers/{server_id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 200
        assert resp.json()["transport"] == "stdio"

        resp = await client.put(
            f"/admin/mcp-tools/servers/{server_id}",
            json={"description": "Updated math server"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated math server"

        resp = await client.delete(
            f"/admin/mcp-tools/servers/{server_id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 204

        resp = await client.get(
            f"/admin/mcp-tools/servers/{server_id}", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_import_mcp_json_then_list(self, e2e_client):
        client = e2e_client

        mcp_config = {
            "weather": {"cmd": ["uv", "run", "weather"]},
            "math": {"url": "http://localhost:9000/sse"},
        }

        config_path = os.path.join(tempfile.gettempdir(), "e2e_mcp.json")
        with open(config_path, "w") as f:
            json.dump(mcp_config, f)

        with open(config_path, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import",
                files={"file": ("mcp.json", f, "application/json")},
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 2
        assert len(data["errors"]) == 0

        resp = await client.get("/admin/mcp-tools", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

        os.unlink(config_path)

    @pytest.mark.anyio
    async def test_import_mcp_json_as_servers(self, e2e_client):
        client = e2e_client

        mcp_config = {
            "weather-sse": {"url": "http://localhost:8080/sse"},
            "calculator": {"cmd": ["uv", "run", "calculator"]},
        }

        config_path = os.path.join(tempfile.gettempdir(), "e2e_servers.json")
        with open(config_path, "w") as f:
            json.dump(mcp_config, f)

        with open(config_path, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import-servers",
                files={"file": ("servers.json", f, "application/json")},
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["success"]) == 2
        assert len(data["errors"]) == 0

        resp = await client.get(
            "/admin/mcp-tools/servers", headers=ADMIN_HEADERS
        )
        assert resp.status_code == 200
        servers = resp.json()
        assert len(servers) == 2

        server_names = {s["name"] for s in servers}
        assert server_names == {"weather-sse", "calculator"}

        os.unlink(config_path)

    @pytest.mark.anyio
    async def test_import_duplicate_returns_error(self, e2e_client):
        client = e2e_client

        mcp_config = {"weather": {"cmd": ["uv", "run", "weather"]}}

        config_path = os.path.join(
            tempfile.gettempdir(), "e2e_dup.json"
        )
        with open(config_path, "w") as f:
            json.dump(mcp_config, f)

        with open(config_path, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import",
                files={"file": ("mcp.json", f, "application/json")},
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 200
        assert len(resp.json()["success"]) == 1

        with open(config_path, "rb") as f:
            resp = await client.post(
                "/admin/mcp-tools/import",
                files={"file": ("mcp.json", f, "application/json")},
                headers=ADMIN_HEADERS,
            )
        assert resp.status_code == 200
        assert len(resp.json()["success"]) == 0
        assert len(resp.json()["errors"]) == 1
        assert "already exists" in resp.json()["errors"][0]["error"]

        os.unlink(config_path)


class TestE2EClientApiWithApiKey:
    async def _create_api_key(self, client):
        resp = await client.post(
            "/admin/api-keys",
            json={"name": "e2e-client-key"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201
        return resp.json()["api_key"]

    async def _seed_tools(self, client):
        for name in ["weather", "translate", "search"]:
            await client.post(
                "/admin/mcp-tools",
                json={
                    "name": name,
                    "description": f"{name} tool",
                    "endpoint_url": f"http://{name}-svc/tools/{name}",
                },
                headers=ADMIN_HEADERS,
            )

    @pytest.mark.anyio
    async def test_client_list_tools_with_api_key(self, e2e_client):
        client = e2e_client
        api_key = await self._create_api_key(client)
        await self._seed_tools(client)

        resp = await client.get(
            "/v1/mcp/tools",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 3
        names = {t["name"] for t in data["data"]}
        assert names == {"weather", "translate", "search"}

    @pytest.mark.anyio
    async def test_client_get_tool_detail(self, e2e_client):
        client = e2e_client
        api_key = await self._create_api_key(client)
        await self._seed_tools(client)

        resp = await client.get(
            "/v1/mcp/tools/weather",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "weather"
        assert resp.json()["description"] == "weather tool"

    @pytest.mark.anyio
    async def test_client_auth_rejected_without_key(self, e2e_client):
        client = e2e_client

        resp = await client.get("/v1/mcp/tools")
        assert resp.status_code == 401

        resp = await client.get(
            "/v1/mcp/tools",
            headers={"Authorization": "Bearer invalid_key"},
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_client_tool_not_found(self, e2e_client):
        client = e2e_client
        api_key = await self._create_api_key(client)

        resp = await client.get(
            "/v1/mcp/tools/nonexistent",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_client_inactive_tool_hidden(self, e2e_client):
        client = e2e_client
        api_key = await self._create_api_key(client)

        create_resp = await client.post(
            "/admin/mcp-tools",
            json={"name": "hidden-tool"},
            headers=ADMIN_HEADERS,
        )
        tool_id = create_resp.json()["id"]

        await client.put(
            f"/admin/mcp-tools/{tool_id}",
            json={"is_active": False},
            headers=ADMIN_HEADERS,
        )

        resp = await client.get(
            "/v1/mcp/tools",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0


class TestE2EHealthAndRoot:
    @pytest.mark.anyio
    async def test_root_endpoint(self, e2e_client):
        resp = await e2e_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "0.4.0" in data["version"]

    @pytest.mark.anyio
    async def test_admin_open_access(self, e2e_client):
        resp = await e2e_client.get("/admin/mcp-tools")
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_admin_api_key_open_access(self, e2e_client):
        resp = await e2e_client.get("/admin/api-keys")
        assert resp.status_code == 200
