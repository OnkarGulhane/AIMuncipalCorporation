import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.schemas.health import HealthResponse, ReadyResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def get_health() -> HealthResponse:
    """
    Basic health/liveness probe returning application status and version.
    """
    return HealthResponse(
        status="healthy",
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@router.get("/ready", response_model=ReadyResponse, summary="Readiness probe")
def get_ready(db: Session = Depends(get_db)) -> ReadyResponse:
    """
    Readiness probe verifying that the application can communicate with PostgreSQL / the database.
    """
    try:
        db.execute(text("SELECT 1"))
        return ReadyResponse(
            status="ready",
            database="connected",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
    except Exception as exc:
        logger.error(f"Database readiness check failed: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(exc),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
