# -*- coding: utf-8 -*-
"""Handles splitting PDF files into individual page images.

Includes per-page error handling during rendering/saving.
"""

import pypdfium2 as pdfium
import os
import sys
import logging
from typing import Generator, Optional # Import Optional
from PIL import Image

# Get a logger instance for this module
logger = logging.getLogger(__name__)

TEMP_PAGE_DIR = "temp_pdf_pages"
# Use Optional[str] as the generator might yield None for failed pages
PageOutputType = Optional[str]

def split_pdf_to_pages(pdf_path: str) -> Generator[PageOutputType, None, None]:
    """Splits a PDF into individual page images saved temporarily to disk.

    Iterates through each page, attempts to render and save it as a WebP
    image. If an error occurs for a specific page, logs the error and yields
    None for that page, allowing the process to continue with subsequent pages.

    Args:
        pdf_path: The path to the input PDF file.

    Yields:
        Optional[str]: The file path to the temporary WebP image file for a
                       successfully processed page, or None if processing
                       for that specific page failed.

    Raises:
        FileNotFoundError: If the `pdf_path` does not point to an existing file.
        OSError: If the temporary directory cannot be created.
        pdfium.PdfiumError: If pypdfium2 encounters a critical error during
                            PDF loading (before page iteration).
        Exception: For other unexpected errors during initial setup.
    """
    if not os.path.isfile(pdf_path):
        error_msg = f"Input PDF not found at: {pdf_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        os.makedirs(TEMP_PAGE_DIR, exist_ok=True)
        logger.info(f"Ensured temporary directory exists: '{TEMP_PAGE_DIR}'")
    except OSError as e:
        logger.error(f"Error creating temporary directory '{TEMP_PAGE_DIR}': {e}", exc_info=True)
        raise

    logger.info(f"Starting PDF splitting for: {pdf_path} (Saving pages as WebP Lossless)")
    pdf = None
    try:
        # --- Load PDF (Critical Step) ---
        # Errors here (e.g., password, major corruption) will stop the process
        pdf = pdfium.PdfDocument(pdf_path)
        n_pages = len(pdf)
        logger.info(f"PDF contains {n_pages} pages.")

        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        safe_basename = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in pdf_basename)
        temp_file_prefix = f"{safe_basename}_page_"

        # --- Iterate Through Pages with Per-Page Error Handling ---
        for i in range(n_pages):
            page_number = i + 1
            page = None
            bitmap = None
            pil_image = None
            temp_image_path = None
            page_successfully_processed = False # Flag for this page

            try:
                # --- Attempt to process this specific page ---
                logger.debug(f"Processing page {page_number}...")
                temp_image_filename = f"{temp_file_prefix}{page_number:04d}.webp"
                temp_image_path = os.path.join(TEMP_PAGE_DIR, temp_image_filename)

                page = pdf.get_page(i)
                # Render (can fail for corrupted pages)
                bitmap = page.render(scale=2)
                # Convert (can fail?)
                pil_image = bitmap.to_pil()
                # Save (can fail due to disk space, permissions, etc.)
                pil_image.save(temp_image_path, format="webp", lossless=True)

                logger.debug(f"Successfully saved page {page_number} to: {temp_image_path}")
                page_successfully_processed = True # Mark success for this page

            # --- Catch errors specific to this page ---
            except pdfium.PdfiumError as page_render_err:
                 logger.error(f"pypdfium2 error processing page {page_number} of '{pdf_path}': {page_render_err}", exc_info=True)
            except Exception as page_proc_err:
                logger.error(f"Unexpected error processing page {page_number} of '{pdf_path}': {page_proc_err}", exc_info=True)
            # --- End per-page error handling ---
            finally:
                # Close resources for the current page regardless of success/failure
                if pil_image: pil_image.close()
                if bitmap: bitmap.close()
                if page: page.close()
                logger.debug(f"Closed resources for page {page_number}.")

            # --- Yield result for the page ---
            if page_successfully_processed:
                yield temp_image_path # Yield path on success
            else:
                yield None # Yield None on failure for this specific page

        logger.info(f"Finished iterating through all pages for '{pdf_path}'.")

    except pdfium.PdfiumError as load_err: # Catch critical load errors
        logger.error(f"Critical pypdfium2 error loading PDF '{pdf_path}': {load_err}", exc_info=True)
        raise load_err # Re-raise critical load errors
    except Exception as setup_err: # Catch other setup errors
        logger.error(f"An unexpected error occurred during PDF splitting setup for '{pdf_path}': {setup_err}", exc_info=True)
        raise setup_err
    finally:
        # Ensure the main PDF document is closed if it was opened
        if pdf:
            pdf.close()
            logger.info(f"Closed PDF document: {pdf_path}")

# Example usage block (remains the same)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running pdf_splitter.py directly for testing ---")
    test_pdf_path = "test_document.pdf"
    if os.path.exists(test_pdf_path):
        logger.info(f"Testing PDF splitting for '{test_pdf_path}'...")
        generated_paths = []
        try:
            generated_paths = list(split_pdf_to_pages(test_pdf_path))
            page_count = len(generated_paths) # Now includes None values
            successful_pages = len([p for p in generated_paths if p is not None])
            logger.info(f"Generator finished. Total items yielded: {page_count}. Successful pages: {successful_pages}.")
            if successful_pages > 0:
                 logger.info(f"Example successful path: {next(p for p in generated_paths if p is not None)}")
                 logger.info(f"(Files are located in '{TEMP_PAGE_DIR}')")
        except Exception as e: logger.error(f"An error occurred during the test: {e}", exc_info=True)
        finally:
            if generated_paths:
                logger.info("Cleaning up temporary files...")
                files_removed_count = 0
                for p in generated_paths:
                    if p and os.path.exists(p): # Only try to remove if path is not None
                        try: os.remove(p); files_removed_count += 1
                        except OSError as e: logger.warning(f"Error removing file {p}: {e}")
                logger.info(f"Removed {files_removed_count} temporary image files.")
            try:
                if os.path.exists(TEMP_PAGE_DIR) and not os.listdir(TEMP_PAGE_DIR):
                    os.rmdir(TEMP_PAGE_DIR); logger.info(f"Removed empty temporary directory: '{TEMP_PAGE_DIR}'")
            except OSError as e: logger.warning(f"Could not remove directory '{TEMP_PAGE_DIR}': {e}")
    else:
        logger.warning(f"Test PDF file not found at '{test_pdf_path}'.")
    logger.info("--- PDF Splitter Test Complete ---")