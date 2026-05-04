from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from botgateway.core.encryptor import ClientApiKeyValidator
from botgateway.db import ApiKeyRepository, Database, McpToolRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/mcp", tags=["mcp"])


class ToolCallRequest(BaseModel):
    arguments: dict = {}


class ToolCallResponse(BaseModel):
    tool_name: str
    result: dict


def get_db() -> Database:
    return Database.get_database()


async def verify_api_key(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required"
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    api_key = parts[1]
    db = Database.get_database()
    repo = ApiKeyRepository(db)

    api_key_hash = ClientApiKeyValidator.hash_key(api_key)
    stored_key = await repo.get_by_hash(api_key_hash)

    if not stored_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return stored_key.id


@router.get("/tools")
async def list_tools(
    api_key_id: str = Depends(verify_api_key),
    db: Database = Depends(get_db),
):
    repo = McpToolRepository(db)
    tools = await repo.get_all(active_only=True)
    return {
        "object": "list",
        "data": [
            {
                "name": t.name,
                "description": t.description,
                "endpoint_url": t.endpoint_url,
                "tool_schema": t.get_tool_schema(),
            }
            for t in tools
        ],
    }


@router.get("/tools/{tool_name}")
async def get_tool_info(
    tool_name: str,
    api_key_id: str = Depends(verify_api_key),
    db: Database = Depends(get_db),
):
    repo = McpToolRepository(db)
    tool = await repo.get_by_name(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )

    return {
        "name": tool.name,
        "description": tool.description,
        "endpoint_url": tool.endpoint_url,
        "tool_schema": tool.get_tool_schema(),
    }


@router.post("/tools/{tool_name}/call", response_model=ToolCallResponse)
async def call_tool(
    tool_name: str,
    request: ToolCallRequest,
    api_key_id: str = Depends(verify_api_key),
    db: Database = Depends(get_db),
):
    repo = McpToolRepository(db)
    tool = await repo.get_by_name(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )

    if not tool.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' is not active"
        )

    import httpx

    if not tool.endpoint_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tool '{tool_name}' has no endpoint configured"
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                tool.endpoint_url,
                json={
                    "tool": tool_name,
                    "arguments": request.arguments,
                },
            )
            response.raise_for_status()
            result = response.json()

        return ToolCallResponse(
            tool_name=tool_name,
            result=result,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tool endpoint returned error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to call tool endpoint: {str(e)}"
        )
    except Exception as e:
        logger.error("Tool call error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
