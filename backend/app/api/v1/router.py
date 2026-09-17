from fastapi import APIRouter
from app.api.v1.endpoints import health

api_v1_router = APIRouter()

# Include health router (also accessible at /api/v1/health or directly)
api_v1_router.include_router(health.router, tags=["Health"])
