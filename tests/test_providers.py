"""Test admin providers module - audit log failure handling"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from botgateway.api.admin.providers import audit_operation


@pytest.mark.asyncio
async def test_audit_log_failure_logs_warning():
    """反例: 审计日志写入失败时记录 warning，主流程不受影响"""
    mock_repo = MagicMock()
    mock_repo.add_operation_log = AsyncMock(
        side_effect=RuntimeError("db write failed")
    )

    main_executed = False

    with patch("botgateway.api.admin.providers.logger") as mock_logger:
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

    with patch("botgateway.api.admin.providers.logger") as mock_logger:
        async with audit_operation(mock_repo, "test_op", "test_detail"):
            main_executed = True

    assert main_executed is True
    mock_logger.warning.assert_not_called()
    mock_repo.add_operation_log.assert_called_once()
