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
# Import the specific Langchain embedding class
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    logging.critical("langchain-openai library not found. Please install it: pip install langchain-openai")
    sys.exit(1)

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Constants ---
# Specifies the OpenAI embedding model to use.
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
# Optional: Specify output dimensions if supported by the model and desired.
# Set to None to use the model's default dimension (1536 for text-embedding-3-small).
# Smaller dimensions (e.g., 256, 512, 1024) can save storage and potentially speed up
# similarity search, possibly at the cost of some semantic nuance.
EMBEDDING_DIMENSIONS = None # Use default

# --- Embedding Model Initialization (Singleton Pattern) ---
# Stores the initialized client instance.
_embedding_client: Optional[OpenAIEmbeddings] = None

def get_embedding_client() -> OpenAIEmbeddings:
    """Initializes and returns a singleton Langchain Embedding client instance.

    Configured for the OpenAI embedding model specified by `EMBEDDING_MODEL_NAME`
    and `EMBEDDING_DIMENSIONS`. It relies on the `OPENAI_API_KEY` environment
    variable being set (typically loaded from `.env` by `llm_client` or another
    part of the application).

    On the first call, it initializes the `OpenAIEmbeddings` client. Subsequent
    calls return the cached instance.

    Returns:
        An initialized `langchain_openai.OpenAIEmbeddings` client instance.

    Raises:
        RuntimeError: If the `langchain-openai` library failed to import or if
                      any other error occurs during client initialization (e.g.,
                      authentication issues due to missing/invalid API key).
                      Logs critical errors before raising.
    """
    global _embedding_client
    if _embedding_client is None:
        logger.info("Initializing Embedding client for the first time...")
        if OpenAIEmbeddings is None:
             # Should have been caught at import, but defensive check
             logger.critical("OpenAIEmbeddings class not available (import failed).")
             raise RuntimeError("langchain-openai library is required but failed to import.")

        try:
            # Note: OpenAIEmbeddings reads OPENAI_API_KEY from env automatically.
            logger.info("Configuring OpenAIEmbeddings:")
            logger.info(f"  Model: {EMBEDDING_MODEL_NAME}")
            logger.info(f"  Dimensions: {EMBEDDING_DIMENSIONS if EMBEDDING_DIMENSIONS else 'Default'}")

            _embedding_client = OpenAIEmbeddings(
                model=EMBEDDING_MODEL_NAME,
                dimensions=EMBEDDING_DIMENSIONS if EMBEDDING_DIMENSIONS else None,
                # Other potential parameters:
                # chunk_size: Max number of texts to embed in one batch (defaults to 16 for ada-002)
                # request_timeout: Timeout for API calls
                # max_retries: Number of retries on failure
            )
            logger.info("Embedding client initialized successfully.")

        except Exception as e:
            # Catch potential initialization errors (e.g., invalid key)
            logger.critical(f"Failed to initialize OpenAI Embedding client: {e}", exc_info=True)
            if "authentication" in str(e).lower():
                 logger.error("Hint: Ensure OPENAI_API_KEY is set correctly in your .env file.")
            # Re-raise as RuntimeError to signal critical failure
            raise RuntimeError(f"Failed to initialize OpenAI Embedding client: {e}") from e

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
            if text and isinstance(text, str):
                texts_to_embed.append(text)
                chunk_indices_to_embed.append(i)
            else:
                 # Ensure 'embedding' key exists even for skipped chunks
                 chunk['embedding'] = None

        if not texts_to_embed:
             logger.warning("No valid text content found in any chunks to generate embeddings.")
             return rag_chunks # Return original list with embeddings set to None

        logger.info(f"Sending {len(texts_to_embed)} non-empty text chunks to embedding API ({EMBEDDING_MODEL_NAME})...")

        # Generate embeddings - Langchain client handles batching
        # This call might raise exceptions on API errors (e.g., network, auth, rate limits)
        embeddings: List[List[float]] = embedding_client.embed_documents(texts_to_embed)

        logger.info(f"Successfully received {len(embeddings)} embeddings from API.")
        if embeddings:
             logger.debug(f"Example embedding dimension: {len(embeddings[0])}")

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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running embedding_generator.py directly for testing ---")
    logger.info(f"Requires .env file with OPENAI_API_KEY for model '{EMBEDDING_MODEL_NAME}'")

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