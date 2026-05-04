"""Test main module"""


from botgateway.api.auth import AuthConfig
from botgateway.main import create_app


class TestCreateApp:
    """Test create_app function"""

    def test_create_app_returns_fastapi_instance(self):
        """正例: 返回 FastAPI 实例"""
        app = create_app(management_token="test-token")
        assert app is not None
        assert app.title == "BotGateway"
        assert app.version == "0.4.0"

    def test_create_app_sets_auth_token(self):
        """正例: 设置认证 token"""
        create_app(management_token="my-secret-token")
        assert AuthConfig.get_token() == "my-secret-token"

    def test_create_app_includes_health_route(self):
        """正例: 包含健康检查路由"""
        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/health" in routes

    def test_create_app_includes_root_route(self):
        """正例: 包含根路由"""
        app = create_app()
        routes = [route.path for route in app.routes]
        assert "/" in routes

    def test_create_app_with_empty_token(self):
        """边界值: 空 token 也被设置"""
        create_app(management_token="")
        assert AuthConfig.get_token() == ""
