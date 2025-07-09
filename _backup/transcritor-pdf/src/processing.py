# -*- coding: utf-8 -*-
"""
Core PDF processing pipeline logic.
"""
import logging
import uuid
from typing import List, Dict, Any

import pypdfium2 as pdfium

# Assuming these modules are in the same src directory or PYTHONPATH is set up correctly
from src.vectorizer import embedding_generator
from src.vectorizer import vector_store_handler
# from src.db_config import EMBEDDING_DIMENSIONS # Not directly used here, but good to be aware of

logger = logging.getLogger(__name__)

# --- Constants for Chunking ---
DEFAULT_CHUNK_SIZE = 1000  # Characters
DEFAULT_CHUNK_OVERLAP = 100 # Characters

# --- Text Chunking Helper Function ---
def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    """
    Splits a long text into smaller overlapping chunks.
    A simple implementation. For more advanced chunking, consider Langchain's text_splitters.
    """
    if not text:
        return []

    chunks = []
    start_index = 0
    text_len = len(text)
    while start_index < text_len:
        end_index = start_index + chunk_size
        chunks.append(text[start_index:end_index])

        next_start_index = start_index + chunk_size - chunk_overlap
        if next_start_index >= text_len: # If the next step would go past the end
            break
        if next_start_index <= start_index : # Avoid infinite loop if chunk_overlap >= chunk_size
            logger.warning("Chunk overlap is too large compared to chunk size, stopping chunking to prevent infinite loop.")
            break
        start_index = next_start_index

    return chunks

# --- Main PDF Processing Pipeline Function ---
async def process_pdf_pipeline(file_content: bytes, filename: str, document_id: int) -> Dict[str, Any]: # Added document_id
    """
    Orchestrates the PDF processing pipeline:
    Requires document_id to associate chunks with their parent document in the vector store.
    1. Loads PDF from bytes.
    2. Extracts text content page by page.
    3. Chunks the extracted text.
    4. Generates embeddings for the chunks.
    5. Stores the chunks and their embeddings in the vector store.
    """
    logger.info(f"Starting PDF processing pipeline for file: {filename} (size: {len(file_content)} bytes)")

    all_text_chunks_with_metadata: List[Dict[str, Any]] = []
    pages_in_pdf = 0

    try:
        # 1. Load PDF from bytes
        logger.info("Loading PDF document...")
        pdf = pdfium.PdfDocument(file_content)
        pages_in_pdf = len(pdf)
        logger.info(f"PDF loaded successfully. Number of pages: {pages_in_pdf}")

        # 2. Iterate through pages, extract text, and chunk
        for page_idx in range(pages_in_pdf): # Iterate by index to ensure pages are closed
            page = pdf[page_idx] # Load page
            page_number = page_idx + 1
            logger.info(f"Processing page {page_number}/{pages_in_pdf}...")

            # Extract text per page
            text_page = page.get_textpage()
            page_text = text_page.get_text_range()

            # It's important to close these objects as per pypdfium2 documentation
            text_page.close()
            page.close()

            if not page_text or page_text.isspace():
                logger.warning(f"No text extracted from page {page_number}.")
                continue

            logger.info(f"Extracted {len(page_text)} characters from page {page_number}.")

            # Chunk extracted page text
            text_chunks_on_page = chunk_text(page_text, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP)
            logger.info(f"Split page {page_number} text into {len(text_chunks_on_page)} chunks.")

            for chunk_idx, chunk_content in enumerate(text_chunks_on_page):
                chunk_id = str(uuid.uuid4()) # Globally unique ID for each chunk

                chunk_data = {
                    "chunk_id": chunk_id,
                    "text_content": chunk_content,
                    "metadata": {
                        "filename": filename,
                        "page_number": page_number,
                        "original_chunk_index_on_page": chunk_idx
                    }
                }
                all_text_chunks_with_metadata.append(chunk_data)

        pdf.close() # Close the PDF document after iterating all pages

        if not all_text_chunks_with_metadata:
            logger.warning(f"No text chunks were generated from the PDF: {filename}")
            return {
                "status": "completed_with_no_chunks",
                "filename": filename,
                "pages_in_pdf": pages_in_pdf,
                "total_chunks_processed": 0,
                "message": "No text content could be extracted or chunked from the PDF."
            }

        logger.info(f"Total text chunks generated from all pages: {len(all_text_chunks_with_metadata)}")

        # 3. Generate Embeddings
        logger.info("Generating embeddings for text chunks...")
        try:
            chunks_with_embeddings = embedding_generator.generate_embeddings_for_chunks(all_text_chunks_with_metadata)
            # Verify embeddings were added (simple check on the first chunk if it exists)
            if not chunks_with_embeddings or (chunks_with_embeddings and not chunks_with_embeddings[0].get("embedding")):
                 logger.warning("Embeddings might not have been generated for all chunks or list is empty.")
            logger.info("Embeddings generation step completed.")
        except Exception as emb_exc:
            logger.error(f"Error during embedding generation for {filename}: {emb_exc}", exc_info=True)
            return {"status": "error_embedding", "message": str(emb_exc), "filename": filename, "error_details": type(emb_exc).__name__}


        # 4. Store Chunks in Database (Vector Store)
        logger.info(f"Adding chunks with embeddings to the vector store for document_id: {document_id}...")
        try:
            # Pass document_id to the updated handler function
            await vector_store_handler.add_chunks_to_vector_store(document_id, chunks_with_embeddings)
            logger.info(f"Successfully added/updated chunks in the vector store for document_id: {document_id}.")
        except Exception as store_exc:
            logger.error(f"Error adding chunks to vector store for {filename} (Doc ID: {document_id}): {store_exc}", exc_info=True)
            return {"status": "error_storing", "message": str(store_exc), "filename": filename, "error_details": type(store_exc).__name__}

        # 5. Return Summary
        return {
            "status": "success",
            "filename": filename,
            "pages_in_pdf": pages_in_pdf,
            "total_chunks_processed": len(chunks_with_embeddings),
            "message": "PDF processed and chunks stored successfully."
        }

    except pdfium.PdfiumError as pdf_err: # Specific pypdfium2 error
        logger.error(f"A pypdfium2 error occurred while processing {filename}: {pdf_err}", exc_info=True)
        if 'pdf' in locals() and pdf is not None: pdf.close() # Ensure PDF is closed on error
        return {"status": "error_pdf_processing", "message": f"PDF library error: {pdf_err}", "filename": filename, "error_details": type(pdf_err).__name__}
    except Exception as e:
        logger.error(f"An unexpected error occurred in PDF processing pipeline for {filename}: {e}", exc_info=True)
        if 'pdf' in locals() and pdf is not None: pdf.close() # Ensure PDF is closed on error
        return {"status": "error_unexpected", "message": str(e), "filename": filename, "error_details": type(e).__name__}
