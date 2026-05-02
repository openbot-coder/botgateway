from fastapi import FastAPI

from .api.auth import AuthConfig
from .api.health import router as health_router


def create_app(management_token: str = "") -> FastAPI:
    AuthConfig.set_token(management_token)
    
    app = FastAPI(title="BotGateway", version="0.2.0")
    
    app.include_router(health_router)
    
    @app.get("/")
    async def root():
        return {"message": "BotGateway API"}
    
    return app