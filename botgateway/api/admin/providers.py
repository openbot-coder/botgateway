import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from botgateway.core.encryptor import ApiKeyEncryptor
from botgateway.db import Database, Provider, ProviderRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])


@asynccontextmanager
async def audit_operation(repo, operation_type: str, details: str):
    """Audit operation context manager.

    Yields control to the caller, then logs the operation.
    If the audit log write fails, logs a warning instead of raising.
    """
    try:
        yield
    finally:
        try:
            await repo.add_operation_log(operation_type, details)
        except Exception:
            logger.warning("Failed to write audit log", exc_info=True)


class ProviderCreate(BaseModel):
    name: str
    api_type: str = "openai"
    base_url: str | None = None
    api_key: str | None = None


class ProviderUpdate(BaseModel):
    name: str | None = None
    api_type: str | None = None
    base_url: str | None = None
    api_key: str | None = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    api_type: str
    base_url: str | None
    is_active: bool
    created_at: str
    updated_at: str


def get_db() -> Database:
    return Database.get_database()


def _encrypt_api_key(api_key: str) -> tuple[str, str]:
    if not api_key:
        return None, None
    try:
        encryptor = ApiKeyEncryptor.get_instance()
        return encryptor.encrypt_to_base64(api_key)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to encrypt API key: {str(e)}. "
                   "Please ensure BOTGATEWAY_MASTER_KEY environment variable is set on the server."
        )


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    db: Database = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = Provider.create(
        name=provider_data.name,
        api_type=provider_data.api_type,
        base_url=provider_data.base_url,
    )

    if provider_data.api_key:
        encrypted_key, nonce = _encrypt_api_key(provider_data.api_key)
        provider.api_key_encrypted = encrypted_key
        provider.key_nonce = nonce

    await repo.create(provider)
    return ProviderResponse(**provider.to_dict())


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    active_only: bool = True,
    db: Database = Depends(get_db),
):
    repo = ProviderRepository(db)
    providers = await repo.get_all(active_only=active_only)
    return [ProviderResponse(**p.to_dict()) for p in providers]


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    db: Database = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = await repo.get_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return ProviderResponse(**provider.to_dict())


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    provider_data: ProviderUpdate,
    db: Database = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = await repo.get_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider_data.name is not None:
        provider.name = provider_data.name
    if provider_data.api_type is not None:
        provider.api_type = provider_data.api_type
    if provider_data.base_url is not None:
        provider.base_url = provider_data.base_url
    if provider_data.api_key is not None:
        encrypted_key, nonce = _encrypt_api_key(provider_data.api_key)
        provider.api_key_encrypted = encrypted_key
        provider.key_nonce = nonce

    provider.updated_at = datetime.utcnow().isoformat()
    await repo.update(provider)
    return ProviderResponse(**provider.to_dict())


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: str,
    db: Database = Depends(get_db),
):
    repo = ProviderRepository(db)
    provider = await repo.get_by_id(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await repo.delete(provider_id)
