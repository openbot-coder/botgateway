import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AuthConfig:
    _management_token: str = ""

    @classmethod
    def set_token(cls, token: str):
        cls._management_token = token

    @classmethod
    def get_token(cls) -> str:
        return cls._management_token


def verify_management_token(request: Request):
    try:
        token = AuthConfig.get_token()
        if not token:
            return JSONResponse(status_code=404, content={})

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(status_code=404, content={})

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return JSONResponse(status_code=404, content={})

        if parts[1] != token:
            return JSONResponse(status_code=404, content={})

        return token
    except Exception as e:
        logger.error("Auth error: %s", e, exc_info=True)
        return JSONResponse(status_code=404, content={})
