"""
Text Extractor
==============
Handles extraction of raw text from PDF and DOCX files.
Preserves page numbers (for PDF) and section headings (for DOCX).
"""

import fitz  # PyMuPDF
import docx


class TextExtractor:
    """Extracts text from documents."""

    @staticmethod
    def extract_from_pdf(file_path: str) -> list[dict]:
        """
        Extract text from a PDF file page by page.
        
        Returns:
            list[dict]: A list of dictionaries representing pages:
                {"page_number": int, "text": str, "needs_ocr": bool, "word_count": int}
        """
        pages = []
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            text = page.get_text()
            clean_text = text.strip() if text else ""
            
            # Simple heuristic: if text is empty, it might be a scanned page needing OCR
            needs_ocr = bool(not clean_text)
            word_count = len(clean_text.split()) if clean_text else 0
            
            pages.append({
                "page_number": i + 1,
                "text": clean_text,
                "needs_ocr": needs_ocr,
                "word_count": word_count
            })
            
        return pages

    @staticmethod
    def extract_from_docx(file_path: str) -> list[dict]:
        """
        Extract text from a DOCX file section by section.
        Groups paragraphs into logical sections separated by headings.
        
        Returns:
            list[dict]: A list of dictionaries representing sections:
                {"section_index": int, "heading": str | None, "text": str, "word_count": int}
        """
        sections = []
        doc = docx.Document(file_path)
        
        current_heading = None
        current_text_blocks = []
        section_index = 1
        
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
                
            style_name = p.style.name if p.style else ""
            
            # Identify headings
            if style_name.startswith("Heading"):
                # Save previous section if there's any content
                if current_text_blocks:
                    combined_text = "\n".join(current_text_blocks)
                    sections.append({
                        "section_index": section_index,
                        "heading": current_heading,
                        "text": combined_text,
                        "word_count": len(combined_text.split())
                    })
                    section_index += 1
                
                # Start new section
                current_heading = text
                current_text_blocks = []
            else:
                current_text_blocks.append(text)
                
        # Flush the last section
        if current_text_blocks:
            combined_text = "\n".join(current_text_blocks)
            sections.append({
                "section_index": section_index,
                "heading": current_heading,
                "text": combined_text,
                "word_count": len(combined_text.split())
            })
            
        return sections
