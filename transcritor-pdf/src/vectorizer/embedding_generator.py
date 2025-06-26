# -*- coding: utf-8 -*-
"""Generates text embeddings using a configured embedding model via API.

This module is responsible for initializing the chosen embedding model client
(currently OpenAI's text-embedding-3-small via `langchain-openai`) and
providing a function to generate vector representations (embeddings) for
a list of text chunks provided by the `formatter` module.
Includes logging for operations and errors.
"""

import sys
import logging
from typing import List, Dict, Any, Optional
# Import the specific Langchain embedding class for Google Gemini
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
except ImportError:
    logging.critical("langchain-google-genai library not found. Please install it: pip install langchain-google-genai")
    sys.exit(1)

from src.core.config import settings # Import Pydantic settings

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Embedding Model Initialization (Singleton Pattern) ---
# Stores the initialized client instance.
_embedding_client: Optional[GoogleGenerativeAIEmbeddings] = None

def get_embedding_client() -> GoogleGenerativeAIEmbeddings:
    """Initializes and returns a singleton Langchain GoogleGenerativeAIEmbeddings client instance.

    Configured using settings from `src.core.config` (GOOGLE_API_KEY, GEMINI_EMBEDDING_MODEL_NAME).

    On the first call, it initializes the `GoogleGenerativeAIEmbeddings` client.
    Subsequent calls return the cached instance.

    Returns:
        An initialized `langchain_google_genai.GoogleGenerativeAIEmbeddings` client instance.

    Raises:
        RuntimeError: If any error occurs during client initialization.
                      Logs critical errors before raising.
    """
    global _embedding_client
    if _embedding_client is None:
        logger.info("Initializing Google Gemini Embedding client for the first time...")
        if GoogleGenerativeAIEmbeddings is None:
             logger.critical("GoogleGenerativeAIEmbeddings class not available (import failed).")
             raise RuntimeError("langchain-google-genai library is required but failed to import.")

        try:
            # GOOGLE_API_KEY is mandatory in settings and Pydantic would have raised error if not set.
            api_key = settings.GOOGLE_API_KEY
            model_name = settings.GEMINI_EMBEDDING_MODEL_NAME
            # EMBEDDING_DIMENSIONS from settings is for DB schema, not directly passed to this client.
            # Gemini embedding models have fixed output dimensions (e.g., 768 for text-embedding-004).

            logger.info("Configuring GoogleGenerativeAIEmbeddings:")
            logger.info(f"  Model: {model_name}")
            # API key is not logged for security.

            _embedding_client = GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=api_key
                # Other potential parameters for Google embeddings if needed:
                # task_type: "RETRIEVAL_DOCUMENT", "SIMILARITY_SEARCH", etc.
                # title: For document retrieval tasks
            )
            logger.info("Google Gemini Embedding client initialized successfully.")

        except Exception as e:
            logger.critical(f"Failed to initialize Google Gemini Embedding client: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize Google Gemini Embedding client: {e}") from e

    return _embedding_client

# --- Embedding Generation Function ---
def generate_embeddings_for_chunks(rag_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generates vector embeddings for the text content of each provided RAG chunk.

    Takes a list of chunk dictionaries (as produced by the `formatter` module),
    extracts the 'text_content' from each valid chunk, calls the configured
    embedding model API (via the Langchain client) to get the vector embeddings,
    and then adds a new 'embedding' key containing the corresponding vector
    (as a list of floats) back into each original chunk dictionary.

    Chunks without valid 'text_content' will have their 'embedding' key set to None.
    If the API call fails entirely, an exception is raised.

    Args:
        rag_chunks: A list of dictionaries, where each dictionary represents a
                    chunk and is expected to have a 'text_content' key (str).

    Returns:
        The input list of dictionaries, modified in-place by adding an
        'embedding' key (List[float] or None) to each dictionary.

    Raises:
        RuntimeError: If the embedding client cannot be initialized.
        Exception: If a non-recoverable error occurs during the embedding API call.
                   Errors are logged before raising.
    """
    if not rag_chunks:
        logger.warning("Embedding Generator: No chunks provided to generate embeddings for.")
        return []

    logger.info(f"--- Generating Embeddings for {len(rag_chunks)} Chunks ---")
    try:
        # Get the initialized embedding client
        embedding_client = get_embedding_client()

        # Prepare list of texts to embed, skipping empty ones
        texts_to_embed: List[str] = []
        chunk_indices_to_embed: List[int] = [] # Keep track of original index
        for i, chunk in enumerate(rag_chunks):
            text = chunk.get("text_content")
            if text and isinstance(text, str) and text.strip(): # Also check if text is not just whitespace
                texts_to_embed.append(text)
                chunk_indices_to_embed.append(i)
            else:
                 # Ensure 'embedding' key exists even for skipped chunks
                 chunk['embedding'] = None
                 if text is not None: # Log if text was present but invalid (e.g. empty string)
                     logger.debug(f"Chunk {chunk.get('chunk_id', 'N/A')} has empty or invalid text_content, skipping embedding.")


        if not texts_to_embed:
             logger.warning("No valid text content found in any chunks to generate embeddings.")
             return rag_chunks # Return original list with embeddings set to None

        logger.info(f"Sending {len(texts_to_embed)} non-empty text chunks to Google Gemini embedding API ({settings.GEMINI_EMBEDDING_MODEL_NAME})...")

        # Generate embeddings - Langchain client handles batching
        # This call might raise exceptions on API errors (e.g., network, auth, rate limits)
        embeddings: List[List[float]] = embedding_client.embed_documents(texts_to_embed)

        logger.info(f"Successfully received {len(embeddings)} embeddings from Gemini API.")
        if embeddings:
             # Verify embedding dimension against settings for consistency, though it's model-defined.
             actual_dim = len(embeddings[0])
             logger.debug(f"Example embedding dimension from Gemini: {actual_dim}")
             if actual_dim != settings.EMBEDDING_DIMENSIONS:
                 logger.warning(
                     f"Mismatch: Gemini model '{settings.GEMINI_EMBEDDING_MODEL_NAME}' produced embeddings of dimension {actual_dim}, "
                     f"but settings.EMBEDDING_DIMENSIONS is {settings.EMBEDDING_DIMENSIONS}. "
                     f"Ensure DB schema matches the model's output ({actual_dim})."
                 )
                 # Forcing settings.EMBEDDING_DIMENSIONS to actual_dim for this run might be an option,
                 # but it's better to fix the config or schema.

        # --- Add embeddings back to the corresponding chunk dictionaries ---
        if len(embeddings) != len(chunk_indices_to_embed):
            # This indicates a mismatch, potentially an API issue or logic error
            logger.error(f"Mismatch between number of texts sent ({len(texts_to_embed)}) "
                         f"and embeddings received ({len(embeddings)}). Cannot reliably assign embeddings.")
            # Mark all potentially affected chunks as failed? Or just log? Logging for now.
            # Set remaining embeddings to None for safety
            for i in chunk_indices_to_embed:
                 rag_chunks[i]['embedding'] = None
            # Consider raising an exception here?
            raise ValueError("Mismatch between requested and received embeddings count.")

        successful_embeddings = 0
        for i, embedding_vector in enumerate(embeddings):
            original_chunk_index = chunk_indices_to_embed[i]
            rag_chunks[original_chunk_index]['embedding'] = embedding_vector
            successful_embeddings += 1

        logger.info(f"Added embeddings to {successful_embeddings} chunks.")
        # Log skipped count based on initial filtering + potential mismatches
        skipped_count = len(rag_chunks) - successful_embeddings
        if skipped_count > 0:
            logger.warning(f"Could not generate/assign embeddings for {skipped_count} chunks (no text or error).")

        return rag_chunks

    except RuntimeError as e:
        # Error from get_embedding_client
        logger.error(f"Failed to get embedding client: {e}", exc_info=True)
        raise # Re-raise client initialization errors
    except Exception as e:
        # Catch errors during the embed_documents call
        logger.error(f"Error during embedding generation API call: {e}", exc_info=True)
        # Mark all embeddings as None if API fails? Or just raise? Raising for now.
        raise # Re-raise API or other processing errors

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    # Uses LOGGING_LEVEL from Pydantic settings now
    logging.basicConfig(level=settings.LOGGING_LEVEL, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running embedding_generator.py directly for testing (Google Gemini) ---")
    logger.info(f"Requires .env file with GOOGLE_API_KEY for model '{settings.GEMINI_EMBEDDING_MODEL_NAME}'")
    logger.info(f"Expected embedding dimension: {settings.EMBEDDING_DIMENSIONS}")

    # Sample RAG chunks (output from formatter.py)
    sample_chunks = [
        {"chunk_id": "doc1_p1_c1", "text_content": "This is the first chunk.", "metadata": {}},
        {"chunk_id": "doc1_p1_c2", "text_content": "Este é o segundo pedaço.", "metadata": {}},
        {"chunk_id": "doc1_p2_c3", "text_content": "", "metadata": {}}, # Empty
        {"chunk_id": "doc1_p2_c4", "text_content": "Final chunk.", "metadata": {}}
    ]
    logger.info(f"Input Chunks: {len(sample_chunks)}")

    try:
        # Attempt to generate embeddings (modifies the list in-place)
        logger.info("Attempting to generate embeddings (requires valid API key)...")
        chunks_with_embeddings = generate_embeddings_for_chunks(sample_chunks)

        logger.info("--- Results ---")
        embedding_count = 0
        for i, chunk in enumerate(chunks_with_embeddings):
            embedding = chunk.get('embedding')
            status = "Yes" if isinstance(embedding, list) else "No"
            dim_info = f"(Dim: {len(embedding)})" if isinstance(embedding, list) else ""
            logger.info(f"Chunk {i+1} (ID: {chunk.get('chunk_id', 'N/A')}): Embedding Generated: {status} {dim_info}")
            if status == "Yes": embedding_count += 1
        logger.info(f"Total embeddings generated: {embedding_count}")

    except RuntimeError as e:
         # Catch initialization errors
         logger.error(f"Testing failed due to runtime error: {e}")
    except Exception as e:
         # Catch API call or other errors
         logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)

    logger.info("--- Embedding Generator Test Complete ---")