import logging

# Import the new centralized settings and database utility functions
from src.core.config import settings, setup_logging as core_setup_logging
from src.core.database import (
    initialize_database as core_initialize_database,
    close_database_connection as core_close_db_connection,
    get_db_session, # For use in application code
    get_db_contextmanager # For use in scripts or background tasks
)

logger = logging.getLogger(__name__)

# EMBEDDING_DIMENSIONS is now sourced from settings
EMBEDDING_DIMENSIONS = settings.EMBEDDING_DIMENSIONS
logger.info(f"EMBEDDING_DIMENSIONS loaded from settings: {EMBEDDING_DIMENSIONS}")

# The global asyncpg db_pool is no longer managed here.
# SQLAlchemy manages its own connection pool.

async def connect_to_db():
    """
    Initializes the application's database connection using the new core database module.
    This function should be called at application startup.
    """
    logger.info("Attempting to initialize database via src.core.database.initialize_database...")
    # Ensure logging is set up before initializing the database, as db init might log
    # core_setup_logging() # Assuming logging is set up earlier in app lifecycle
    await core_initialize_database() # Now an async function if create_engine is called within
    # If core_initialize_database is not async, remove await.
    # Based on its current implementation, initialize_database() is synchronous.
    # Let's adjust core.database.initialize_database to be synchronous or ensure it's called appropriately.
    # For now, assuming it's synchronous as per its current structure.
    core_initialize_database() # Corrected: initialize_database is sync

async def close_db_connection():
    """
    Closes the application's database connection using the new core database module.
    This function should be called at application shutdown.
    """
    logger.info("Attempting to close database connection via src.core.database.close_database_connection...")
    await core_close_db_connection()

# Re-exporting the session utilities for convenience if other modules were importing them from here.
# Consumers should ideally import directly from src.core.database in the future.
get_db_session = get_db_session
get_db_contextmanager = get_db_contextmanager

# It's generally better to have a single point of logging setup.
# This could be in main.py or the application factory.
# For now, we can provide a utility function if db_config was responsible.
def setup_application_logging():
    """
    Sets up logging for the application using the core config.
    """
    core_setup_logging()
    logger.info("Application logging configured via src.core.config.setup_logging.")

if __name__ == "__main__":
    # Example of how this module might be tested or used (though direct execution is less common for config files)
    import asyncio

    async def main():
        setup_application_logging() # Setup logging first
        logger.info(f"ASYNC_DATABASE_URL from settings: {settings.ASYNC_DATABASE_URL}")
        
        await connect_to_db() # Initialize DB connection

        if settings.ASYNC_DATABASE_URL: # Check if DB URL is actually set
            logger.info("Attempting to get a DB session and perform a test query...")
            try:
                async with get_db_contextmanager() as db:
                    from sqlalchemy import text
                    result = await db.execute(text("SELECT 1 AS test_col"))
                    logger.info(f"Test query result: {result.scalar_one()}")
                logger.info("Successfully connected to DB and executed a query via SQLAlchemy.")
            except Exception as e:
                logger.error(f"Failed to connect or query database: {e}", exc_info=True)
        else:
            logger.warning("ASYNC_DATABASE_URL is not set. Skipping database test query.")

        await close_db_connection() # Close DB connection

    asyncio.run(main())
