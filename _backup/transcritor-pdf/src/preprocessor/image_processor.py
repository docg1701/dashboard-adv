# -*- coding: utf-8 -*-
"""Handles image preprocessing operations before OCR/extraction.

Includes Deskewing based on Hough Transform and Border Cropping.
"""

from PIL import Image
import numpy as np
import sys
import os
import logging
import math

# Get a logger instance for this module
logger = logging.getLogger(__name__)

# Import necessary functions from Scikit-image
try:
    from skimage import io as skimage_io
    from skimage.color import rgb2gray
    from skimage.filters import median, threshold_sauvola, gaussian
    from skimage.morphology import disk
    from skimage.exposure import equalize_adapthist # CLAHE
    from skimage.util import img_as_ubyte, img_as_float, invert # Added invert for cropping
    from skimage.feature import canny
    from skimage.transform import hough_line, hough_line_peaks, rotate
    # Import measure for finding contours/bounding box (alternative to np.nonzero)
    # from skimage.measure import find_contours, approximate_polygon
except ImportError:
    logger.critical("scikit-image library not found. Please install it using: pip install scikit-image")
    sys.exit(1)

# --- Helper Function for Deskewing ---
def estimate_skew_angle(image_gray: np.ndarray, angle_range: tuple = (-15, 15), num_peaks: int = 20) -> float:
    """Estimates the skew angle of text in a grayscale image."""
    # ...(function remains the same)...
    logger.debug("Estimating skew angle...")
    image_float = img_as_float(image_gray)
    sigma = 1.0
    blurred = gaussian(image_float, sigma=sigma)
    edges = canny(blurred, sigma=1.0, low_threshold=0.1, high_threshold=0.3)
    min_angle_rad = np.deg2rad(angle_range[0]); max_angle_rad = np.deg2rad(angle_range[1])
    tested_angles = np.linspace(min_angle_rad, max_angle_rad, 180, endpoint=False)
    try: h, theta, d = hough_line(edges, theta=tested_angles)
    except Exception as e: logger.warning(f"Hough transform failed: {e}", exc_info=True); return 0.0
    try: accum, angles, dists = hough_line_peaks(h, theta, d, num_peaks=num_peaks, min_distance=5, min_angle=5)
    except Exception as e: logger.warning(f"Hough peak finding failed: {e}"); return 0.0
    if angles.size == 0: logger.debug("No significant peaks found in Hough transform."); return 0.0
    median_angle_rad = np.median(angles)
    skew_angle_deg = np.rad2deg(median_angle_rad)
    logger.debug(f"Estimated skew (deg): {skew_angle_deg:.2f}")
    if not (angle_range[0] <= skew_angle_deg <= angle_range[1]):
         logger.debug(f"Estimated angle outside range {angle_range}. Assuming no skew.")
         return 0.0
    return skew_angle_deg

# --- Helper Function for Cropping ---
def crop_border(image_binary: np.ndarray, padding: int = 5) -> np.ndarray:
    """
    Crops the image to the bounding box of the non-background pixels.

    Assumes input is a binary image where content is non-zero (e.g., white text
    on black background after standard thresholding, or inverted).

    Args:
        image_binary: Input binary image (NumPy array, typically uint8 with 0 and 255).
        padding: Number of pixels to add around the detected bounding box.

    Returns:
        The cropped image as a NumPy array, or the original image if no
        content is found or an error occurs.
    """
    logger.debug("Attempting to crop borders...")
    if image_binary.ndim != 2:
        logger.warning("Cropping requires a 2D binary image. Skipping crop.")
        return image_binary

    # Ensure content is white (non-zero) and background is black (zero)
    # Our Sauvola output is uint8 with 0=black, 255=white (text)
    # So, we find non-zero pixels. If binarization was inverted, use np.where(image_binary == 0)
    coords = np.argwhere(image_binary > 0) # Find coordinates of non-black pixels

    if coords.size == 0:
        logger.warning("No content found in binary image. Skipping crop.")
        return image_binary # Return original if image is all black

    try:
        # Find min/max row and column indices
        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0)

        # Add padding, ensuring bounds stay within image dimensions
        y0 = max(0, y0 - padding)
        x0 = max(0, x0 - padding)
        y1 = min(image_binary.shape[0] - 1, y1 + padding)
        x1 = min(image_binary.shape[1] - 1, x1 + padding)

        # Crop the image using NumPy slicing
        cropped_image = image_binary[y0:y1+1, x0:x1+1]
        logger.debug(f"Cropped image from {image_binary.shape} to {cropped_image.shape}")
        return cropped_image
    except Exception as e:
        logger.error(f"Error during border cropping: {e}", exc_info=True)
        return image_binary # Return original image on error


# --- Main Preprocessing Function ---
def preprocess_image(img_pil: Image.Image) -> Image.Image:
    """Applies a preprocessing pipeline to a PIL Image object using Scikit-image.

    Pipeline: Deskew -> Grayscale -> Median -> CLAHE -> Sauvola -> Crop Borders

    Args:
        img_pil: The input PIL Image object.

    Returns:
        A new PIL Image object with preprocessing applied.
    """
    # ...(Input validation remains the same)...
    if not isinstance(img_pil, Image.Image):
        msg = "Invalid input type for preprocess_image: Expected PIL Image."; logger.error(msg); raise TypeError(msg)
    logger.info(f"Preprocessing image (mode: {img_pil.mode}, size: {img_pil.size})...")

    # --- Convert PIL Image to NumPy array ---
    # ...(Conversion logic remains the same)...
    try:
        img_array = np.array(img_pil); img_float = img_as_float(img_array[:,:,:3] if img_array.ndim == 3 and img_array.shape[2] == 4 else img_array)
        logger.debug(f"Converted PIL to NumPy array (shape: {img_float.shape}, dtype: {img_float.dtype}).")
    except Exception as e: logger.error(f"Error converting PIL to NumPy: {e}", exc_info=True); raise

    processed_img = img_float

    # --- Step 1: Convert to Grayscale (Needed for Deskewing) ---
    # ...(Grayscale logic remains the same)...
    if processed_img.ndim == 3:
        logger.debug("Converting to grayscale for deskewing..."); processed_img_gray = rgb2gray(processed_img)
    else: processed_img_gray = processed_img
    if processed_img_gray.dtype != np.float64 and processed_img_gray.dtype != np.float32: processed_img_gray = img_as_float(processed_img_gray)

    # --- Step 2: Deskewing ---
    # ...(Deskewing logic remains the same)...
    logger.debug("Attempting deskewing...")
    try:
        skew_angle = estimate_skew_angle(processed_img_gray)
        if abs(skew_angle) > 0.1:
            logger.info(f"Estimated skew angle: {skew_angle:.2f} degrees. Rotating...")
            processed_img = rotate(processed_img, skew_angle, resize=True, mode='constant', cval=1.0, order=1)
            # Update grayscale version if rotation happened
            processed_img_gray = rgb2gray(processed_img) if processed_img.ndim == 3 else processed_img
        else: logger.debug("Skew angle not significant. Skipping rotation.")
    except Exception as e: logger.warning(f"Deskewing failed: {e}", exc_info=True) # Continue with potentially skewed gray image

    # --- Step 3: Median Filter ---
    # ...(Median filter logic remains the same, input is processed_img_gray)...
    logger.debug("Applying Median Filter...")
    try:
        with np.errstate(invalid='ignore'): img_uint8_med = img_as_ubyte(processed_img_gray)
        processed_img_median = median(img_uint8_med, footprint=disk(1))
        processed_img = img_as_float(processed_img_median) # Result is float grayscale
    except Exception as e: logger.warning(f"Median Filter failed: {e}", exc_info=True); processed_img = processed_img_gray

    # --- Step 4: CLAHE ---
    # ...(CLAHE logic remains the same, input is processed_img from median)...
    logger.debug("Applying CLAHE...")
    try: processed_img = equalize_adapthist(processed_img, clip_limit=0.01)
    except Exception as e: logger.warning(f"CLAHE failed: {e}", exc_info=True) # Continue with image before CLAHE

    # --- Step 5: Binarization (Sauvola) ---
    # ...(Sauvola logic remains the same, input is processed_img from CLAHE)...
    logger.debug("Applying Sauvola Binarization...")
    try:
        window_size = 15; k = 0.2
        if processed_img.dtype != np.float64 and processed_img.dtype != np.float32: processed_img_float_bin = img_as_float(processed_img)
        else: processed_img_float_bin = processed_img
        thresh_sauvola = threshold_sauvola(processed_img_float_bin, window_size=window_size, k=k)
        binary_sauvola = processed_img_float_bin > thresh_sauvola
        processed_img_binary = img_as_ubyte(binary_sauvola) # Result is uint8 binary (0/255)
        logger.debug(f"Applied Sauvola Binarization (window={window_size}, k={k}).")
    except Exception as e:
        logger.warning(f"Sauvola Binarization failed: {e}", exc_info=True)
        # Fallback: Convert current processed_img to uint8 binary using simple threshold
        try:
            if np.max(processed_img) <= 1.0 and np.min(processed_img) >= 0.0: processed_img_binary = img_as_ubyte(processed_img > 0.5)
            else: processed_img_binary = processed_img.astype(np.uint8)
            logger.warning("Using fallback uint8 conversion after binarization failure.")
        except Exception as fallback_e: logger.error(f"Fallback uint8 conversion failed: {fallback_e}", exc_info=True); raise

    # --- Step 6: Crop Borders ---
    # Apply cropping to the binary image result from Step 5
    processed_img_cropped = crop_border(processed_img_binary, padding=5) # Use the helper function

    # --- Convert final NumPy array back to PIL Image ---
    # Use the cropped image result
    logger.debug(f"Converting final NumPy array (shape: {processed_img_cropped.shape}, dtype: {processed_img_cropped.dtype}) back to PIL Image...")
    try:
        # Ensure uint8
        if processed_img_cropped.dtype != np.uint8:
            logger.error(f"Cropped image array is not uint8 ({processed_img_cropped.dtype})!")
            processed_img_final = img_as_ubyte(processed_img_cropped)
        else:
            processed_img_final = processed_img_cropped
        final_pil_image = Image.fromarray(processed_img_final)
        logger.info(f"Preprocessing complete (incl. cropping). Final PIL Image mode: {final_pil_image.mode}")
        return final_pil_image
    except Exception as e:
        logger.error(f"Error converting final NumPy array to PIL Image: {e}", exc_info=True)
        raise

# Example usage block (remains the same)
if __name__ == "__main__":
    # ...(Testing block remains unchanged)...
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger.info("--- Running image_processor.py directly for testing ---")
    test_image_dir = "temp_test_loader"; test_image_path = os.path.join(test_image_dir, "test_loader_image.webp")
    processed_image_path = os.path.join(test_image_dir, "processed_skimage_test_image.png")
    if os.path.exists(test_image_path):
        logger.info(f"Loading test image: {test_image_path}")
        input_image = None; processed_image = None
        try:
            input_image = Image.open(test_image_path); input_image.load()
            logger.info(f"Input image loaded: mode={input_image.mode}, size={input_image.size}")
            processed_image = preprocess_image(input_image)
            logger.info(f"Saving processed image to: {processed_image_path}")
            processed_image.save(processed_image_path, format="PNG")
            logger.info(f"Test processing complete. Check the output image: {processed_image_path}")
        except FileNotFoundError: logger.error(f"Test image not found at {test_image_path}")
        except ImportError: logger.error("scikit-image not installed. Cannot run test.")
        except Exception as e: logger.error(f"An error occurred during testing: {e}", exc_info=True)
        finally:
            if input_image: input_image.close()
            if processed_image: processed_image.close()
            logger.info(f"(Remember to manually clean up '{test_image_dir}' directory if needed)")
    else:
        logger.warning(f"Test image not found at '{test_image_path}'.")
    logger.info("--- Image Processor Test Complete ---")