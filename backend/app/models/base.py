import datetime
from sqlalchemy import Column, Integer, DateTime
from app.core.database import Base


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

