import logging
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file in the transcritor-pdf directory
# This ensures that when running the transcritor-pdf service, its specific .env is loaded.
load_dotenv(dotenv_path="transcritor-pdf/.env")

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Transcritor-PDF Service"
    LOGGING_LEVEL: int = logging.INFO # Default logging level

    # --- API Keys ---
    GOOGLE_API_KEY: str # Made mandatory as it's now the primary LLM provider key

    # --- Model Configuration ---
    GEMINI_CHAT_MODEL_NAME: str = "gemini-pro" # Default chat model for Gemini
    GEMINI_EMBEDDING_MODEL_NAME: str = "models/text-embedding-004" # Default embedding model for Gemini

    # --- Transcritor-PDF Specific Configuration ---
    EMBEDDING_DIMENSIONS: int = 768 # Updated for Gemini embedding dimension

    # --- Database Configuration ---
    # These are loaded from the .env file, which should be shared or consistent with the backend's.
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None # Sync URL
    ASYNC_DATABASE_URL: Optional[str] = None # Async URL for SQLAlchemy

    # --- Celery / Redis Configuration ---
    CELERY_BROKER_URL: Optional[str] = "redis://redis:6379/0"
    CELERY_BACKEND_URL: Optional[str] = "redis://redis:6379/1"

    # --- Transcritor-PDF Service Specific ---
    TRANSCRITOR_PDF_PORT: int = 8001
    INTERNAL_API_KEY: str # For securing internal API calls - Made mandatory
    # Ensure INTERNAL_API_KEY is set in .env or environment for production.
    # Example: INTERNAL_API_KEY=your_strong_random_internal_api_key_here

    # Transcritor-PDF Logging Level (can be different from backend if needed)
    TRANSCRITOR_LOGGING_LEVEL: int = logging.INFO

    # Pydantic V2 Config using ConfigDict
    model_config = {
        "env_file": "transcritor-pdf/.env",
        "env_file_encoding": 'utf-8',
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings.
    This ensures that the .env file is read and parsed only once.
    """
    return Settings()

# Global instance of settings to be imported and used by other modules
settings = get_settings()

from pythonjsonlogger.jsonlogger import JsonFormatter # Corrected import path

# Configure logging for the transcritor-pdf service based on settings
# This should be called early in the application startup.
def setup_logging():
    # Get the root logger
    root_logger = logging.getLogger()
    # Set the level for the root logger from settings
    root_logger.setLevel(settings.LOGGING_LEVEL)

    # Remove any existing handlers to avoid duplicate logs if this is called multiple times
    # or if basicConfig was called elsewhere.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create a stream handler (outputs to stderr by default)
    log_handler = logging.StreamHandler()

    # Create a JSON formatter
    # Example format: includes standard log record attributes, plus some custom ones if needed
    # For a comprehensive list of default attributes: https://docs.python.org/3/library/logging.html#logrecord-attributes
    formatter = JsonFormatter( # Use the imported JsonFormatter
        "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(lineno)d %(message)s",
        rename_fields={"levelname": "level"} # Optional: rename fields
    )

    log_handler.setFormatter(formatter)
    root_logger.addHandler(log_handler)

    # Configure specific log levels for noisy libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Quieten Uvicorn access logs unless error
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # Quieten SQLAlchemy engine logs unless warning/error
    # Add more specific logger level settings here as needed

    # Test log to confirm setup
    # logger = logging.getLogger(__name__) # Get a logger for the current module
    # logger.info("JSON logging configured.", extra={'custom_field': 'custom_value'})


if __name__ == "__main__":
    # Example of how to use the settings
    # This will also demonstrate that .env loading is working as expected.
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Project Name: {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Async DB URL (from settings): {settings.ASYNC_DATABASE_URL}")
    logger.info(f"Google API Key (from settings): {'Set' if settings.GOOGLE_API_KEY else 'Not Set'}")
    logger.info(f"Gemini Chat Model: {settings.GEMINI_CHAT_MODEL_NAME}")
    logger.info(f"Gemini Embedding Model: {settings.GEMINI_EMBEDDING_MODEL_NAME}")
    logger.info(f"Embedding Dimensions: {settings.EMBEDDING_DIMENSIONS}")
    logger.info(f"Internal API Key (from settings): {'Set' if settings.INTERNAL_API_KEY else 'Not Set'}")

    if not settings.ASYNC_DATABASE_URL:
        logger.error("ASYNC_DATABASE_URL is not set in the environment or .env file for transcritor-pdf!")
    if not settings.GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is not set. LLM functionalities will fail.")
    if not settings.INTERNAL_API_KEY: # Already mandatory by type, but good for explicit check if logic changes
        logger.error("INTERNAL_API_KEY is not set. The service is insecure and will likely fail authorization.")
