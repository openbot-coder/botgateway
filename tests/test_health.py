"""Test health module"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from botgateway.api.health import (
    get_memory_info,
    get_cpu_info,
    get_disk_info,
    get_network_info,
    get_uptime,
    health_check,
    PSUTIL_AVAILABLE,
)


class TestGetMemoryInfo:
    """Test get_memory_info function"""

    def test_returns_dict_with_required_keys(self):
        """正例: 返回包含必需键的字典"""
        if PSUTIL_AVAILABLE:
            result = get_memory_info()
            assert isinstance(result, dict)
            assert "total" in result
            assert "available" in result
            assert "used" in result
            assert "percent" in result

    def test_percent_is_numeric(self):
        """正例: percent 是数值类型"""
        if PSUTIL_AVAILABLE:
            result = get_memory_info()
            assert isinstance(result["percent"], (int, float))

    def test_percent_in_valid_range(self):
        """边界值: percent 在 0-100 范围内"""
        if PSUTIL_AVAILABLE:
            result = get_memory_info()
            assert 0 <= result["percent"] <= 100

    def test_raises_error_when_psutil_not_available(self):
        """反例: psutil 不可用时抛出 RuntimeError"""
        with patch('botgateway.api.health.PSUTIL_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="psutil not available"):
                get_memory_info()


class TestGetCpuInfo:
    """Test get_cpu_info function"""

    def test_returns_dict_with_required_keys(self):
        """正例: 返回包含必需键的字典"""
        if PSUTIL_AVAILABLE:
            result = get_cpu_info()
            assert isinstance(result, dict)
            assert "percent" in result
            assert "count" in result

    def test_count_is_positive_integer(self):
        """边界值: count 是正整数"""
        if PSUTIL_AVAILABLE:
            result = get_cpu_info()
            assert isinstance(result["count"], int)
            assert result["count"] > 0

    def test_percent_is_numeric(self):
        """正例: percent 是数值类型"""
        if PSUTIL_AVAILABLE:
            result = get_cpu_info()
            assert isinstance(result["percent"], (int, float))

    def test_raises_error_when_psutil_not_available(self):
        """反例: psutil 不可用时抛出 RuntimeError"""
        with patch('botgateway.api.health.PSUTIL_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="psutil not available"):
                get_cpu_info()


class TestGetDiskInfo:
    """Test get_disk_info function"""

    def test_returns_dict_with_required_keys(self):
        """正例: 返回包含必需键的字典"""
        if PSUTIL_AVAILABLE:
            result = get_disk_info()
            assert isinstance(result, dict)
            assert "total" in result
            assert "used" in result
            assert "free" in result
            assert "percent" in result

    def test_used_plus_free_equals_total(self):
        """正例: used + free = total"""
        if PSUTIL_AVAILABLE:
            result = get_disk_info()
            assert result["used"] + result["free"] == result["total"]

    def test_percent_in_valid_range(self):
        """边界值: percent 在 0-100 范围内"""
        if PSUTIL_AVAILABLE:
            result = get_disk_info()
            assert 0 <= result["percent"] <= 100

    def test_raises_error_when_psutil_not_available(self):
        """反例: psutil 不可用时抛出 RuntimeError"""
        with patch('botgateway.api.health.PSUTIL_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="psutil not available"):
                get_disk_info()


class TestGetNetworkInfo:
    """Test get_network_info function"""

    def test_returns_dict_with_connections_key(self):
        """正例: 返回包含 connections 键的字典"""
        if PSUTIL_AVAILABLE:
            result = get_network_info()
            assert isinstance(result, dict)
            assert "connections" in result

    def test_connections_is_non_negative(self):
        """边界值: connections 是非负整数"""
        if PSUTIL_AVAILABLE:
            result = get_network_info()
            assert isinstance(result["connections"], int)
            assert result["connections"] >= 0

    def test_raises_error_when_psutil_not_available(self):
        """反例: psutil 不可用时抛出 RuntimeError"""
        with patch('botgateway.api.health.PSUTIL_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="psutil not available"):
                get_network_info()


class TestGetUptime:
    """Test get_uptime function"""

    def test_returns_positive_number(self):
        """正例: 返回正数（运行时间）"""
        if PSUTIL_AVAILABLE:
            result = get_uptime()
            assert isinstance(result, (int, float))
            assert result > 0

    def test_raises_error_when_psutil_not_available(self):
        """反例: psutil 不可用时抛出 RuntimeError"""
        with patch('botgateway.api.health.PSUTIL_AVAILABLE', False):
            with pytest.raises(RuntimeError, match="psutil not available"):
                get_uptime()


class TestHealthCheck:
    """Test health_check endpoint"""

    def _mock_psutil_functions(self):
        """Helper to mock all psutil-dependent functions"""
        return [
            patch('botgateway.api.health.get_memory_info', return_value={"total": 1, "available": 1, "used": 0, "percent": 0}),
            patch('botgateway.api.health.get_cpu_info', return_value={"percent": 0, "count": 4, "freq": None}),
            patch('botgateway.api.health.get_disk_info', return_value={"total": 1, "used": 0, "free": 1, "percent": 0}),
            patch('botgateway.api.health.get_network_info', return_value={"connections": 0}),
            patch('botgateway.api.health.get_process_info', return_value={"pid": 1, "name": "test", "memory_percent": 0, "cpu_percent": 0}),
            patch('botgateway.api.health.get_uptime', return_value=3600),
        ]

    @pytest.mark.asyncio
    async def test_returns_status_healthy(self):
        """正例: 返回 healthy 状态"""
        mock_request = MagicMock()
        mock_request.app.routes = []

        mocks = self._mock_psutil_functions()
        with patch('botgateway.api.health.verify_management_token', return_value="token"):
            with mocks[0], mocks[1], mocks[2], mocks[3], mocks[4], mocks[5]:
                result = await health_check(mock_request)

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_returns_server_time(self):
        """正例: 返回服务器时间"""
        mock_request = MagicMock()
        mock_request.app.routes = []

        mocks = self._mock_psutil_functions()
        with patch('botgateway.api.health.verify_management_token', return_value="token"):
            with mocks[0], mocks[1], mocks[2], mocks[3], mocks[4], mocks[5]:
                result = await health_check(mock_request)

        assert "server_time" in result
        assert result["server_time"].endswith("Z")

    @pytest.mark.asyncio
    async def test_returns_memory_info(self):
        """正例: 返回内存信息"""
        mock_request = MagicMock()
        mock_request.app.routes = []

        mocks = self._mock_psutil_functions()
        with patch('botgateway.api.health.verify_management_token', return_value="token"):
            with patch('botgateway.api.health.get_memory_info', return_value={"total": 100, "available": 50, "used": 50, "percent": 50}):
                with mocks[1], mocks[2], mocks[3], mocks[4], mocks[5]:
                    result = await health_check(mock_request)

        assert "memory" in result
        assert "total" in result["memory"]
        assert result["memory"]["total"] == 100

    @pytest.mark.asyncio
    async def test_returns_cpu_info(self):
        """正例: 返回 CPU 信息"""
        mock_request = MagicMock()
        mock_request.app.routes = []

        mocks = self._mock_psutil_functions()
        with patch('botgateway.api.health.verify_management_token', return_value="token"):
            with mocks[0]:
                with patch('botgateway.api.health.get_cpu_info', return_value={"percent": 25, "count": 4, "freq": None}):
                    with mocks[2], mocks[3], mocks[4], mocks[5]:
                        result = await health_check(mock_request)

        assert "cpu" in result
        assert "percent" in result["cpu"]
        assert result["cpu"]["percent"] == 25

    @pytest.mark.asyncio
    async def test_returns_endpoints_list(self):
        """正例: 返回端点列表"""
        mock_route = MagicMock()
        mock_route.path = "/test"
        mock_route.methods = ["GET"]

        mock_request = MagicMock()
        mock_request.app.routes = [mock_route]

        mocks = self._mock_psutil_functions()
        with patch('botgateway.api.health.verify_management_token', return_value="token"):
            with mocks[0], mocks[1], mocks[2], mocks[3], mocks[4], mocks[5]:
                result = await health_check(mock_request)

        assert "endpoints" in result
        assert len(result["endpoints"]) == 1
        assert result["endpoints"][0]["path"] == "/test"

    @pytest.mark.asyncio
    async def test_auth_failure_returns_404(self):
        """反例: 认证失败返回 404"""
        from fastapi.responses import JSONResponse

        mock_request = MagicMock()

        with patch('botgateway.api.health.verify_management_token',
                   return_value=JSONResponse(status_code=404, content={})):
            result = await health_check(mock_request)

        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_psutil_not_available_returns_500(self):
        """反例: psutil 不可用时返回 500 错误"""
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.app.routes = []

        with patch('botgateway.api.health.verify_management_token', return_value="token"):
            with patch('botgateway.api.health.PSUTIL_AVAILABLE', False):
                with pytest.raises(HTTPException) as exc_info:
                    await health_check(mock_request)

                assert exc_info.value.status_code == 500
                assert "required dependencies not available" in exc_info.value.detail