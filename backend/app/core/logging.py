import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("ai_case_manager")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
