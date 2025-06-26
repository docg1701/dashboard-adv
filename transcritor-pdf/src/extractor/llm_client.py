# -*- coding: utf-8 -*-
"""Configures and provides the Large Language Model (LLM) client instance.

This module is responsible for:
1. Loading API credentials (API key, base URL, model name) securely using
   Pydantic settings from `src.core.config`.
2. Initializing a Langchain chat model client (specifically `ChatOpenAI` for
   compatibility with OpenAI API standards, often used by providers like
   OpenRouter) with the loaded configuration.
3. Providing a singleton instance of the initialized client via the
   `get_llm_client` function to ensure configuration is loaded only once.
Includes logging for operations and potential configuration errors.
"""

import sys
import logging
from typing import Optional

from src.core.config import settings # Import Pydantic settings

# Import the specific Langchain chat model class for Google Gemini
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Log critical error if dependency is missing
    logging.critical("langchain-google-genai library not found. Please install it: pip install langchain-google-genai")
    sys.exit(1)

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Singleton Client Instance ---
# Stores the initialized client to avoid re-initialization on subsequent calls.
_llm_client: Optional[ChatGoogleGenerativeAI] = None

def get_llm_client() -> ChatGoogleGenerativeAI:
    """Initializes and returns a singleton Langchain ChatGoogleGenerativeAI client instance.

    On the first call, it loads the API configuration from Pydantic `settings`
    and initializes a `ChatGoogleGenerativeAI` client. Subsequent calls return the same cached client instance.

    Returns:
        An initialized `langchain_google_genai.ChatGoogleGenerativeAI` client instance.

    Raises:
        ValueError: If the required API key (e.g., OPENAI_API_KEY) is not found in settings.
        RuntimeError: If any other error occurs during client initialization.
    """
    global _llm_client
    if _llm_client is None:
        logger.info("Initializing LLM client for Google Gemini using Pydantic settings...")
        try:
            # Load configuration from Pydantic settings
            api_key = settings.GOOGLE_API_KEY # Now using GOOGLE_API_KEY
            model_name = settings.GEMINI_CHAT_MODEL_NAME # Using GEMINI_CHAT_MODEL_NAME

            # GOOGLE_API_KEY is already mandatory in settings, so Pydantic would have failed on load if missing.
            # No need for an explicit 'if not api_key:' check here like before.

            logger.info("Configuring Langchain ChatGoogleGenerativeAI client from settings:")
            logger.info(f"  Model: {model_name}")
            # Base URL is not typically configured for ChatGoogleGenerativeAI in the same way as ChatOpenAI
            # It uses standard Google API endpoints.
            # Intentionally DO NOT log the API key for security

            # Initialize the ChatGoogleGenerativeAI client
            client_params = {
                "model": model_name,
                "google_api_key": api_key,
                # "convert_system_message_to_human": True, # Deprecated, remove.
                # System messages are typically handled by prefixing to human message or specific model params.
            }

            # Optional parameters can also be sourced from settings if needed
            # e.g., client_params["temperature"] = settings.GEMINI_TEMPERATURE
            # client_params["max_output_tokens"] = settings.GEMINI_MAX_TOKENS
            # client_params["top_k"] = settings.GEMINI_TOP_K
            # client_params["top_p"] = settings.GEMINI_TOP_P

            _llm_client = ChatGoogleGenerativeAI(**client_params)
            logger.info("Google Gemini LLM client initialized successfully.")

        except ValueError as e: # Should not happen for API key due to Pydantic validation
            # API key missing error already logged, re-raise
            raise
        except Exception as e:
            # Catch any other unexpected errors during initialization
            logger.critical(f"Failed to initialize LLM client: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize LLM client: {e}") from e

    return _llm_client

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=settings.LOGGING_LEVEL, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    logger.info("--- Running llm_client.py directly for testing (Google Gemini with Pydantic settings) ---")
    logger.info(f"Ensure .env file exists and is loaded by Pydantic settings, with 'GOOGLE_API_KEY' set.")
    logger.info(f"Using Gemini Model: {settings.GEMINI_CHAT_MODEL_NAME}")

    try:
        client = get_llm_client()
        logger.info("Test successful: LLM Client object obtained.")

        logger.info("Calling get_llm_client() again...")
        client_again = get_llm_client()
        if client is client_again:
             logger.info("Successfully retrieved the same client instance (singleton pattern working).")
        else:
             logger.warning("A new client instance was created on the second call (singleton pattern failed).")

    except (ValueError, RuntimeError) as e:
         logger.error(f"Test failed during client initialization: {e}")
    except Exception as e:
         logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)

    logger.info("--- LLM Client Test Complete ---")