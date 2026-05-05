"""
Language Detector
=================
Detects the ISO 639-1 language code from a document's text.
"""

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Ensure deterministic results
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """
    Detects language of the first 1000 characters of the document.
    Returns 'unknown' on failure.
    """
    if not text or not text.strip():
        return "unknown"
        
    sample_text = text[:1000].strip()
    try:
        lang_code = detect(sample_text)
        return lang_code
    except LangDetectException:
        return "unknown"
    except Exception:
        return "unknown"
