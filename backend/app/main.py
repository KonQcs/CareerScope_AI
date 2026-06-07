from fastapi import FastAPI

from backend.app.api.routes import router
from backend.app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="CareerScope AI API for CV, portfolio, and job-market matching.",
    )
    app.include_router(router, prefix="/api")

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "status": "ready",
            "docs": "/docs",
        }

    return app


app = create_app()
