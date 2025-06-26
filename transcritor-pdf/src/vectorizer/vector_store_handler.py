# -*- coding: utf-8 -*-
"""Handles interaction with the vector store (PostgreSQL + pgvector) using SQLAlchemy.
Simplified internal error handling. Includes logging.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings # For EMBEDDING_DIMENSIONS and potentially other configs
from src.core.database import get_db_contextmanager, initialize_database, close_database_connection # For testing
from src.vectorizer import embedding_generator

logger = logging.getLogger(__name__)

async def add_chunks_to_vector_store(db: AsyncSession, document_id: int, rag_chunks: List[Dict[str, Any]]):
    """Adds or updates text chunks, metadata, and embeddings in PostgreSQL using SQLAlchemy.

    Args:
        db: The SQLAlchemy AsyncSession to use for database operations.
        document_id: The ID of the document these chunks belong to.
        rag_chunks: List of chunk dictionaries with required keys.
    Raises:
        ConnectionError: If DB operation fails (wrapped from SQLAlchemyError).
        ValueError: If chunk data formatting fails (logged as warning, chunk skipped).
        Exception: For other unexpected errors.
    """
    if not rag_chunks:
        logger.warning("Vector Store Handler: No chunks provided.")
        return

    logger.info(f"--- Adding {len(rag_chunks)} Chunks to Vector Store (SQLAlchemy) for document_id {document_id} ---")
    inserted_count = 0
    skipped_count = 0

    table_name = "document_chunks"
    # pgvector expects embeddings as a string representation of a list, e.g., '[0.1, 0.2, ...]'
    # or a Python list that the driver (psycopg with asyncpg) can adapt.
    # For pgvector, passing the Python list directly is usually correct.
    insert_query_str = f"""
        INSERT INTO {table_name} (document_id, logical_chunk_id, chunk_text, embedding, chunk_order)
        VALUES (:document_id, :logical_chunk_id, :chunk_text, :embedding, :chunk_order)
        ON CONFLICT (logical_chunk_id) DO UPDATE SET
        document_id=EXCLUDED.document_id, chunk_text=EXCLUDED.chunk_text,
        embedding=EXCLUDED.embedding, chunk_order=EXCLUDED.chunk_order;
    """
    insert_query = text(insert_query_str)

    logger.info(f"Preparing to insert/update data into table '{table_name}'...")

    try:
        for chunk in rag_chunks:
            logical_chunk_id = chunk.get("chunk_id")
            text_content = chunk.get("text_content")
            embedding_list = chunk.get("embedding") # This should be a list of floats/ints
            metadata = chunk.get("metadata", {})
            chunk_order = metadata.get("original_chunk_index_on_page", 0)

            if not logical_chunk_id or not text_content or embedding_list is None:
                logger.warning(f"Skipping chunk ID '{logical_chunk_id}' due to missing essential data (ID, text, or embedding).")
                skipped_count += 1
                continue

            if not (isinstance(embedding_list, list) and all(isinstance(x, (int, float)) for x in embedding_list)):
                logger.warning(f"Skipping chunk ID '{logical_chunk_id}' due to invalid embedding format. Expected list of numbers.")
                skipped_count += 1
                continue

            # For pgvector, the Python list of floats should be directly usable.
            # The driver handles the conversion to the appropriate string format if needed by pgvector.
            # No need for json.dumps(embedding_list) if the column type is VECTOR.

            params = {
                "document_id": document_id,
                "logical_chunk_id": logical_chunk_id,
                "chunk_text": text_content,
                "embedding": embedding_list, # Pass the list directly
                "chunk_order": chunk_order,
            }

            logger.debug(f"Executing upsert for logical_chunk_id: {logical_chunk_id}")
            await db.execute(insert_query, params)
            inserted_count += 1

        # Commit is handled by the context manager that provides the 'db' session,
        # or needs to be called explicitly if the session is managed manually.
        # Assuming session is managed by a context manager from get_db_contextmanager or get_db_session.
        logger.info(f"Successfully prepared {inserted_count} chunks for document_id {document_id}. Commit will occur at end of session scope.")

        if skipped_count > 0:
            logger.warning(f"Skipped {skipped_count} chunks due to validation/formatting issues for document_id {document_id}.")

    except SQLAlchemyError as db_error:
        logger.critical(f"Database operation error while adding chunks for document_id {document_id}: {db_error}", exc_info=True)
        # Rollback is typically handled by the session context manager on error.
        raise ConnectionError(f"Database operation failed for document_id {document_id}: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred while adding chunks for document_id {document_id}: {e}", exc_info=True)
        raise


async def search_similar_chunks(
    db: AsyncSession,
    query_text: str,
    top_k: int = 5,
    document_filename: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches for text chunks most similar to the query_text using vector embeddings and SQLAlchemy.

    Args:
        db: The SQLAlchemy AsyncSession to use for database operations.
        query_text: The text to search for.
        top_k: The number of top similar chunks to retrieve.
        document_filename: Optional. If provided, filters chunks by this filename.

    Returns:
        A list of dictionaries, each representing a similar chunk with its
        ID, text content, metadata, and similarity score. Returns an empty
        list if an error occurs or no chunks are found.
    """
    logger.info(f"Starting similarity search (SQLAlchemy) for query: '{query_text[:50]}...', top_k={top_k}, filename_filter='{document_filename}'")

    if top_k <= 0:
        logger.warning("top_k must be positive. Returning empty list.")
        return []

    try:
        embedding_client = embedding_generator.get_embedding_client() # Assumes this is configured
        query_embedding = embedding_client.embed_query(query_text) # This is a list of floats
        logger.info(f"Generated embedding for query (Dimension: {len(query_embedding)})")
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}", exc_info=True)
        return []

    results: List[Dict[str, Any]] = []
    params: Dict[str, Any] = {"query_embedding": query_embedding, "top_k": top_k}

    # Base query using cosine distance operator <=> from pgvector
    # Ensure the 'documents' and 'document_chunks' tables and columns are correct.
    # The embedding column in document_chunks is assumed to be of type VECTOR.

    if document_filename:
        sql_query_str = f"""
            SELECT dc.logical_chunk_id, dc.chunk_text, dc.chunk_order, dc.embedding <=> :query_embedding AS distance
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE d.file_name = :document_filename
            ORDER BY distance ASC
            LIMIT :top_k;
        """
        params["document_filename"] = document_filename
    else:
        sql_query_str = f"""
            SELECT logical_chunk_id, chunk_text, chunk_order, embedding <=> :query_embedding AS distance
            FROM document_chunks
            ORDER BY distance ASC
            LIMIT :top_k;
        """

    sql_query = text(sql_query_str)

    # Log query without actual embedding for security/brevity
    log_params_str = {k: (v if not isinstance(v, list) else f"<embedding_vector_len_{len(v)}>") for k, v in params.items()}
    logger.info(f"Executing search query: {sql_query_str.strip()} with params: {log_params_str}")

    try:
        result_proxy = await db.execute(sql_query, params)
        rows = result_proxy.mappings().all() # Get results as list of dict-like RowMappings

        for row in rows:
            similarity_score = 1 - row['distance'] # Cosine distance to similarity
            results.append({
                "chunk_id": row['logical_chunk_id'],
                "text_content": row['chunk_text'],
                "chunk_order": row['chunk_order'],
                "similarity_score": similarity_score
            })

        logger.info(f"Found {len(results)} similar chunks.")
        return results

    except SQLAlchemyError as db_error:
        logger.critical(f"Database query error during search: {db_error}", exc_info=True)
        raise ConnectionError(f"Database query failed during search: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred during search: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    async def run_test():
        logger.info("--- Running vector_store_handler.py (SQLAlchemy) directly for testing ---")
        logger.warning("This test block WILL attempt to connect to and write to the database using settings from .env.")

        # Initialize database using the new core functions
        # Make sure transcritor-pdf/.env is configured correctly
        initialize_database() # Synchronous call

        embedding_dim = settings.EMBEDDING_DIMENSIONS # Get from settings
        sample_document_id = 999  # Example document_id for testing
        sample_rag_chunks_with_embeddings = [
            {"chunk_id": "sqlalchemy_test_001", "text_content": "SQLAlchemy test chunk 1.",
             "metadata": {"original_chunk_index_on_page": 1}, "embedding": [0.55] * embedding_dim},
            {"chunk_id": "sqlalchemy_test_002", "text_content": "SQLAlchemy test chunk 2.",
             "metadata": {"original_chunk_index_on_page": 2}, "embedding": [0.65] * embedding_dim}
        ]
        logger.info(f"Sample Chunks to Add/Update: {len(sample_rag_chunks_with_embeddings)} for document_id {sample_document_id}")

        confirm = input("\nProceed with test database insertion/update? (yes/no): ")
        if confirm.lower() == 'yes':
            logger.info("Proceeding with test database operation...")
            try:
                async with get_db_contextmanager() as db_session: # Use the context manager
                    await add_chunks_to_vector_store(db_session, sample_document_id, sample_rag_chunks_with_embeddings)
                    await db_session.commit() # Explicit commit after operations within the session
                    logger.info("Test add_chunks_to_vector_store completed and committed.")

                    # Test search
                    logger.info("Testing search_similar_chunks...")
                    search_results = await search_similar_chunks(db_session, "test chunk", top_k=2)
                    logger.info(f"Search results: {search_results}")

            except ConnectionError as e:
                logger.error(f"Test failed due to connection error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
            else:
                logger.info("Test database operation process completed (check database).")
        else:
            logger.info("Test database operation cancelled by user.")

        await close_database_connection() # Clean up connections
        logger.info("--- Vector Store Handler Test Complete (SQLAlchemy) ---")

    asyncio.run(run_test())