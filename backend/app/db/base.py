"""Async SQLAlchemy engine, session factory, and declarative base."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_async_engine(
    settings.database_url, echo=False, connect_args=connect_args
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Create tables if they don't exist. A schema-migration tool (Alembic)
    is the right long-term approach and is introduced in the production
    hardening phase; for the current feature set, metadata-driven table
    creation is sufficient and keeps local/dev setup to zero extra steps."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
