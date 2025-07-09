# -*- coding: utf-8 -*-
"""Parses structured information (entities) from raw extracted text using an LLM.
Defines the chain within the parsing function. Includes logging and specific
OpenAI API error handling with tenacity retries.
"""

import json
import sys
import logging
from typing import Dict, Any, Optional, List # Added List
# Import tenacity for retry logic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
# Import LLM client getter
from .llm_client import get_llm_client
# Import Langchain components
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
# Import Langchain and OpenAI exceptions
from langchain_core.exceptions import OutputParserException
try:
    from openai import (
        APIError, APIConnectionError, APITimeoutError, AuthenticationError,
        BadRequestError, PermissionDeniedError, RateLimitError
    )
    # Define which errors should trigger a retry for the LLM call itself
    RETRYABLE_API_ERRORS = (
        RateLimitError, APITimeoutError, APIError, APIConnectionError
    )
    OPENAI_ERRORS_AVAILABLE = True
except ImportError:
    OPENAI_ERRORS_AVAILABLE = False
    class APIError(Exception): pass
    class APIConnectionError(APIError): pass
    class APITimeoutError(APIError): pass
    class AuthenticationError(APIError): pass
    class BadRequestError(APIError): pass
    class PermissionDeniedError(APIError): pass
    class RateLimitError(APIError): pass
    # Retry on generic Exception if specific ones aren't available
    RETRYABLE_API_ERRORS = (Exception,)
    logging.warning("openai library not found or exceptions changed. Specific API error handling may be limited.")

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Output Parser ---
parser = JsonOutputParser()

# --- Prompt Template String (Defined line by line) ---
prompt_lines = [
    "Analyze the following text extracted from a medical document page.",
    "Identify and extract the following information:",
    "- client_name: The patient's full name (null if none).",
    "- document_date: The document's date (YYYY-MM-DD if possible, else as written; null if none).",
    "- signature_found: Boolean (true/false) indicating if a professional signature is present/implied.",
    "- relevant_illness_mentions: List of strings with key medical conditions/symptoms (empty list [] if none).",
    "",
    "Return ONLY a valid JSON object with these exact keys. No explanations.",
    "",
    "Extracted Text:",
    "```text",
    "{extracted_text}",
    "```",
    "",
    "JSON Output:",
]
prompt_template_str = "\n".join(prompt_lines)

# Create the prompt template object at module level
prompt = PromptTemplate(
    template=prompt_template_str,
    input_variables=["extracted_text"],
)

# --- Helper function with retry logic for the chain invocation ---
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(RETRYABLE_API_ERRORS), # Retry only on API errors, not parsing errors
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _invoke_chain_with_retry(chain: Any, input_data: Dict[str, Any]) -> Any:
    """
    Internal helper to invoke the LCEL chain with retry logic for specific API errors.
    Note: This assumes the error originates from the LLM step within the chain.
    OutputParserException will not be retried by this decorator.

    Args:
        chain: The initialized Langchain LCEL chain (prompt | llm | parser).
        input_data: The dictionary input for the chain's invoke method.

    Returns:
        The result from the chain's invoke method.

    Raises:
        Propagates exceptions defined in RETRYABLE_API_ERRORS if retries fail.
        Propagates other exceptions (like AuthenticationError, OutputParserException) immediately.
    """
    logger.debug("Invoking LCEL chain...")
    # Exceptions like AuthenticationError, PermissionDeniedError, BadRequestError,
    # and crucially OutputParserException will be raised immediately by invoke
    # and NOT retried by this decorator. Only RETRYABLE_API_ERRORS trigger retries.
    return chain.invoke(input_data)


# --- Parsing Function ---
def parse_extracted_info(raw_text: str) -> Optional[Dict[str, Any]]:
    """Parses structured information from raw text using an LLM call with retry logic.

    Args:
        raw_text: The raw text content extracted from a document page.

    Returns:
        A dictionary containing the parsed information if successful, otherwise None.

    Raises:
        RuntimeError: If the LLM client cannot be initialized or critical API errors occur.
    """
    if not raw_text or not isinstance(raw_text, str):
        logger.warning("Info Parser: Invalid or empty input text provided. Skipping parsing.")
        return None

    logger.info("Starting structured information parsing...")
    parsed_result = None
    try:
        llm = get_llm_client() # Can raise RuntimeError
        chain = prompt | llm | parser
        logger.debug("LCEL chain (prompt | llm | parser) constructed.")

        logger.info("Invoking information parsing chain (with retries)...")
        # --- Call the helper function which includes the @retry decorator ---
        parsed_result = _invoke_chain_with_retry(chain, {"extracted_text": raw_text})
        # --- End Call ---

        logger.info("Chain invocation successful (possibly after retries).")

        # Basic validation
        if isinstance(parsed_result, dict):
            logger.debug(f"Parsed Info Dictionary: {parsed_result}")
            return parsed_result
        else:
            # Should ideally not happen if JsonOutputParser worked, but check anyway
            logger.error(f"Chain returned unexpected type after invoke. Expected dict, got: {type(parsed_result)}. Result: {parsed_result}")
            return None

    # --- Error Handling for Non-Retryable or Final Errors ---
    except OutputParserException as ope:
        # Error parsing the LLM's response (JSON invalid, etc.) - NOT retried
        logger.error(f"Failed to parse LLM response as JSON: {ope}", exc_info=True)
        return None
    except AuthenticationError as e: # Non-retryable auth errors
        logger.critical(f"OpenAI API Authentication Error during info parsing: {e}", exc_info=True)
        raise RuntimeError("API Authentication Failed during info parsing") from e
    except PermissionDeniedError as e: # Non-retryable permission errors
         logger.critical(f"OpenAI API Permission Error during info parsing: {e}", exc_info=True)
         raise RuntimeError("API Permission Denied during info parsing") from e
    except BadRequestError as e: # Non-retryable bad request errors
         logger.error(f"OpenAI API Bad Request Error during info parsing: {e}", exc_info=True)
         return None # Input/prompt likely invalid
    except RuntimeError as rte: # Catch client initialization errors
         logger.critical(f"LLM client runtime error preventing info parsing: {rte}", exc_info=True)
         raise # Re-raise critical runtime errors
    except Exception as e:
        # This will catch the final RETRYABLE_API_ERRORS if all retries failed,
        # or any other unexpected error during chain setup/invocation.
        logger.error(f"Failed to parse info after retries or due to other error: {e}", exc_info=True)
        return None

# No __main__ block needed