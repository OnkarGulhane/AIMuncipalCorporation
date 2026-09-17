from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

# Re-export get_db for easy consumption in API routers
DbSession = Depends(get_db)
