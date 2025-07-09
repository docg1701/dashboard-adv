# -*- coding: utf-8 -*-
"""
Handles PDF document layout analysis using the Docling library.
Extracts structural elements like text blocks, images, and tables from PDF pages.
"""
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

# Attempt to import Docling components
try:
    from docling import DocumentConverter, ConversionParameters
    from docling.datamodel.structure import ContentView, LayoutBlockType as DoclingLayoutBlockType
    DOClING_AVAILABLE = True
except ImportError:
    DOClING_AVAILABLE = False
    # This module will not be usable if Docling is not installed,
    # but we define the structures so other modules can type hint.
    # A runtime check or an explicit init error would be good in a real scenario.
    class DoclingLayoutBlockType: # Dummy for type hinting if not available
        TEXT = "TEXT"
        IMAGE = "IMAGE"
        TABLE = "TABLE"
        LIST = "LIST" # Common type, add others as discovered from Docling
        HEADLINE = "HEADLINE"
        CUSTOM = "CUSTOM" # For any other types Docling might have

logger = logging.getLogger(__name__)

@dataclass
class BoundingBox:
    """Represents a bounding box with x, y, width, height coordinates."."""
    x: float
    y: float
    width: float
    height: float
    page_width: Optional[float] = None # Optional: page dimensions for context
    page_height: Optional[float] = None

@dataclass
class LayoutBlockData:
    """
    Represents a single layout block identified on a page.
    Stores its type, bounding box, extracted text content, and reading order.
    """
    type: str  # e.g., "TEXT", "IMAGE", "TABLE", "LIST_ITEM", "TITLE", etc.
    bbox_abs: BoundingBox # Absolute coordinates on the page
    # bbox_rel: Optional[BoundingBox] = None # Relative coordinates (0-1, if needed)
    text_content: Optional[str] = None
    reading_order_id: Optional[int] = None
    confidence: Optional[float] = None # If Docling provides it
    raw_block_type: Optional[str] = None # Store the original Docling block type string

    # Example of how one might include the image data for an image block
    # image_bytes: Optional[bytes] = field(default=None, repr=False)


# Mappings from Docling's type enum (or string if enum not directly used) to our simple strings
# This needs to be verified against actual Docling output once observable.
# Assuming DoclingLayoutBlockType is an enum-like object from docling.datamodel.structure
DOCLING_TYPE_MAP = {
    DoclingLayoutBlockType.TEXT: "TEXT",
    DoclingLayoutBlockType.IMAGE: "IMAGE",
    DoclingLayoutBlockType.TABLE: "TABLE",
    DoclingLayoutBlockType.LIST: "LIST", # Assuming LIST exists
    DoclingLayoutBlockType.HEADLINE: "HEADLINE", # Assuming HEADLINE exists
    # Add other mappings as discovered from Docling's LayoutBlockType
}

def _convert_docling_block_to_layout_block_data(docling_block, page_width: float, page_height: float) -> LayoutBlockData:
    """Converts a single Docling LayoutBlock object to our LayoutBlockData."."""

    # Type mapping
    # The 'type' attribute of a docling_block might be an enum or similar object.
    # We need to access its value (e.g., .name or .value) for the key in DOCLING_TYPE_MAP.
    # This is speculative until actual docling_block structure is seen.
    # For now, let's assume docling_block.type has a .name attribute if it's an enum.
    docling_block_type_enum_val = getattr(docling_block, 'type', None)
    block_type_str = "UNKNOWN"
    raw_block_type_str = str(docling_block_type_enum_val)

    if docling_block_type_enum_val:
        block_type_str = DOCLING_TYPE_MAP.get(docling_block_type_enum_val, f"UNMAPPED_{raw_block_type_str}")

    # Bounding box
    # Assuming docling_block.bbox has x, y, width, height attributes.
    # These are assumed to be absolute coordinates on the page.
    abs_bbox = BoundingBox(
        x=docling_block.bbox.x,
        y=docling_block.bbox.y,
        width=docling_block.bbox.width,
        height=docling_block.bbox.height,
        page_width=page_width,
        page_height=page_height
    )

    text = getattr(docling_block, 'text_content', None)
    if text is not None:
        text = text.strip()

    return LayoutBlockData(
        type=block_type_str,
        bbox_abs=abs_bbox,
        text_content=text,
        reading_order_id=getattr(docling_block, 'reading_order_id', None),
        confidence=getattr(docling_block, 'confidence', None), # If available
        raw_block_type=raw_block_type_str
    )

def analyze_pdf_layout(pdf_path: str) -> List[List[LayoutBlockData]]:
    """
    Analyzes the layout of a given PDF using Docling.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of lists, where each inner list contains LayoutBlockData objects
        for a page. Returns an empty list if Docling is unavailable or processing fails.
    """
    if not DOClING_AVAILABLE:
        logger.warning("Docling library is not available. Cannot analyze PDF layout.")
        return []

    logger.info(f"Starting layout analysis for PDF: {pdf_path} using Docling.")
    all_pages_layout_data: List[List[LayoutBlockData]] = []

    try:
        converter = DocumentConverter()
        # Requesting specific views that should include layout information
        params = ConversionParameters(
            content_views=[
                ContentView.TEXT, # For overall text and potentially text within blocks
                ContentView.LAYOUT_BLOCKS, # Primary source for layout block geometry and type
                ContentView.STRUCTURE # Might provide higher-level semantic structure
            ]
        )

        logger.debug(f"Docling: Converting PDF '{pdf_path}' with views: TEXT, LAYOUT_BLOCKS, STRUCTURE")
        docling_doc = converter.convert(source=pdf_path, params=params)

        if not docling_doc or not docling_doc.pages:
            logger.warning(f"Docling conversion of '{pdf_path}' resulted in no document or no pages.")
            return []

        logger.info(f"Docling processed {len(docling_doc.pages)} pages from '{pdf_path}'.")

        for i, page in enumerate(docling_doc.pages):
            page_layout_data: List[LayoutBlockData] = []
            page_width = getattr(page, 'width', 0.0)
            page_height = getattr(page, 'height', 0.0)

            if page.layout_blocks:
                logger.debug(f"Page {i+1}: Found {len(page.layout_blocks)} layout blocks.")
                for docling_block in page.layout_blocks:
                    try:
                        layout_block_item = _convert_docling_block_to_layout_block_data(docling_block, page_width, page_height)
                        page_layout_data.append(layout_block_item)
                    except Exception as e:
                        logger.error(f"Page {i+1}: Error converting a Docling block: {e}", exc_info=True)
            else:
                logger.debug(f"Page {i+1}: No layout blocks found via page.layout_blocks.")

            all_pages_layout_data.append(page_layout_data)

    except Exception as e:
        logger.error(f"Error during Docling PDF layout analysis for '{pdf_path}': {e}", exc_info=True)
        # Depending on desired robustness, could return partially processed data or empty
        return []

    logger.info(f"Successfully completed layout analysis for '{pdf_path}'.")
    return all_pages_layout_data

if __name__ == '__main__':
    # This is a placeholder for direct testing of this module.
    # Requires a PDF path and Docling to be installed.
    # Example:
    # logging.basicConfig(level=logging.DEBUG)
    # test_pdf_path = "path/to/your/sample.pdf"
    # if DOClING_AVAILABLE and os.path.exists(test_pdf_path):
    #     layouts = analyze_pdf_layout(test_pdf_path)
    #     for page_num, page_layout in enumerate(layouts):
    #         logger.info(f"--- Page {page_num + 1} ---")
    #         if not page_layout:
    #             logger.info("  No layout blocks found.")
    #             continue
    #         for block_num, block in enumerate(page_layout):
    #             logger.info(f"  Block {block_num + 1}: Type={block.type}, Text='{str(block.text_content)[:50]}...', BBox={block.bbox_abs}")
    # else:
    #     if not DOClING_AVAILABLE:
    #         logger.error("Cannot run example: Docling not available.")
    #     if not os.path.exists(test_pdf_path):
    #         logger.error(f"Cannot run example: Test PDF not found at {test_pdf_path}")
    pass
