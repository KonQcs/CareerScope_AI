from fastapi import APIRouter

from . import candidates, health, jobs, matching, portfolio

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(candidates.router)
api_router.include_router(portfolio.router)
api_router.include_router(jobs.router)
api_router.include_router(matching.router)

__all__ = ["api_router"]
