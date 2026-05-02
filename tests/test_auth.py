"""Test auth module"""

import pytest
from unittest.mock import MagicMock

from botgateway.api.auth import AuthConfig, verify_management_token


class TestAuthConfig:
    """Test AuthConfig class"""

    def test_set_and_get_token(self):
        """正例: 设置和获取 token"""
        AuthConfig.set_token("test-token")
        assert AuthConfig.get_token() == "test-token"
        AuthConfig.set_token("")
        assert AuthConfig.get_token() == ""

    def test_default_token_is_empty(self):
        """正例: 默认 token 为空"""
        AuthConfig.set_token("")
        assert AuthConfig.get_token() == ""


class TestVerifyManagementToken:
    """Test verify_management_token function"""

    def setup_method(self):
        """每个测试前重置 token"""
        AuthConfig.set_token("valid-token-123")

    def teardown_method(self):
        """每个测试后清理"""
        AuthConfig.set_token("")

    def test_valid_token_returns_token(self):
        """正例: 有效 token 返回 token 值"""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer valid-token-123"}

        result = verify_management_token(mock_request)
        assert result == "valid-token-123"

    def test_missing_token_config_returns_404(self):
        """反例: 未配置 token 时返回 404"""
        AuthConfig.set_token("")
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer some-token"}

        result = verify_management_token(mock_request)
        assert result.status_code == 404

    def test_missing_authorization_header_returns_404(self):
        """反例: 缺少 Authorization header 返回 404"""
        mock_request = MagicMock()
        mock_request.headers = {}

        result = verify_management_token(mock_request)
        assert result.status_code == 404

    def test_invalid_auth_scheme_returns_404(self):
        """反例: 无效的认证 scheme 返回 404"""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Basic valid-token-123"}

        result = verify_management_token(mock_request)
        assert result.status_code == 404

    def test_malformed_authorization_header_returns_404(self):
        """反例: 格式错误的 Authorization header 返回 404"""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer"}

        result = verify_management_token(mock_request)
        assert result.status_code == 404

    def test_wrong_token_returns_404(self):
        """反例: 错误的 token 返回 404"""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "Bearer wrong-token"}

        result = verify_management_token(mock_request)
        assert result.status_code == 404

    def test_bearer_case_insensitive(self):
        """边界值: Bearer scheme 大小写不敏感"""
        mock_request = MagicMock()
        mock_request.headers = {"Authorization": "bearer valid-token-123"}

        result = verify_management_token(mock_request)
        assert result == "valid-token-123"