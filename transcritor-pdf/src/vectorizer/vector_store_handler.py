# -*- coding: utf-8 -*-
"""Handles interaction with the vector store (PostgreSQL + pgvector) using asyncpg.
Simplified internal error handling. Includes logging.
"""

import os
import sys
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
import json # Ensure json is imported
try:
    import asyncpg
except ImportError:
    logging.critical("asyncpg library not found. Please install it: pip install asyncpg")
    sys.exit(1)
from dotenv import load_dotenv, find_dotenv

from src.vectorizer import embedding_generator # Added for search_similar_chunks

logger = logging.getLogger(__name__)

def load_db_config() -> Dict[str, Optional[str]]:
    """Loads PostgreSQL connection parameters from environment variables."""
    env_path = find_dotenv()
    if env_path: logger.info(f"Loading database config from: {env_path}"); load_dotenv(dotenv_path=env_path, override=True)
    else: logger.warning(".env file not found for database config.")
    config = {
        "host": os.getenv("DB_HOST", "localhost"), "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME"), "user": os.getenv("DB_USER"), "password": os.getenv("DB_PASSWORD"),
    }
    if not config["database"]: logger.warning("DB_NAME not found in environment variables.")
    if not config["user"]: logger.warning("DB_USER not found in environment variables.")
    if not config["password"]: logger.warning("DB_PASSWORD not found in environment variables.")
    logger.info(f"DB Config Loaded: Host={config['host']}, Port={config['port']}, DB={config['database']}, User={config['user']}")
    return config

async def add_chunks_to_vector_store(document_id: int, rag_chunks: List[Dict[str, Any]]):
    """Adds or updates text chunks, metadata, and embeddings in PostgreSQL using asyncpg.

    Connects asynchronously, starts a transaction, and attempts to upsert each
    valid chunk. If any upsert fails due to a database error, the entire
    transaction is rolled back and ConnectionError is raised.

    Args:
        rag_chunks: List of chunk dictionaries with required keys.
    Raises:
        ConnectionError: If credentials missing, connection fails, or DB operation fails.
        ValueError: If chunk data formatting fails (logged as warning, chunk skipped).
        Exception: For other unexpected errors.
    """
    if not rag_chunks: logger.warning("Vector Store Handler: No chunks provided."); return

    logger.info(f"--- Adding {len(rag_chunks)} Chunks to Vector Store (asyncpg) ---")
    db_config = load_db_config()
    conn: Optional[asyncpg.Connection] = None
    inserted_count = 0
    skipped_count = 0

    if not all([db_config["database"], db_config["user"], db_config["password"]]):
         error_msg = "Database connection details missing in .env (DB_NAME, DB_USER, DB_PASSWORD)."
         logger.critical(error_msg); raise ConnectionError(error_msg)

    try:
        logger.info(f"Connecting to PostgreSQL database '{db_config['database']}' on {db_config['host']}...")
        conn = await asyncpg.connect(**db_config)
        logger.info("Database connection successful (asyncpg).")

        table_name = "document_chunks" # Target the correct table for chunks
        # chunk_id_col, text_col, metadata_col are implicitly correct. vector_col changed.
        # For simplicity, direct usage in query string is preferred over maintaining these variables if fixed.

        insert_query = f"""
            INSERT INTO {table_name} (document_id, logical_chunk_id, chunk_text, embedding, chunk_order)
            VALUES ($1, $2, $3, $4, $5) ON CONFLICT (logical_chunk_id) DO UPDATE SET
            document_id=EXCLUDED.document_id, chunk_text=EXCLUDED.chunk_text, embedding=EXCLUDED.embedding, chunk_order=EXCLUDED.chunk_order;
        """
        logger.info(f"Preparing to insert/update data into table '{table_name}'...")

        # --- Start Transaction ---
        async with conn.transaction():
            logger.debug("Transaction started.")
            for chunk in rag_chunks:
                logical_chunk_id = chunk.get("chunk_id") # This is the UUID from processing.py
                text_content = chunk.get("text_content")
                embedding = chunk.get("embedding")
                metadata = chunk.get("metadata", {})
                chunk_order = metadata.get("original_chunk_index_on_page", 0) # Default to 0 if not present

                if not logical_chunk_id or not text_content or embedding is None:
                    logger.warning(f"Skipping chunk ID '{logical_chunk_id}' due to missing essential data (ID, text, or embedding)."); skipped_count += 1; continue

                try:
                    if not (isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding)):
                        # If embedding is not a list of numbers, raise error.
                        raise ValueError("Invalid embedding format, expected list of numbers for VECTOR column")
                    # Convert the list to its JSON string representation for asyncpg
                    embedding_to_insert = json.dumps(embedding)
                except Exception as fmt_e:
                    logger.warning(f"Skipping chunk ID '{logical_chunk_id}' due to data formatting error for embedding: {fmt_e}", exc_info=True)
                    skipped_count += 1; continue

                # --- Execute Query (Inner try removed) ---
                # Let asyncpg.PostgresError propagate to the outer handler if execute fails
                logger.debug(f"Executing upsert for logical_chunk_id: {logical_chunk_id}")
                await conn.execute(insert_query, document_id, logical_chunk_id, text_content, embedding_to_insert, chunk_order)
                inserted_count += 1
            # Transaction commits automatically if loop finishes without error
            logger.info(f"Transaction commit successful. Added/Updated {inserted_count} chunks for document_id {document_id}.")

        if skipped_count > 0: logger.warning(f"Skipped {skipped_count} chunks due to validation/formatting.")

    except (asyncpg.PostgresError, OSError) as db_error:
        # Catch connection errors OR database errors propagated from transaction
        logger.critical(f"Database connection or operation error: {db_error}", exc_info=True)
        # Wrap and raise ConnectionError for unified handling upstream
        raise ConnectionError(f"Database connection or operation failed: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        raise # Re-raise other unexpected errors
    finally:
        if conn and not conn.is_closed(): await conn.close(); logger.info("Database connection closed.")


async def search_similar_chunks(
    query_text: str,
    top_k: int = 5,
    document_filename: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches for text chunks most similar to the query_text using vector embeddings.

    Args:
        query_text: The text to search for.
        top_k: The number of top similar chunks to retrieve.
        document_filename: Optional. If provided, filters chunks by this filename.

    Returns:
        A list of dictionaries, each representing a similar chunk with its
        ID, text content, metadata, and similarity score. Returns an empty
        list if an error occurs or no chunks are found.
    """
    logger.info(f"Starting similarity search for query: '{query_text[:50]}...', top_k={top_k}, filename_filter='{document_filename}'")

    if top_k <= 0:
        logger.warning("top_k must be positive. Returning empty list.")
        return []

    try:
        # Note: embedding_generator.get_embedding_client() and .embed_query() are synchronous
        embedding_client = embedding_generator.get_embedding_client()
        query_embedding = embedding_client.embed_query(query_text)
        logger.info(f"Generated embedding for query (Dimension: {len(query_embedding)})")
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}", exc_info=True)
        return []

    db_config = load_db_config()
    if not all([db_config["database"], db_config["user"], db_config["password"]]):
        error_msg = "Database connection details missing in .env (DB_NAME, DB_USER, DB_PASSWORD) for search."
        logger.critical(error_msg)
        raise ConnectionError(error_msg)

    conn: Optional[asyncpg.Connection] = None
    results: List[Dict[str, Any]] = []

    try:
        logger.info(f"Connecting to PostgreSQL database '{db_config['database']}' on {db_config['host']} for search...")
        conn = await asyncpg.connect(**db_config)
        logger.info("Database connection successful for search (asyncpg).")

        table_name = "document_chunks"  # Use the correct table for chunks
        params: List[Any] = [json.dumps(query_embedding)]

        # Base query using cosine distance operator <=>
        # Selecting logical_chunk_id, chunk_text, and chunk_order.
        # The query now joins document_chunks with documents to filter by file_name.
        
        param_idx = 2  # Start next param index from $2 ($1 is query_embedding)
        
        if document_filename:
            sql_query_parts = [
                f"SELECT dc.logical_chunk_id, dc.chunk_text, dc.chunk_order, dc.embedding <=> $1 AS distance",
                f"FROM document_chunks dc",
                f"JOIN documents d ON dc.document_id = d.id",
                f"WHERE d.file_name = ${param_idx}",
            ]
            params.append(document_filename)
            param_idx += 1
        else:
            sql_query_parts = [
                f"SELECT logical_chunk_id, chunk_text, chunk_order, embedding <=> $1 AS distance FROM {table_name}"
            ]

        sql_query_parts.append(f"ORDER BY distance ASC LIMIT ${param_idx}")
        params.append(top_k)

        sql_query_string = " ".join(sql_query_parts)

        # Log query without actual embedding for security/brevity
        log_params_str = [str(p) if not isinstance(p, list) else f"<embedding_vector_len_{len(p)}>" for p in params]
        logger.info(f"Executing search query: {sql_query_string} with params: {log_params_str}")

        rows = await conn.fetch(sql_query_string, *params)

        for row in rows:
            # Cosine distance (row['distance']) is 0 for identical, 2 for opposite.
            # Similarity score = 1 - distance.
            similarity_score = 1 - row['distance']

            # metadata_content is no longer directly selected.
            # We return chunk_order instead.
            # If more metadata is needed, a JOIN with 'documents' table and specific selection is required.
            results.append({
                "chunk_id": row['logical_chunk_id'], # Use logical_chunk_id
                "text_content": row['chunk_text'], # Changed from row['text_content'] to row['chunk_text']
                "chunk_order": row['chunk_order'], # Added chunk_order
                # "metadata": {}, # Placeholder if metadata structure is expected by caller
                "similarity_score": similarity_score
            })

        logger.info(f"Found {len(results)} similar chunks.")
        return results

    except (asyncpg.PostgresError, OSError) as db_error:
        logger.critical(f"Database connection or query error during search: {db_error}", exc_info=True)
        raise ConnectionError(f"Database connection or query failed during search: {db_error}") from db_error
    except Exception as e:
        logger.critical(f"An unexpected error occurred during search: {e}", exc_info=True)
        raise # Re-raise other unexpected errors
    finally:
        if conn and not conn.is_closed():
            await conn.close()
            logger.info("Database connection closed after search.")


# Example usage block (remains the same)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running vector_store_handler.py (asyncpg) directly for testing ---")
    logger.warning("This test block WILL attempt to connect to and write to the database.")
    embedding_dim = 1536
    sample_document_id = 999  # Example document_id for testing
    sample_rag_chunks_with_embeddings = [
        {"chunk_id": "async_test_001", "text_content": "Async test chunk 1.", "metadata": {"s": "t1a"}, "embedding": [0.5] * embedding_dim},
        {"chunk_id": "async_test_002", "text_content": "Async test chunk 2.", "metadata": {"s": "t2a"}, "embedding": [0.6] * embedding_dim}
    ]
    logger.info(f"Sample Chunks to Add/Update: {len(sample_rag_chunks_with_embeddings)} for document_id {sample_document_id}")
    confirm = input("\nProceed with test database insertion/update? (yes/no): ")
    if confirm.lower() == 'yes':
        logger.info("Proceeding with test database operation...")
        try: asyncio.run(add_chunks_to_vector_store(sample_document_id, sample_rag_chunks_with_embeddings))
        except ConnectionError as e: logger.error(f"Test failed due to connection error: {e}")
        except Exception as e: logger.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
        else: logger.info("Test database operation process completed (check database).")
    else: logger.info("Test database operation cancelled by user.")
    logger.info("--- Vector Store Handler Test Complete ---")