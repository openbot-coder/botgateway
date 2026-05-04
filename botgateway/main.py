from contextlib import asynccontextmanager

from fastapi import FastAPI

from botgateway.db import Database

from .api.admin import (
    api_keys_router,
    model_groups_router,
    models_router,
    providers_router,
)
from .api.auth import AuthConfig
from .api.chat import router as chat_router
from .api.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database.get_database()
    await db.init_schema()
    yield
    await db.close()


def create_app(management_token: str = "") -> FastAPI:
    AuthConfig.set_token(management_token)

    app = FastAPI(title="BotGateway", version="0.3.0", lifespan=lifespan)

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(providers_router, prefix="/admin")
    app.include_router(models_router, prefix="/admin")
    app.include_router(model_groups_router, prefix="/admin")
    app.include_router(api_keys_router, prefix="/admin")

    @app.get("/")
    async def root():
        return {"message": "BotGateway API v0.3.0", "version": "0.3.0"}

    return app
