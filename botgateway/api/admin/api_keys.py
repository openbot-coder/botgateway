from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from botgateway.api.auth import verify_management_token
from botgateway.core.encryptor import ClientApiKeyValidator
from botgateway.db import ApiKey, ApiKeyRepository, Database

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    name: str


class ApiKeyUpdate(BaseModel):
    name: str | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    api_key: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    api_key: str
    message: str


def get_db() -> Database:
    return Database.get_database()


@router.post("", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    api_key_raw = ClientApiKeyValidator.generate_api_key_v2(prefix="bgw", length=40)
    api_key_hash = ClientApiKeyValidator.hash_key(api_key_raw)

    api_key = ApiKey.create(name=api_key_data.name, api_key_hash=api_key_hash)
    repo = ApiKeyRepository(db)
    await repo.create(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        api_key=api_key_raw,
        message="Store this API key securely. It will not be shown again.",
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    active_only: bool = False,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = ApiKeyRepository(db)
    api_keys = await repo.get_all(active_only=active_only)
    return [ApiKeyResponse(**k.to_dict()) for k in api_keys]


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = ApiKeyRepository(db)
    api_key = await repo.get_by_id(api_key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyResponse(**api_key.to_dict())


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: str,
    api_key_data: ApiKeyUpdate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = ApiKeyRepository(db)
    api_key = await repo.get_by_id(api_key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    if api_key_data.name is not None:
        api_key.name = api_key_data.name

    api_key.updated_at = datetime.utcnow().isoformat()
    await repo.update(api_key)
    return ApiKeyResponse(**api_key.to_dict())


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    repo = ApiKeyRepository(db)
    api_key = await repo.get_by_id(api_key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await repo.delete(api_key_id)
