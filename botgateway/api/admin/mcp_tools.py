from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from botgateway.api.auth import verify_management_token
from botgateway.core.mcp_client import McpClient
from botgateway.db import Database, McpServer, McpServerRepository, McpTool, McpToolRepository

router = APIRouter(prefix="/mcp-tools", tags=["mcp-tools"])


class McpToolCreate(BaseModel):
    name: str
    description: str | None = None
    endpoint_url: str | None = None
    tool_schema: dict | None = None


class McpToolUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    endpoint_url: str | None = None
    tool_schema: dict | None = None
    is_active: bool | None = None


class McpToolResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    endpoint_url: str | None = None
    tool_schema: dict | None = None
    is_active: bool
    created_at: str
    updated_at: str


class McpToolImportResult(BaseModel):
    success: list[McpToolResponse]
    errors: list[dict]


class McpServerCreate(BaseModel):
    name: str
    transport: str = "stdio"
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: dict | None = None
    description: str | None = None


class McpServerUpdate(BaseModel):
    name: str | None = None
    transport: str | None = None
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: dict | None = None
    description: str | None = None
    is_active: bool | None = None


class McpServerResponse(BaseModel):
    id: str
    name: str
    transport: str
    command: str | None = None
    args: list[str] | None = None
    url: str | None = None
    env: dict | None = None
    description: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class McpServerImportResult(BaseModel):
    success: list[McpServerResponse]
    errors: list[dict]


class McpSyncResult(BaseModel):
    success: list[McpToolResponse]
    errors: list[dict]


def get_db() -> Database:
    return Database.get_database()


def _parse_mcp_json(data: dict) -> list[dict]:
    servers = []
    for name, config in data.items():
        server = {"name": name}
        if "url" in config:
            server["url"] = config["url"]
            server["transport"] = "http"
        if "cmd" in config:
            server["command"] = config["cmd"][0] if config["cmd"] else None
            server["args"] = config["cmd"][1:] if len(config["cmd"]) > 1 else []
            server["transport"] = "stdio"
        servers.append(server)
    return servers


@router.post("", response_model=McpToolResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_tool(
    tool_data: McpToolCreate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpToolRepository(db)
    existing = await repo.get_by_name(tool_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MCP tool with name '{tool_data.name}' already exists"
        )

    tool = McpTool.create(
        name=tool_data.name,
        description=tool_data.description,
        endpoint_url=tool_data.endpoint_url,
        tool_schema=tool_data.tool_schema,
    )
    await repo.create(tool)
    return McpToolResponse(**tool.to_dict())


@router.get("", response_model=list[McpToolResponse])
async def list_mcp_tools(
    active_only: bool = False,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpToolRepository(db)
    tools = await repo.get_all(active_only=active_only)
    return [McpToolResponse(**t.to_dict()) for t in tools]


@router.post("/import", response_model=McpToolImportResult)
async def import_mcp_tools(
    file: UploadFile,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are supported"
        )

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON must be an object with tool names as keys"
        )

    servers_data = _parse_mcp_json(data)
    repo = McpToolRepository(db)
    success = []
    errors = []

    for idx, server_data in enumerate(servers_data):
        existing = await repo.get_by_name(server_data["name"])
        if existing:
            errors.append({
                "index": idx,
                "name": server_data["name"],
                "error": f"Tool with name '{server_data['name']}' already exists"
            })
            continue

        tool = McpTool.create(
            name=server_data["name"],
            description=server_data.get("description"),
            endpoint_url=server_data.get("url"),
            tool_schema=None,
        )
        await repo.create(tool)
        success.append(McpToolResponse(**tool.to_dict()))

    return McpToolImportResult(success=success, errors=errors)


@router.post("/import-servers", response_model=McpServerImportResult)
async def import_mcp_servers(
    file: UploadFile,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    if not file.filename.endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JSON files are supported"
        )

    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JSON must be an object with server names as keys"
        )

    servers_data = _parse_mcp_json(data)
    repo = McpServerRepository(db)
    success = []
    errors = []

    for idx, server_data in enumerate(servers_data):
        existing = await repo.get_by_name(server_data["name"])
        if existing:
            errors.append({
                "index": idx,
                "name": server_data["name"],
                "error": f"Server with name '{server_data['name']}' already exists"
            })
            continue

        server = McpServer.create(**server_data)
        await repo.create(server)
        success.append(McpServerResponse(**server.to_dict()))

    return McpServerImportResult(success=success, errors=errors)


@router.post("/servers", response_model=McpServerResponse, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    server_data: McpServerCreate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpServerRepository(db)
    existing = await repo.get_by_name(server_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MCP server with name '{server_data.name}' already exists"
        )

    server = McpServer.create(
        name=server_data.name,
        transport=server_data.transport,
        command=server_data.command,
        args=server_data.args,
        url=server_data.url,
        env=server_data.env,
        description=server_data.description,
    )
    await repo.create(server)
    return McpServerResponse(**server.to_dict())


@router.get("/servers", response_model=list[McpServerResponse])
async def list_mcp_servers(
    active_only: bool = False,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpServerRepository(db)
    servers = await repo.get_all(active_only=active_only)
    return [McpServerResponse(**s.to_dict()) for s in servers]


@router.get("/servers/{server_id}", response_model=McpServerResponse)
async def get_mcp_server(
    server_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpServerRepository(db)
    server = await repo.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return McpServerResponse(**server.to_dict())


@router.put("/servers/{server_id}", response_model=McpServerResponse)
async def update_mcp_server(
    server_id: str,
    server_data: McpServerUpdate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpServerRepository(db)
    server = await repo.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    if server_data.name is not None:
        existing = await repo.get_by_name(server_data.name)
        if existing and existing.id != server_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MCP server with name '{server_data.name}' already exists"
            )
        server.name = server_data.name

    if server_data.transport is not None:
        server.transport = server_data.transport

    if server_data.command is not None:
        server.command = server_data.command

    if server_data.args is not None:
        server.args = json.dumps(server_data.args)

    if server_data.url is not None:
        server.url = server_data.url

    if server_data.env is not None:
        server.env = json.dumps(server_data.env)

    if server_data.description is not None:
        server.description = server_data.description

    if server_data.is_active is not None:
        server.is_active = server_data.is_active

    server.updated_at = datetime.now(timezone.utc).isoformat()
    await repo.update(server)
    return McpServerResponse(**server.to_dict())


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpServerRepository(db)
    server = await repo.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    await repo.delete(server_id)


@router.post("/servers/{server_id}/sync-tools", response_model=McpSyncResult)
async def sync_mcp_server_tools(
    server_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    server_repo = McpServerRepository(db)
    server = await server_repo.get_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")

    server_config = server.to_dict()
    client = McpClient(server_config)

    try:
        tools = await client.list_tools()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to MCP server: {str(e)}"
        )

    tool_repo = McpToolRepository(db)
    success = []
    errors = []

    for idx, tool_data in enumerate(tools):
        tool_name = f"{server.name}_{tool_data['name']}"
        existing = await tool_repo.get_by_name(tool_name)
        if existing:
            existing.description = tool_data.get("description")
            existing.tool_schema = json.dumps(tool_data.get("input_schema"))
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            await tool_repo.update(existing)
            success.append(McpToolResponse(**existing.to_dict()))
        else:
            tool = McpTool.create(
                name=tool_name,
                description=tool_data.get("description"),
                tool_schema=tool_data.get("input_schema"),
            )
            await tool_repo.create(tool)
            success.append(McpToolResponse(**tool.to_dict()))

    return McpSyncResult(success=success, errors=errors)


@router.get("/{tool_id}", response_model=McpToolResponse)
async def get_mcp_tool(
    tool_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpToolRepository(db)
    tool = await repo.get_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="MCP tool not found")
    return McpToolResponse(**tool.to_dict())


@router.put("/{tool_id}", response_model=McpToolResponse)
async def update_mcp_tool(
    tool_id: str,
    tool_data: McpToolUpdate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpToolRepository(db)
    tool = await repo.get_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="MCP tool not found")

    if tool_data.name is not None:
        existing = await repo.get_by_name(tool_data.name)
        if existing and existing.id != tool_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"MCP tool with name '{tool_data.name}' already exists"
            )
        tool.name = tool_data.name

    if tool_data.description is not None:
        tool.description = tool_data.description

    if tool_data.endpoint_url is not None:
        tool.endpoint_url = tool_data.endpoint_url

    if tool_data.tool_schema is not None:
        tool.tool_schema = json.dumps(tool_data.tool_schema)

    if tool_data.is_active is not None:
        tool.is_active = tool_data.is_active

    tool.updated_at = datetime.now(timezone.utc).isoformat()
    await repo.update(tool)
    return McpToolResponse(**tool.to_dict())


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_tool(
    tool_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = McpToolRepository(db)
    tool = await repo.get_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="MCP tool not found")
    await repo.delete(tool_id)
