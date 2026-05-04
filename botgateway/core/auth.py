from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from botgateway.db import ApiKeyRepository, Database


class AuthMiddleware(BaseHTTPMiddleware):
    # UNCOVERED: Starlette 中间件需要集成测试，使用真实 HTTP 请求验证
    def __init__(self, app, excluded_paths: list[str] | None = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    # UNCOVERED: 中间件需要集成测试
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        for excluded in self.excluded_paths:
            if path == excluded or path.startswith(excluded + "/"):
                return await call_next(request)

        api_key = self._extract_api_key(request)
        db = Database.get_database()

        api_key_count = await ApiKeyRepository(db).count()

        if api_key_count > 0:
            if not api_key:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "message": "API key is required"}
                )

            from .encryptor import ClientApiKeyValidator
            api_key_hash = ClientApiKeyValidator.hash_key(api_key)
            repo = ApiKeyRepository(db)
            stored_key = await repo.get_by_hash(api_key_hash)

            if not stored_key:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Unauthorized", "message": "Invalid API key"}
                )

        return await call_next(request)

    # UNCOVERED: 中间件集成测试覆盖
    def _extract_api_key(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        api_key_header = request.headers.get("X-API-Key", "")
        if api_key_header:
            return api_key_header

        return None


# UNCOVERED: 仅供管理接口使用，详见 test_auth.py
async def verify_api_key(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    api_key_header = request.headers.get("X-API-Key", "")
    if api_key_header:
        return api_key_header

    return None
