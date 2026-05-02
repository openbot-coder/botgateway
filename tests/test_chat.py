"""Test chat module - audit log failure handling and async verification"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from botgateway.api.chat import (
    ChatCompletionRequest,
    ChatMessage,
    audit_operation,
    chat_completions,
)
from botgateway.db.models import Model, ModelGroup, Provider


@pytest.mark.asyncio
async def test_audit_log_failure_logs_warning():
    """反例: 审计日志写入失败时记录 warning，主流程不受影响"""
    mock_repo = MagicMock()
    mock_repo.add_operation_log = AsyncMock(
        side_effect=RuntimeError("db write failed")
    )

    main_executed = False

    with patch("botgateway.api.chat.logger") as mock_logger:
        async with audit_operation(mock_repo, "test_op", "test_detail"):
            main_executed = True

    assert main_executed is True
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args
    assert "audit" in call_args[0][0].lower() or "log" in call_args[0][0].lower()


@pytest.mark.asyncio
async def test_audit_log_success_no_warning():
    """正例: 审计日志写入成功时不记录 warning"""
    mock_repo = MagicMock()
    mock_repo.add_operation_log = AsyncMock(return_value=None)

    main_executed = False

    with patch("botgateway.api.chat.logger") as mock_logger:
        async with audit_operation(mock_repo, "test_op", "test_detail"):
            main_executed = True

    assert main_executed is True
    mock_logger.warning.assert_not_called()
    mock_repo.add_operation_log.assert_called_once()


def _build_chat_mocks():
    """Helper to build mock dependencies for chat_completions endpoint."""
    mock_group = ModelGroup.create(name="test-group")
    mock_model = Model(id="m1", provider_id="p1", name="gpt-3.5-turbo", max_tokens=100)
    mock_provider = Provider(id="p1", name="openai", api_type="openai", is_active=True)

    mock_db = MagicMock()

    mock_group_repo = MagicMock()
    mock_group_repo.get_by_name = AsyncMock(return_value=mock_group)

    mock_provider_repo = MagicMock()
    mock_provider_repo.get_by_id = AsyncMock(return_value=mock_provider)

    mock_router = MagicMock()
    mock_router.select_model = AsyncMock(return_value=mock_model)

    mock_adapter = MagicMock()
    mock_adapter.chat_completions = AsyncMock(
        return_value={"id": "test", "choices": [], "usage": {}}
    )

    mock_retry_handler = MagicMock()

    async def _execute_with_retry_side_effect(model_id, func, *args, **kwargs):
        return await func(*args, **kwargs)

    mock_retry_executor = MagicMock()
    mock_retry_executor.execute_with_retry = AsyncMock(
        side_effect=_execute_with_retry_side_effect
    )

    return {
        "db": mock_db,
        "group_repo": mock_group_repo,
        "provider_repo": mock_provider_repo,
        "router": mock_router,
        "adapter": mock_adapter,
        "retry_handler": mock_retry_handler,
        "retry_executor": mock_retry_executor,
    }


@pytest.mark.asyncio
async def test_chat_completions_uses_await_adapter():
    """正例: chat_completions 使用 await 调用适配器的 chat_completions"""
    mocks = _build_chat_mocks()

    request = ChatCompletionRequest(
        model="test-group",
        messages=[ChatMessage(role="user", content="Hello")],
    )

    with (
        patch("botgateway.api.chat.ModelGroupRepository", return_value=mocks["group_repo"]),
        patch("botgateway.api.chat.ProviderRepository", return_value=mocks["provider_repo"]),
        patch("botgateway.api.chat.Router", return_value=mocks["router"]),
        patch("botgateway.api.chat.CooldownTracker"),
        patch("botgateway.api.chat.ErrorRetryHandler") as mock_retry_cls,
        patch("botgateway.api.chat.RetryExecutor", return_value=mocks["retry_executor"]),
        patch("botgateway.api.chat.get_adapter", return_value=mocks["adapter"]),
    ):
        mock_retry_cls.from_model_group.return_value = mocks["retry_handler"]
        response = await chat_completions(request, db=mocks["db"])

    mocks["adapter"].chat_completions.assert_awaited_once()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_completions_uses_await_router():
    """正例: chat_completions 使用 await 调用路由器的 select_model"""
    mocks = _build_chat_mocks()

    request = ChatCompletionRequest(
        model="test-group",
        messages=[ChatMessage(role="user", content="Hello")],
    )

    with (
        patch("botgateway.api.chat.ModelGroupRepository", return_value=mocks["group_repo"]),
        patch("botgateway.api.chat.ProviderRepository", return_value=mocks["provider_repo"]),
        patch("botgateway.api.chat.Router", return_value=mocks["router"]),
        patch("botgateway.api.chat.CooldownTracker"),
        patch("botgateway.api.chat.ErrorRetryHandler") as mock_retry_cls,
        patch("botgateway.api.chat.RetryExecutor", return_value=mocks["retry_executor"]),
        patch("botgateway.api.chat.get_adapter", return_value=mocks["adapter"]),
    ):
        mock_retry_cls.from_model_group.return_value = mocks["retry_handler"]
        response = await chat_completions(request, db=mocks["db"])

    mocks["router"].select_model.assert_awaited_once()
    assert response.status_code == 200
