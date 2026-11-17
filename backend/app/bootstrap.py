"""Create tables and seed the dashboard administrator when a database exists.

The webhook must stay reachable even if Supabase is down, so every failure here
is logged and swallowed instead of aborting application startup.
"""

import logging

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (registers metadata before create_all)
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import User
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


def ensure_admin(db: Session) -> User | None:
    """Idempotently create the admin account described by ADMIN_EMAIL/PASSWORD."""
    email = settings.ADMIN_EMAIL.strip().lower()
    password = settings.ADMIN_PASSWORD
    if not email or not password:
        logger.warning("ADMIN_EMAIL/ADMIN_PASSWORD not set; no admin account seeded")
        return None

    user = db.query(User).filter(func.lower(User.email) == email).first()
    if user is not None:
        if not user.hashed_password:
            user.hashed_password = hash_password(password)
            db.commit()
            logger.info("Set password for existing account %s", email)
        return user

    user = User(
        phone=settings.ADMIN_PHONE,
        email=email,
        full_name=settings.ADMIN_NAME,
        role="admin",
        is_verified=True,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Seeded admin account %s", email)
    return user


def init_database() -> None:
    if engine is None or SessionLocal is None:
        logger.warning("DATABASE_URL not set; skipping table creation and admin seed")
        return

    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            ensure_admin(db)
    except SQLAlchemyError as exc:
        logger.error("Database bootstrap failed: %s", exc)
