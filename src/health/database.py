"""Database configuration and session management for health metrics."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


class DatabaseConfig:
    """Database configuration for health metrics."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or self._get_default_url()
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_default_url(self) -> str:
        """Get default database URL (SQLite for single user)."""
        db_path = os.getenv("HEALTH_DATABASE_URL", "health_metrics.db")
        return f"sqlite:///{db_path}"

    def create_tables(self) -> None:
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Generator[Session, None, None]:
        """Get database session."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Global database instance
_db_config: DatabaseConfig | None = None


def get_database() -> DatabaseConfig:
    """Get global database configuration."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
        _db_config.create_tables()
    return _db_config


def get_db_session() -> Generator[Session, None, None]:
    """Get database session (dependency injection)."""
    db = get_database()
    yield from db.get_session()
