# -*- coding: utf-8 -*-
"""Extracts text content from preprocessed page images using a multimodal LLM.

Includes specific error handling and retry logic using tenacity.
"""

import base64
import io
import sys
import logging
from typing import Optional, Any, List # <<< CORRECTION: Added List import
from PIL import Image
# Import tenacity for retry logic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
# Import the function to get the initialized LLM client
from .llm_client import get_llm_client
# Import necessary Langchain components
from langchain_core.messages import HumanMessage, BaseMessage # Added BaseMessage
# Import specific OpenAI exceptions for handling
try:
    from openai import (
        APIError, APIConnectionError, APITimeoutError, AuthenticationError,
        BadRequestError, PermissionDeniedError, RateLimitError
    )
    # Define which errors should trigger a retry
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
    class RateLimitError(Exception): pass
    RETRYABLE_API_ERRORS = (Exception,)
    logging.warning("openai library not found or exceptions changed. Specific API error handling may be limited.")

# Get a logger instance for this module
logger = logging.getLogger(__name__)

def encode_image_to_base64(image: Image.Image, format: str = "WEBP") -> str:
    """Encodes a PIL Image object into a base64 data URI string."""
    logger.debug(f"Encoding image to base64 using format: {format}")
    try:
        buffered = io.BytesIO()
        save_kwargs = {"format": format}
        if format.upper() == "WEBP": save_kwargs["lossless"] = True
        image.save(buffered, **save_kwargs)
        img_bytes = buffered.getvalue()
        base64_str = base64.b64encode(img_bytes).decode('utf-8')
        mime_type = f"image/{format.lower()}"
        return f"data:{mime_type};base64,{base64_str}"
    except Exception as e:
        logger.error(f"Error encoding image to base64: {e}", exc_info=True)
        raise

# --- Helper function with retry logic for the LLM call ---
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(RETRYABLE_API_ERRORS),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _invoke_llm_with_retry(llm_client: Any, messages: List[BaseMessage]) -> Any: # List is used here
    """
    Internal helper to invoke the LLM client with retry logic for specific errors.
    """
    logger.debug("Invoking LLM...")
    return llm_client.invoke(messages)


def extract_text_from_image(image: Image.Image) -> Optional[str]:
    """Extracts text content from an image using a multimodal LLM with retry logic.

    Args:
        image: The preprocessed PIL Image object of a document page.

    Returns:
        The extracted text as a single string if successful, otherwise None.

    Raises:
        TypeError: If the input `image` is not a PIL Image object.
        RuntimeError: If the LLM client cannot be initialized or critical API errors occur.
    """
    if not isinstance(image, Image.Image):
        msg = "Invalid input type for text extraction: Expected PIL Image."
        logger.error(msg); raise TypeError(msg)

    logger.info(f"Starting text extraction for image (mode: {image.mode}, size: {image.size})...")

    try:
        llm = get_llm_client()
        logger.debug("Encoding image to base64 data URI for LLM...")
        base64_data_uri = encode_image_to_base64(image, format="WEBP")
        logger.debug(f"Image successfully encoded.")

        prompt_text = (
            "This is an image of a potentially handwritten medical document page, likely in Portuguese. "
            "The image may have been preprocessed to enhance text visibility. "
            "Extract all the text content from this image. "
            "Preserve the original structure (paragraphs, line breaks) as accurately as possible. "
            "Output only the extracted text, without any additional commentary or formatting."
        )
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": {"url": base64_data_uri}},
            ]
        )

        logger.info("Sending image and prompt to LLM for text extraction (with retries)...")
        response = _invoke_llm_with_retry(llm, [message]) # Call helper

        if hasattr(response, 'content') and isinstance(response.content, str):
            extracted_text = response.content
            logger.info("LLM text extraction successful (possibly after retries).")
            logger.debug(f"Extracted Text Snippet: {extracted_text[:100]}...")
            return extracted_text
        else:
            logger.error(f"Unexpected LLM response format or type after successful call. Response: {response}")
            return None

    except AuthenticationError as e:
        logger.critical(f"OpenAI API Authentication Error: Invalid API Key? {e}", exc_info=True)
        raise RuntimeError("API Authentication Failed") from e
    except PermissionDeniedError as e:
         logger.critical(f"OpenAI API Permission Error: Key lacks permission? {e}", exc_info=True)
         raise RuntimeError("API Permission Denied") from e
    except BadRequestError as e:
         logger.error(f"OpenAI API Bad Request Error: {e}", exc_info=True)
         return None
    except Exception as e: # Catch errors from encoding, client init, or final retry failure
        logger.error(f"Failed to extract text after retries or due to other error: {e}", exc_info=True)
        return None

# Example usage block (remains the same)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running text_extractor.py directly for testing ---")
    test_image_dir = "temp_test_loader"; test_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png")
    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None
        try:
            input_image = Image.open(test_image_path); input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")
            logger.info("Attempting text extraction (requires configured .env)...")
            extracted_text = extract_text_from_image(input_image)
            if extracted_text is not None: logger.info("--- Extracted Text ---"); print(extracted_text); logger.info("----------------------")
            else: logger.warning("Text extraction failed or returned None.")
        except FileNotFoundError: logger.error(f"Test image not found at {test_image_path}")
        except (TypeError, RuntimeError) as e: logger.error(f"Test failed due to configuration or input error: {e}")
        except Exception as e: logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()
    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
    logger.info("--- Text Extractor Test Complete ---")