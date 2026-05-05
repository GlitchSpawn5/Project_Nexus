"""
Image Extractor
===============
Extracts metadata and embedded text (via OCR) from an image file.
"""

import os
import logging
from PIL import Image

try:
    import pytesseract
    TESSERACT_INSTALLED = True
except ImportError:
    TESSERACT_INSTALLED = False

from app.config import settings

logger = logging.getLogger(__name__)

class ImageExtractor:
    """Extracts metadata and OCR text from images."""

    @staticmethod
    def extract(file_path: str) -> dict:
        """
        Extract metadata and OCR text from an image.
        Never crashes; catches all errors and returns empty metadata if failed.
        
        Args:
            file_path (str): The absolute path to the image file.
            
        Returns:
            dict: {"width": int, "height": int, "format": str, "mode": str, 
                   "file_size_bytes": int, "has_transparency": bool, "ocr_text": str}
        """
        metadata = {
            "width": 0,
            "height": 0,
            "format": "unknown",
            "mode": "unknown",
            "file_size_bytes": 0,
            "has_transparency": False,
            "ocr_text": ""
        }
        
        try:
            # File size
            if os.path.exists(file_path):
                metadata["file_size_bytes"] = os.path.getsize(file_path)
                
            # Image metadata
            with Image.open(file_path) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["format"] = img.format or "unknown"
                metadata["mode"] = img.mode
                
                # Check for transparency
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    metadata["has_transparency"] = True
                    
                # Run OCR if available and enabled
                if settings.TESSERACT_AVAILABLE and TESSERACT_INSTALLED:
                    try:
                        # Convert to RGB for better OCR reliability if it has transparency
                        ocr_img = img.convert("RGB") if metadata["has_transparency"] else img
                        ocr_text = pytesseract.image_to_string(ocr_img).strip()
                        metadata["ocr_text"] = ocr_text
                    except Exception as ocr_err:
                        logger.warning(f"OCR failed for {file_path}: {ocr_err}")
                        
        except Exception as e:
            logger.warning(f"Failed to extract image metadata for {file_path}: {e}")
            
        return metadata
