# -*- coding: utf-8 -*-
"""
Handles interaction with the vector store (PostgreSQL + pgvector) using SQLAlchemy.
"""
import os
import sys
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import text, insert
from sqlalchemy.exc import SQLAlchemyError

from src.db_config import get_db_session
from src.vectorizer import embedding_generator
from src.models.document import DocumentChunk # Import the ORM model

logger = logging.getLogger(__name__)


async def add_chunks_to_vector_store(document_id: int, rag_chunks: List[Dict[str, Any]]):
    """
    Adds or updates text chunks, metadata, and embeddings in PostgreSQL using SQLAlchemy ORM.
    Uses a single bulk "upsert" operation with the insert() construct.
    """
    if not rag_chunks:
        logger.warning("Vector Store Handler: No chunks provided to add.")
        return

    logger.info(f"--- Adding {len(rag_chunks)} Chunks to Vector Store for document_id: {document_id} ---")

    chunks_to_insert = []
    skipped_count = 0
    for chunk in rag_chunks:
        logical_chunk_id = chunk.get("chunk_id")
        text_content = chunk.get("text_content")
        embedding = chunk.get("embedding")
        metadata = chunk.get("metadata", {})
        chunk_order = metadata.get("original_chunk_index_on_page", 0)

        if not all([logical_chunk_id, text_content, embedding]):
            logger.warning(f"Skipping chunk with logical_id '{logical_chunk_id}' due to missing data.")
            skipped_count += 1
            continue
        
        chunks_to_insert.append({
            "document_id": document_id,
            "logical_chunk_id": logical_chunk_id,
            "chunk_text": text_content,
            "embedding": json.dumps(embedding),
            "chunk_order": chunk_order
        })

    if not chunks_to_insert:
        logger.warning("No valid chunks to insert after validation.")
        return

    # Use the ORM insert() construct for a robust bulk insert.
    # The 'on_conflict_do_update' is specific to PostgreSQL.
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    insert_stmt = pg_insert(DocumentChunk).values(chunks_to_insert)
    
    update_dict = {
        'document_id': insert_stmt.excluded.document_id,
        'chunk_text': insert_stmt.excluded.chunk_text,
        'embedding': insert_stmt.excluded.embedding,
        'chunk_order': insert_stmt.excluded.chunk_order,
    }

    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=['logical_chunk_id'],
        set_=update_dict
    )

    try:
        async with get_db_session() as session:
            async with session.begin():
                await session.execute(upsert_stmt)
            
            inserted_count = len(chunks_to_insert)
            logger.info(f"Transaction committed. Successfully upserted {inserted_count} chunks for document_id {document_id}.")
            if skipped_count > 0:
                logger.warning(f"Skipped {skipped_count} invalid chunks.")

    except SQLAlchemyError as e:
        logger.critical(f"A database error occurred during chunk insertion: {e}", exc_info=True)
        raise ConnectionError(f"Database operation failed: {e}") from e
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        raise


async def search_similar_chunks(
    query_text: str,
    top_k: int = 5,
    document_filename: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches for text chunks most similar to the query_text using vector embeddings.
    """
    logger.info(f"Starting similarity search for query: '{query_text[:50]}...', top_k={top_k}, filename_filter='{document_filename}'")

    if top_k <= 0:
        logger.warning("top_k must be positive. Returning empty list.")
        return []

    try:
        embedding_client = embedding_generator.get_embedding_client()
        query_embedding = embedding_client.embed_query(query_text)
        logger.info(f"Generated embedding for query (Dimension: {len(query_embedding)})")
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}", exc_info=True)
        return []

    params = {
        "query_embedding": json.dumps(query_embedding),
        "top_k": top_k
    }
    
    query_parts = [
        "SELECT dc.logical_chunk_id, dc.chunk_text, dc.chunk_order, dc.embedding <=> :query_embedding::vector AS distance",
        "FROM document_chunks dc"
    ]
    
    if document_filename:
        query_parts.append("JOIN documents d ON dc.document_id = d.id")
        query_parts.append("WHERE d.file_name = :document_filename")
        params["document_filename"] = document_filename

    query_parts.append("ORDER BY distance ASC")
    query_parts.append("LIMIT :top_k")
    
    sql_query = text(" ".join(query_parts))

    try:
        async with get_db_session() as session:
            result = await session.execute(sql_query, params)
            rows = result.fetchall()

        results = []
        for row in rows:
            similarity_score = 1 - row.distance
            results.append({
                "chunk_id": row.logical_chunk_id,
                "text_content": row.chunk_text,
                "chunk_order": row.chunk_order,
                "similarity_score": similarity_score
            })

        logger.info(f"Found {len(results)} similar chunks.")
        return results

    except SQLAlchemyError as e:
        logger.critical(f"Database query error during similarity search: {e}", exc_info=True)
        raise ConnectionError(f"Database query failed: {e}") from e
    except Exception as e:
        logger.critical(f"An unexpected error occurred during similarity search: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running vector_store_handler.py directly for testing ---")
    
    embedding_dim = 768
    sample_document_id = 1001
    sample_rag_chunks = [
        {
            "chunk_id": f"test_chunk_{i}",
            "text_content": f"This is a sample text for chunk number {i}.",
            "embedding": [float(i) / 100.0] * embedding_dim,
            "metadata": {"original_chunk_index_on_page": i}
        }
        for i in range(5)
    ]

    async def run_tests():
        logger.info(f"--- Testing add_chunks_to_vector_store for document_id {sample_document_id} ---")
        try:
            await add_chunks_to_vector_store(sample_document_id, sample_rag_chunks)
            logger.info("add_chunks_to_vector_store completed successfully.")
        except Exception as e:
            logger.error(f"add_chunks_to_vector_store failed: {e}", exc_info=True)

        logger.info("\n--- Testing search_similar_chunks ---")
        test_query = "sample text for chunk"
        try:
            similar_chunks = await search_similar_chunks(test_query, top_k=3)
            logger.info(f"Search results for '{test_query}':")
            for chunk in similar_chunks:
                logger.info(f"  - Chunk ID: {chunk['chunk_id']}, Score: {chunk['similarity_score']:.4f}, Text: '{chunk['text_content'][:50]}...' ")
        except Exception as e:
            logger.error(f"search_similar_chunks failed: {e}", exc_info=True)

    confirm = input("\nThis test will connect to the database and perform read/write operations. Proceed? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(run_tests())
    else:
        logger.info("Test execution cancelled by user.")
    
    logger.info("--- Vector Store Handler Test Complete ---")