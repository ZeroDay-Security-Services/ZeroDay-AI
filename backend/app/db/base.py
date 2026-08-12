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
    """Create tables if they don't exist. Also applies safe additive migrations
    for columns added after initial schema creation (e.g. agent_id)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Safe migration: add agent_id to conversations if it doesn't exist yet.
        # Works for both SQLite and PostgreSQL.
        if settings.database_url.startswith("sqlite"):
            # SQLite: check pragma, then add column
            result = await conn.execute(
                __import__("sqlalchemy").text("PRAGMA table_info(conversations)")
            )
            columns = [row[1] for row in result.fetchall()]
            if "agent_id" not in columns:
                await conn.execute(
                    __import__("sqlalchemy").text(
                        "ALTER TABLE conversations ADD COLUMN agent_id VARCHAR(64) NOT NULL DEFAULT 'assistant'"
                    )
                )
        else:
            # PostgreSQL: use DO block for idempotent ADD COLUMN
            await conn.execute(
                __import__("sqlalchemy").text(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='conversations' AND column_name='agent_id'
                        ) THEN
                            ALTER TABLE conversations ADD COLUMN agent_id VARCHAR(64) NOT NULL DEFAULT 'assistant';
                            CREATE INDEX IF NOT EXISTS ix_conversations_agent_id ON conversations(agent_id);
                        END IF;
                    END $$;
                    """
                )
            )

