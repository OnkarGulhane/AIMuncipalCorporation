import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import health
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.core.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown routines.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    # In development, create tables if using SQLite or fresh db before migrations
    Base.metadata.create_all(bind=engine)
    logger.info("Database connectivity established and schemas checked.")
    
    # Start in-process background scheduler for SLA & Risk monitoring
    start_scheduler()
    
    yield
    
    # Gracefully stop scheduler
    shutdown_scheduler()
    logger.info(f"Shutting down {settings.PROJECT_NAME}.")



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Assisted Municipal Case Management System REST API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level health & readiness endpoints for easy orchestration and container checks
app.include_router(health.router, tags=["Health"])

# V1 API Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
        "health": "/health",
        "ready": "/ready",
        "api_v1": settings.API_V1_STR,
        "server_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
