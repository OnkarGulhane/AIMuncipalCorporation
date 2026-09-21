import os
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.v1.endpoints import health
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.core.scheduler import start_scheduler, shutdown_scheduler


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware injecting hardened HTTP security headers on all responses.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown routines.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    # In development, ensure tables exist
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
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENABLE_DOCS else None,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    lifespan=lifespan,
)

# 1. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. GZip Compression Middleware (High Performance)
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)

# 3. Configure CORS
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

# Register Custom Standardized Exception Handlers (PRD Section 50)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    validation_exception_handler,
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Mount Interactive Web Portal Static App
portal_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static_portal"))
if os.path.exists(portal_dir):
    app.mount("/portal", StaticFiles(directory=portal_dir, html=True), name="portal")


@app.get("/", tags=["Root"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse(url="/portal")
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "portal": "/portal",
        "documentation": "/docs" if settings.ENABLE_DOCS else "disabled",
        "health": "/health",
        "ready": "/ready",
        "api_v1": settings.API_V1_STR,
        "server_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
