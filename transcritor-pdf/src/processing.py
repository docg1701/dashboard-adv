# -*- coding: utf-8 -*-
"""
Core PDF processing pipeline logic.
"""
import logging
import uuid
from typing import List, Dict, Any

import pypdfium2 as pdfium
from PIL import Image # For handling images if needed by IA extraction

# Assuming these modules are in the same src directory or PYTHONPATH is set up correctly
from src.vectorizer import embedding_generator
from src.vectorizer import vector_store_handler
from src.extractor import text_extractor # For IA-based text extraction from images

logger = logging.getLogger(__name__)

from langchain.text_splitter import RecursiveCharacterTextSplitter # Import Langchain splitter

# --- Constants ---
# For Chunking
DEFAULT_CHUNK_SIZE = 1000  # Characters
DEFAULT_CHUNK_OVERLAP = 100 # Characters
# For Hybrid Extraction Decision
MIN_DIGITAL_TEXT_LENGTH_THRESHOLD = 20 # Characters. If digital text < this, try IA OCR.


# --- Text Chunking Helper Function ---
# Initialize the text splitter once, can be configured via settings if needed
langchain_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=DEFAULT_CHUNK_SIZE,
    chunk_overlap=DEFAULT_CHUNK_OVERLAP,
    length_function=len,
    is_separator_regex=False, # Treat separators as literal strings
    separators=["\n\n", "\n", ". ", " ", ""], # Common separators, can be customized
)

def chunk_text_langchain(text: str) -> List[str]:
    """
    Splits a long text into smaller overlapping chunks using Langchain's RecursiveCharacterTextSplitter.
    The splitter instance is pre-configured with DEFAULT_CHUNK_SIZE and DEFAULT_CHUNK_OVERLAP.
    """
    if not text:
        return []

    logger.debug(f"Chunking text of length {len(text)} with Langchain RecursiveCharacterTextSplitter "
                 f"(chunk_size={DEFAULT_CHUNK_SIZE}, chunk_overlap={DEFAULT_CHUNK_OVERLAP})")

    chunks = langchain_text_splitter.split_text(text)

    logger.debug(f"Produced {len(chunks)} chunks.")
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
            page_text_digital = None
            final_page_text = None
            extraction_method = "digital" # Default method

            try:
                text_page = page.get_textpage()
                page_text_digital = text_page.get_text_range()
                text_page.close() # Close text_page object early

                # Decision logic for hybrid extraction
                if not page_text_digital or len(page_text_digital.strip()) < MIN_DIGITAL_TEXT_LENGTH_THRESHOLD:
                    logger.warning(
                        f"Page {page_number}: Digital text is empty or below threshold ({len(page_text_digital.strip())} chars). "
                        f"Attempting IA-based OCR."
                    )
                    extraction_method = "ia_ocr"
                    try:
                        # Render page to PIL Image
                        # Common practice: render at a reasonable DPI for OCR, e.g., 200-300 DPI.
                        # Default pypdfium2 render DPI is 72, which might be low for OCR.
                        # page.render(scale=300/72) would be approx 300 DPI.
                        pil_image = page.render(scale=2).to_pil() # Scale=2 (approx 144 DPI), adjust as needed

                        # Extract text using the IA model
                        final_page_text = text_extractor.extract_text_from_image(pil_image)
                        pil_image.close() # Close PIL image after use

                        if final_page_text:
                            logger.info(f"Page {page_number}: Successfully extracted text using IA-OCR ({len(final_page_text)} chars).")
                        else:
                            logger.warning(f"Page {page_number}: IA-OCR extraction returned no text. Original digital text had {len(page_text_digital.strip())} chars.")
                            # Fallback to digital text if IA fails, even if it's short, or treat as empty.
                            # For now, if IA returns None/empty, and digital was also poor, it will be skipped.
                            # If digital had some text, but IA failed, we might want to use the digital one.
                            # Current logic: if IA fails, final_page_text is None.
                    except Exception as ia_exc:
                        logger.error(f"Page {page_number}: Error during IA-based OCR: {ia_exc}", exc_info=True)
                        # Fallback to digital text in case of IA error
                        final_page_text = page_text_digital
                        extraction_method = "digital_fallback_after_ia_error"
                else:
                    final_page_text = page_text_digital
                    logger.info(f"Page {page_number}: Extracted {len(final_page_text)} characters using digital method.")

            finally:
                page.close() # Ensure page object is closed in all cases for this iteration

            if not final_page_text or final_page_text.isspace():
                logger.warning(f"Page {page_number}: No text extracted after attempting {extraction_method} method.")
                continue

            # Log the length of the text we are actually going to chunk
            logger.info(f"Page {page_number}: Proceeding to chunk {len(final_page_text)} characters (method: {extraction_method}).")

            # Chunk extracted page text using the new Langchain splitter
            # The `final_page_text` variable holds the text to be chunked
            text_chunks_on_page = chunk_text_langchain(final_page_text)
            logger.info(f"Split page {page_number} text into {len(text_chunks_on_page)} chunks using Langchain splitter.")

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
