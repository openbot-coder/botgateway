from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from botgateway.core.retry import ErrorRetryHandler, RetryExecutor
from botgateway.core.router import CooldownTracker, Router
from botgateway.core.sdk_adapter import SDKError, get_adapter
from botgateway.db import (
    Database,
    ModelGroupRepository,
    ModelRepository,
    ProviderRepository,
)

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    stream: bool | None = False


class ChatCompletionResponse(BaseModel):
    id: str
    model: str
    choices: list[dict[str, Any]]
    usage: dict[str, int]


def get_db() -> Database:
    return Database.get_database()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    db: Database = Depends(get_db),
):
    model_group_name = request.model

    group_repo = ModelGroupRepository(db)
    group = await group_repo.get_by_name(model_group_name)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model group '{model_group_name}' not found"
        )

    if not group.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model group is not active"
        )

    router_instance = Router(db)
    cooldown_tracker = CooldownTracker()
    retry_handler = ErrorRetryHandler.from_model_group(group)
    retry_executor = RetryExecutor(retry_handler)

    provider_repo = ProviderRepository(db)

    selected_model = await router_instance.select_model(group, cooldown_tracker)

    if not selected_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No available models in the model group"
        )

    provider = await provider_repo.get_by_id(selected_model.provider_id)

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Provider not found for selected model"
        )

    if not provider.is_active:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provider is not active"
        )

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def call_api():
        adapter = get_adapter(provider.api_type)
        return await adapter.chat_completions(
            provider=provider,
            model=selected_model,
            messages=messages,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens or selected_model.max_tokens,
        )

    try:
        response = await retry_executor.execute_with_retry(
            selected_model.id,
            call_api,
        )
    except SDKError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )

    return JSONResponse(content=response)


@router.get("/v1/models")
async def list_models(
    db: Database = Depends(get_db),
):
    model_repo = ModelRepository(db)
    models = await model_repo.get_all(active_only=True)

    provider_repo = ProviderRepository(db)
    providers = await provider_repo.get_all(active_only=True)
    providers_map = {p.id: p for p in providers}

    model_list = []
    for model in models:
        provider = providers_map.get(model.provider_id)
        model_list.append({
            "id": model.id,
            "object": "model",
            "created": 0,
            "owned_by": provider.name if provider else "unknown",
            "permission": [],
            "root": model.name,
            "parent": None,
        })

    return {
        "object": "list",
        "data": model_list,
    }
