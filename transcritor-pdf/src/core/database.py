from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, DeclarativeBase
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import logging

# Import settings from the new core.config module
from .config import settings

logger = logging.getLogger(__name__)

# Use the ASYNC Database URL from transcritor-pdf's settings
ASYNC_DATABASE_URL = settings.ASYNC_DATABASE_URL

async_engine = None
async_session_local: async_sessionmaker[AsyncSession] | None = None

def initialize_database():
    """
    Initializes the async database engine and session maker.
    This function should be called at application startup.
    """
    global async_engine, async_session_local

    if not ASYNC_DATABASE_URL:
        logger.error("ASYNC_DATABASE_URL not set in transcritor-pdf settings. Async database connection cannot be established.")
        # Potentially raise an error or handle this state as critical
        return

    try:
        logger.info(f"Initializing SQLAlchemy async engine with URL: {ASYNC_DATABASE_URL}")
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=settings.ENVIRONMENT == "development", # Log SQL queries only in development
            pool_pre_ping=True, # Helps with connection validity
            # pool_size=settings.DB_POOL_MIN_SIZE, # If we want to control pool size via settings
            # max_overflow=settings.DB_POOL_MAX_SIZE - settings.DB_POOL_MIN_SIZE, # Example
        )
        async_session_local = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        logger.info("SQLAlchemy async engine and session maker configured successfully for transcritor-pdf.")
    except Exception as e:
        logger.error(f"Failed to configure SQLAlchemy async engine/session maker for transcritor-pdf: {e}", exc_info=True)
        async_engine = None
        async_session_local = None
        # Consider re-raising or exiting if DB is critical for startup

# Base class for declarative class definitions for transcritor-pdf models (if any are defined with SQLAlchemy)
# If transcritor-pdf primarily reads from tables defined by the backend's models, it might not need its own Base.
# However, for consistency and potential future local tables, it's good to have.
class Base(DeclarativeBase):
    pass

# Dependency function for FastAPI endpoints (if transcritor-pdf uses FastAPI and needs DB sessions per request)
# Or, a general utility to get a session for Celery tasks.
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an SQLAlchemy AsyncSession.
    Designed for use as a dependency or in a 'with' statement via asynccontextmanager.
    """
    if async_session_local is None:
        logger.error("Database session factory (async_session_local) is not configured for transcritor-pdf.")
        # This indicates initialize_database() was not called or failed.
        raise RuntimeError("Database session factory is not available in transcritor-pdf.")

    session: AsyncSession = async_session_local()
    logger.debug(f"Yielding database session: {session}")
    try:
        yield session
    except Exception:
        logger.exception("Exception during database session scope in transcritor-pdf, rolling back.")
        await session.rollback()
        raise
    finally:
        logger.debug(f"Closing database session: {session}")
        await session.close()

@asynccontextmanager
async def get_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an SQLAlchemy AsyncSession within an async context manager.
    Useful for scripts or background tasks where dependency injection isn't available.
    """
    if async_session_local is None:
        logger.error("Database session factory (async_session_local) is not configured for transcritor-pdf context manager.")
        raise RuntimeError("Database session factory is not available for transcritor-pdf context manager.")

    session: AsyncSession = async_session_local()
    logger.debug(f"Yielding database session from context manager: {session}")
    try:
        yield session
    except Exception:
        logger.exception("Exception within database context manager scope in transcritor-pdf, rolling back.")
        await session.rollback()
        raise
    finally:
        logger.debug(f"Closing database session from context manager: {session}")
        await session.close()

async def close_database_connection():
    """
    Closes the database engine. Call on application shutdown.
    """
    global async_engine
    if async_engine:
        logger.info("Closing SQLAlchemy async engine for transcritor-pdf.")
        await async_engine.dispose()
        async_engine = None
        logger.info("SQLAlchemy async engine for transcritor-pdf closed.")

# Example of how this might be used in main.py or an app factory
# async def startup_event():
#     setup_logging() # from core.config
#     initialize_database()
#     logger.info("Transcritor-PDF application startup complete.")

# async def shutdown_event():
#     await close_database_connection()
#     logger.info("Transcritor-PDF application shutdown complete.")

if __name__ == "__main__":
    # Basic test for database initialization
    # This requires .env to be correctly set up.
    import asyncio
    from .config import setup_logging as setup_transcritor_logging

    async def test_db_connection():
        setup_transcritor_logging() # Initialize logging from transcritor's config
        initialize_database()

        if async_session_local:
            logger.info("Attempting to connect and query...")
            try:
                async with get_db_contextmanager() as db:
                    # Example: Perform a simple query if you have a table or just test connection
                    # For now, a raw SQL execution to test the connection
                    from sqlalchemy import text
                    result = await db.execute(text("SELECT 1"))
                    logger.info(f"Test query result: {result.scalar_one()}")
                logger.info("Database connection test successful.")
            except Exception as e:
                logger.error(f"Database connection test failed: {e}", exc_info=True)
        else:
            logger.error("async_session_local is None, cannot test DB connection.")

        await close_database_connection()

    asyncio.run(test_db_connection())
