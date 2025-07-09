# -*- coding: utf-8 -*-
"""Configures and provides the Large Language Model (LLM) client instance.

This module is responsible for:
1. Loading API credentials (API key, base URL, model name) securely from
   environment variables defined in a `.env` file.
2. Initializing a Langchain chat model client (specifically `ChatOpenAI` for
   compatibility with OpenAI API standards, often used by providers like
   OpenRouter) with the loaded configuration.
3. Providing a singleton instance of the initialized client via the
   `get_llm_client` function to ensure configuration is loaded only once.
Includes logging for operations and potential configuration errors.
"""

import os
import sys
import logging
from dotenv import load_dotenv, find_dotenv
from typing import Optional

# Import the specific Langchain chat model class
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Log critical error if dependency is missing
    logging.critical("langchain-openai library not found. Please install it: pip install langchain-openai")
    sys.exit(1)

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Constants for Environment Variables ---
OPENAI_API_KEY_VAR = "OPENAI_API_KEY"
OPENAI_BASE_URL_VAR = "OPENAI_BASE_URL"
MODEL_NAME_VAR = "OPENAI_MODEL_NAME"

# --- Sensible Defaults for OpenAI ---
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL_NAME = "gpt-3.5-turbo"

# --- LLM Client Initialization Logic ---
def load_api_config() -> tuple[str, str, str]:
    """Loads API configuration directly from environment variables.

    Returns:
        A tuple containing: api_key, base_url, model_name.

    Raises:
        ValueError: If the mandatory OPENAI_API_KEY is not found.
    """
    api_key = os.getenv(OPENAI_API_KEY_VAR)
    if not api_key:
        error_msg = f"Required environment variable '{OPENAI_API_KEY_VAR}' not found."
        logger.critical(error_msg)
        raise ValueError(error_msg)

    base_url = os.getenv(OPENAI_BASE_URL_VAR, DEFAULT_OPENAI_BASE_URL)
    model_name = os.getenv(MODEL_NAME_VAR, DEFAULT_MODEL_NAME)

    logger.info(f"API Config Loaded: Base URL='{base_url}', Model Name='{model_name}'")
    return api_key, base_url, model_name

# --- Singleton Client Instance ---
# Stores the initialized client to avoid re-initialization on subsequent calls.
_llm_client: Optional[ChatOpenAI] = None

def get_llm_client() -> ChatOpenAI:
    """Initializes and returns a singleton Langchain Chat Model client instance.

    On the first call, it loads the API configuration using `load_api_config`
    and initializes a `ChatOpenAI` client configured for the specified endpoint
    (e.g., OpenRouter). Subsequent calls return the same cached client instance.

    Returns:
        An initialized `langchain_openai.ChatOpenAI` client instance.

    Raises:
        ValueError: Propagated from `load_api_config` if the API key is missing.
        RuntimeError: If any other error occurs during client initialization
                      (e.g., library issues, network problems during potential
                       initial checks by the library). Logs a critical error
                       before raising.
    """
    global _llm_client
    # Use a lock if thread safety becomes a concern, but likely not needed for this CLI tool
    if _llm_client is None:
        logger.info("Initializing LLM client for the first time...")
        try:
            # Load configuration from environment variables
            api_key, base_url, model_name = load_api_config()

            logger.info("Configuring Langchain ChatOpenAI client:")
            logger.info(f"  Model: {model_name}")
            logger.info(f"  Base URL: {base_url}")
            # Intentionally DO NOT log the API key for security

            # Initialize the ChatOpenAI client
            _llm_client = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                openai_api_base=base_url,
                # --- Optional Parameters (Examples) ---
                # Adjust temperature for creativity vs predictability (0.0 to 1.0+)
                # temperature=0.5,
                # Set maximum tokens for the response to control length and cost
                # max_tokens=2048,
                # Set timeout for API calls (in seconds)
                # request_timeout=60,
                # Configure automatic retries on transient errors
                # max_retries=2,
            )
            logger.info("LLM client initialized successfully.")

        except ValueError as e:
            # API key missing error already logged, re-raise
            raise
        except Exception as e:
            # Catch any other unexpected errors during initialization
            logger.critical(f"Failed to initialize LLM client: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize LLM client: {e}") from e

    # Return the initialized (or cached) client instance
    return _llm_client

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running llm_client.py directly for testing ---")
    logger.info(f"Ensure .env file exists with '{OPENAI_API_KEY_VAR}' set.")
    logger.info(f"Optional vars: '{OPENAI_BASE_URL_VAR}', '{MODEL_NAME_VAR}'/'{ALT_MODEL_NAME_VAR}'")

    try:
        # First call initializes the client
        client = get_llm_client()
        logger.info("Test successful: LLM Client object obtained.")
        # logger.debug(f"Client details: {client}") # Can be very verbose

        # Test getting the client again (should return the same cached instance)
        logger.info("Calling get_llm_client() again...")
        client_again = get_llm_client()
        if client is client_again:
             logger.info("Successfully retrieved the same client instance (singleton pattern working).")
        else:
             logger.warning("A new client instance was created on the second call (singleton pattern failed).")

        # --- Optional: Simple Test API Call ---
        # Uncomment carefully - this will make a real API call and may incur costs.
        # logger.info("Attempting a simple test call to the LLM (requires API key)...")
        # try:
        #     from langchain_core.prompts import ChatPromptTemplate
        #     prompt_test = ChatPromptTemplate.from_messages([("system", "You are helpful."), ("user", "{input}")])
        #     chain_test = prompt_test | client
        #     response_test = chain_test.invoke({"input": "What is OpenRouter in one brief sentence?"})
        #     if hasattr(response_test, 'content'):
        #         logger.info(f"Test call response: {response_test.content}")
        #     else:
        #         logger.info(f"Test call response (raw): {response_test}")
        # except ImportError:
        #      logger.warning("Skipping test call: langchain-core components not found.")
        # except Exception as call_error:
        #      logger.error(f"Error during test call: {call_error}", exc_info=True)

    except (ValueError, RuntimeError) as e:
         # Catch errors specifically from get_llm_client initialization
         logger.error(f"Test failed during client initialization: {e}")
    except Exception as e:
         # Catch any other unexpected errors during the test itself
         logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)

    logger.info("--- LLM Client Test Complete ---")