import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    project: str
    version: str
    environment: str
    timestamp: datetime.datetime


class ReadyResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime.datetime
