"""
Database Connection and Session Management
Provides async SQLAlchemy session for PostgreSQL
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine = None
_async_session_maker = None


def get_engine():
    """Get or create async SQLAlchemy engine"""
    global _engine

    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.app_debug,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,  # Verify connections before using
        )
        logger.info(f"Database engine created: {settings.database_url.split('@')[1]}")

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create async session maker"""
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Async session maker created")

    return _async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Yields:
        AsyncSession: Database session

    Example:
        @router.get("/users")
        async def get_users(db: Annotated[AsyncSession, Depends(get_db_session)]):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            await session.close()


async def close_db_connections():
    """Close database connections (call on application shutdown)"""
    global _engine, _async_session_maker

    if _engine:
        await _engine.dispose()
        logger.info("Database engine disposed")
        _engine = None
        _async_session_maker = None
