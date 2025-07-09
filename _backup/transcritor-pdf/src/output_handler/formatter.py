# -*- coding: utf-8 -*-
"""Formats extracted page data into chunks suitable for RAG systems.

This module takes the list of dictionaries (each representing processed data
from a single page) and transforms it into a list of smaller "chunks".
Each chunk contains a piece of text content and associated metadata
(like source file, page number, and extracted entities) necessary for
effective indexing and retrieval in a Retrieval-Augmented Generation context.
Includes logging for operations and errors.
"""

import json
import os
import logging
from typing import List, Dict, Any

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# --- Configuration ---
# Defines how text is split into chunks. Using double newline (paragraph).
# TODO: Consider more advanced chunking (e.g., recursive, semantic) via Langchain text splitters if needed.
CHUNK_SEPARATOR = "\n\n"
# Minimum character length for a chunk to be considered valid. Prevents overly short/noisy chunks.
# TODO: Make this configurable?
MIN_CHUNK_LENGTH = 50

def format_output_for_rag(all_pages_data: List[Dict[str, Any]], original_pdf_path: str) -> List[Dict[str, Any]]:
    """Formats page data into a list of RAG-suitable text chunks with metadata.

    Iterates through the data extracted from each page. For pages without errors
    and containing extracted text, it splits the text into chunks based on the
    `CHUNK_SEPARATOR`. Chunks shorter than `MIN_CHUNK_LENGTH` are discarded.
    Each valid chunk is then combined with relevant metadata extracted from
    that page (e.g., source PDF filename, page number, client name, document date)
    into a dictionary structure optimized for vector store indexing.

    Args:
        all_pages_data: A list where each item is a dictionary containing the
                        results of processing a single page. Expected keys
                        include 'page_number', 'extracted_text', 'error' (optional),
                        and potentially parsed entities like 'client_name',
                        'document_date', 'signature_found'.
        original_pdf_path: The file path of the original PDF document being processed.
                           Used to associate chunks with their source file.

    Returns:
        A list of dictionaries. Each dictionary represents a single text chunk
        ready for embedding and indexing. The dictionary structure includes:
        - 'chunk_id': A unique identifier for the chunk.
        - 'text_content': The actual text content of the chunk.
        - 'metadata': A dictionary containing associated metadata (source_pdf,
                      page_number, chunk_index_on_page, client_name, etc.).
        Returns an empty list if `all_pages_data` is empty or if no valid
        chunks meeting the length requirement are found.
    """
    logger.info("--- Formatting output for RAG ---")
    rag_chunks = []
    chunk_id_counter = 0 # Global counter for unique chunk IDs across the document

    if not all_pages_data:
        logger.warning("No page data provided to format.")
        return []

    # Extract just the filename for potentially cleaner metadata
    pdf_basename = os.path.basename(original_pdf_path)
    logger.debug(f"Using PDF basename for metadata: {pdf_basename}")

    for page_data in all_pages_data:
        page_number = page_data.get("page_number", "Unknown")
        extracted_text = page_data.get("extracted_text", "")
        page_error = page_data.get("error")

        # Validate page data before processing
        if page_error or not extracted_text or extracted_text in ["Extraction Failed", "Processing Error", "Loading Error"]:
            logger.warning(f"Skipping page {page_number} due to error ('{page_error}') or missing/invalid text.")
            continue

        # --- Text Chunking ---
        logger.debug(f"Chunking text for page {page_number} using separator '{CHUNK_SEPARATOR.encode('unicode_escape').decode()}'.")
        text_chunks = extracted_text.split(CHUNK_SEPARATOR)
        page_chunk_index = 0 # Index of the chunk within the current page

        for chunk_text in text_chunks:
            chunk_text = chunk_text.strip() # Remove leading/trailing whitespace

            # Filter out short or empty chunks
            if len(chunk_text) < MIN_CHUNK_LENGTH:
                logger.debug(f"  Skipping short chunk on page {page_number} (length: {len(chunk_text)} < {MIN_CHUNK_LENGTH}).")
                continue

            # Increment counters for valid chunks
            chunk_id_counter += 1
            page_chunk_index += 1

            # --- Metadata Association ---
            # Gather metadata specific to this chunk from the page data
            metadata = {
                "source_pdf": pdf_basename, # Or use original_pdf_path if full path needed
                "page_number": page_number,
                "chunk_index_on_page": page_chunk_index,
                # Carry over parsed information if available
                "client_name": page_data.get("client_name"),
                "document_date": page_data.get("document_date"),
                "signature_found": page_data.get("signature_found"),
                # Example: Add illness list only if it's not empty
                # "relevant_illness_mentions": ills if (ills := page_data.get("relevant_illness_mentions")) else None,
            }
            # Optional: Remove keys with None values from metadata for cleaner storage
            # metadata = {k: v for k, v in metadata.items() if v is not None}
            logger.debug(f"  Metadata for chunk {chunk_id_counter}: {metadata}")

            # --- Create RAG Chunk Dictionary ---
            # Define the final structure for each chunk entry
            chunk_unique_id = f"{pdf_basename}_p{page_number}_c{chunk_id_counter}"
            rag_chunk_data = {
                "chunk_id": chunk_unique_id, # Construct a unique ID
                "text_content": chunk_text, # The text itself
                "metadata": metadata, # Associated metadata dictionary
            }
            rag_chunks.append(rag_chunk_data)
            logger.debug(f"  Created RAG chunk: {chunk_unique_id}")

    logger.info(f"Formatted data into {len(rag_chunks)} chunks suitable for RAG.")
    return rag_chunks

# Example usage block (for testing when script is run directly)
if __name__ == "__main__":
    # Configure logging for test run
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running formatter.py directly for testing ---")

    # Example input data simulating output from previous steps
    sample_page_data_list = [
        { # Page 1
            "page_number": 1, "source_file": "test_doc.pdf", "temp_image_path": "temp/page_001.webp",
            "preprocessing_applied": True,
            "extracted_text": "First paragraph, definitely longer than fifty characters to pass the minimum length check.\n\nSecond paragraph, also made long enough for testing purposes.\n\nShort one.",
            "client_name": "Maria Souza", "document_date": "2025-04-20", "signature_found": True,
            "relevant_illness_mentions": ["diabetes", "hypertension"]
        },
        { # Page 2
            "page_number": 2, "source_file": "test_doc.pdf", "temp_image_path": "temp/page_002.webp",
            "preprocessing_applied": True,
            "extracted_text": "Page 2 only has one single paragraph of text content which is long enough to be considered a chunk.",
            "client_name": "Maria Souza", "document_date": "2025-04-20", "signature_found": False,
            "relevant_illness_mentions": []
        },
        { # Page 3 (Error)
            "page_number": 3, "source_file": "test_doc.pdf", "temp_image_path": "temp/page_003.webp",
            "error": "LLM Timeout", "extracted_text": "Processing Error"
        }
    ]
    sample_pdf_path = "example_docs/medical_report_01.pdf"

    logger.info("\nInput Page Data (Sample - showing page numbers):")
    for p in sample_page_data_list: logger.info(f"  Page: {p.get('page_number')}, Error: {p.get('error')}, Text Length: {len(p.get('extracted_text','')) if p.get('extracted_text') else 0}")

    # Format the data
    formatted_chunks = format_output_for_rag(sample_page_data_list, sample_pdf_path)

    if formatted_chunks:
        logger.info("--- Formatted Chunks for RAG (Sample Output) ---")
        logger.info("Example Chunk (First Chunk):")
        # Use print for direct test output, or log the JSON string
        print(json.dumps(formatted_chunks[0], indent=2, ensure_ascii=False))
        logger.info(f"\nTotal chunks generated: {len(formatted_chunks)}")
        logger.info("-----------------------------------------------")
    else:
        logger.warning("No RAG chunks were generated from the sample data.")

    logger.info("--- Formatter Test Complete ---")