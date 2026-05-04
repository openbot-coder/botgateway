from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from botgateway.api.auth import verify_management_token
from botgateway.db import Database, Model, ModelRepository, ProviderRepository

router = APIRouter(prefix="/models", tags=["models"])


class ModelCreate(BaseModel):
    provider_id: str
    name: str
    model_type: str = "chat"
    max_tokens: int | None = None
    temperature: float = 0.7
    top_p: float = 1.0
    timeout: int = 60
    extra_params: dict | None = None


class ModelUpdate(BaseModel):
    name: str | None = None
    model_type: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    timeout: int | None = None
    extra_params: dict | None = None


class ModelResponse(BaseModel):
    id: str
    provider_id: str
    name: str
    model_type: str
    max_tokens: int | None
    temperature: float
    top_p: float
    timeout: int
    extra_params: dict | None
    is_active: bool
    created_at: str
    updated_at: str


def get_db() -> Database:
    return Database.get_database()


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    provider_repo = ProviderRepository(db)
    provider = await provider_repo.get_by_id(model_data.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    model = Model.create(
        provider_id=model_data.provider_id,
        name=model_data.name,
        model_type=model_data.model_type,
        max_tokens=model_data.max_tokens,
        temperature=model_data.temperature,
        top_p=model_data.top_p,
        timeout=model_data.timeout,
        extra_params=model_data.extra_params,
    )

    model_repo = ModelRepository(db)
    await model_repo.create(model)
    return ModelResponse(**model.to_dict())


@router.get("", response_model=list[ModelResponse])
async def list_models(
    provider_id: str | None = None,
    active_only: bool = True,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    model_repo = ModelRepository(db)
    models = await model_repo.get_all(provider_id=provider_id, active_only=active_only)
    return [ModelResponse(**m.to_dict()) for m in models]


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    model_repo = ModelRepository(db)
    model = await model_repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse(**model.to_dict())


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str,
    model_data: ModelUpdate,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    model_repo = ModelRepository(db)
    model = await model_repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model_data.name is not None:
        model.name = model_data.name
    if model_data.model_type is not None:
        model.model_type = model_data.model_type
    if model_data.max_tokens is not None:
        model.max_tokens = model_data.max_tokens
    if model_data.temperature is not None:
        model.temperature = model_data.temperature
    if model_data.top_p is not None:
        model.top_p = model_data.top_p
    if model_data.timeout is not None:
        model.timeout = model_data.timeout
    if model_data.extra_params is not None:
        import json
        model.extra_params = json.dumps(model_data.extra_params)

    model.updated_at = datetime.utcnow().isoformat()
    await model_repo.update(model)
    return ModelResponse(**model.to_dict())


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: str,
    db: Database = Depends(get_db),
    token: str = Depends(verify_management_token),
):
    model_repo = ModelRepository(db)
    model = await model_repo.get_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await model_repo.delete(model_id)
