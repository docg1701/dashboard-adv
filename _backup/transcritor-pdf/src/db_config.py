import asyncpg
import os
import logging

logger = logging.getLogger(__name__)

# Attempt to use ASYNC_DATABASE_URL first, then DATABASE_URL
# The default value is a placeholder and should ideally not be used if .env is set up correctly.
ASYNC_DB_URL_FROM_ENV = os.getenv("ASYNC_DATABASE_URL")
DB_URL_FROM_ENV = os.getenv("DATABASE_URL")

if ASYNC_DB_URL_FROM_ENV:
    DATABASE_URL = ASYNC_DB_URL_FROM_ENV
    logger.info(f"Using ASYNC_DATABASE_URL for transcritor-pdf: {DATABASE_URL}")
elif DB_URL_FROM_ENV:
    # If using a sync URL for an async app, ensure it's adapted if necessary,
    # though asyncpg typically expects the connection string without a specific +driver.
    # For simplicity, we'll assume it's compatible or will be made so.
    DATABASE_URL = DB_URL_FROM_ENV
    logger.info(f"Using DATABASE_URL for transcritor-pdf: {DATABASE_URL}")
    # Potentially adapt if it's a sync-only DSN like 'postgresql://...' for asyncpg
    if not DATABASE_URL.startswith("postgresql+asyncpg://") and DATABASE_URL.startswith("postgresql://"):
         # This basic replacement might not cover all cases but is a common adaptation.
         # DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
         # logger.info(f"Adapted DATABASE_URL for asyncpg: {DATABASE_URL}")
         # For now, let's assume the URL provided in .env is suitable or will be adjusted there.
         pass # Keep it simple, rely on .env to provide a compatible URL
else:
    # Fallback if neither is set (should not happen in a configured environment)
    DATABASE_URL = "postgresql+asyncpg://user:pass@host:port/db" # Placeholder
    logger.warning("Neither ASYNC_DATABASE_URL nor DATABASE_URL found in environment. Using placeholder for transcritor-pdf.")

# The rest of the file (db_pool, connect_to_db, close_db_connection)
# will use this DATABASE_URL.

# Placeholder for embedding dimensions - this might come from a model config later
# For now, common dimensions are 384 (e.g., all-MiniLM-L6-v2), 768 (e.g., BERT base), 1536 (OpenAI Ada-002)
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# Global variable for the connection pool
# Explicitly type hint that it can be None initially
db_pool: asyncpg.Pool | None = None

async def connect_to_db():
    """
    Establishes a global database connection pool.
    This function is called once at FastAPI application startup.
    """
    global db_pool
    if db_pool:
        logger.info("Database pool already exists.")
        return

    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set in environment variables.")
        db_pool = None
        return

    logger.info(f"Attempting to connect to database using URL: {DATABASE_URL}")
    try:
        # FIX: asyncpg expects a DSN starting with 'postgresql://', not 'postgresql+asyncpg://'.
        # We replace the SQLAlchemy-specific scheme with the asyncpg-compatible one.
        compatible_dsn = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
        
        pool = await asyncpg.create_pool(
            dsn=compatible_dsn,
            min_size=1,
            max_size=10,
            # Add other pool options here if needed, e.g., command_timeout
        )
        db_pool = pool
        logger.info("Successfully connected to the database and created pool.")
    except (asyncpg.exceptions.PostgresError, OSError) as e:
        logger.error(f"Failed to connect to the database and create pool: {e}", exc_info=True)
        db_pool = None

async def close_db_connection():
    """
    Closes the database connection pool if it exists.
    """
    global db_pool
    if db_pool:
        logger.info("Closing database connection pool...")
        try:
            await db_pool.close()
            db_pool = None # Ensure it's reset
            logger.info("Database connection pool closed successfully.")
        except Exception as e:
            logger.error(f"Error while closing database connection pool: {e}", exc_info=True)
    else:
        logger.info("No active database connection pool to close.")

# Example of how to use (typically called at app startup/shutdown):
# async def main_app_lifecycle():
#     await connect_to_db()
#     # ... your application runs ...
#     if db_pool: # Check if pool was successfully created
#         # Example usage
#         async with db_pool.acquire() as conn:
#             val = await conn.fetchval("SELECT $1::TEXT", "Hello DB")
#             print(f"Test query result: {val}")
#     await close_db_connection()

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO) # Ensure logger is configured for standalone run
#     asyncio.run(main_app_lifecycle())
