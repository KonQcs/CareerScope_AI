from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import api_router
from backend.app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="CareerScope AI API for CV, portfolio, and job-market matching.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "status": "ready",
            "docs": "/docs",
        }

    return app


app = create_app()
