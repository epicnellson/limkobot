import logging

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _build_engine():
    """A broken DATABASE_URL or missing driver must not stop the app from serving."""
    try:
        connect_args = {}
        if settings.DATABASE_URL.startswith("postgresql"):
            connect_args["connect_timeout"] = settings.DB_CONNECT_TIMEOUT_SECONDS
        return create_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    except Exception as exc:  # noqa: BLE001 - log and degrade to database-less mode
        logger.error("Could not create database engine: %s", exc)
        return None


if settings.DATABASE_URL:
    engine = _build_engine()
    SessionLocal = (
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
        if engine is not None
        else None
    )
else:
    engine = None
    SessionLocal = None


def get_db():
    if SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured (set DATABASE_URL)",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
