from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


if settings.DATABASE_URL:
    engine = create_engine(settings.DATABASE_URL, pool_size=settings.DB_POOL_SIZE)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
