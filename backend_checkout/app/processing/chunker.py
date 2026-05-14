"""
Semantic Chunker
================
Splits text into chunks of roughly equal size (word count based) with overlap.
Preserves metadata such as page number (for PDFs) and section heading (for DOCX).
"""

class SemanticChunker:
    """Splits document pages/sections into semantic chunks."""

    @staticmethod
    def chunk(
        pages_or_sections: list[dict], 
        source_type: str, 
        chunk_size: int = 500, 
        overlap: int = 50
    ) -> list[dict]:
        """
        Splits text into chunks of approximately `chunk_size` words with `overlap` words.
        
        Args:
            pages_or_sections: Output from TextExtractor (pages or sections).
            source_type: "pdf" or "docx".
            chunk_size: Target number of words per chunk.
            overlap: Number of overlapping words from the previous chunk.
            
        Returns:
            list[dict]: List of chunk dicts.
        """
        chunks = []
        chunk_index = 0
        
        for item in pages_or_sections:
            text = item.get("text", "")
            if not text:
                continue
                
            page_number = item.get("page_number")
            section_heading = item.get("heading")
            
            words = text.split()
            total_words = len(words)
            
            # If the entire page/section is very small, just yield it as one chunk
            if total_words <= chunk_size:
                # Merge small chunks (<20 words) with the previous one if possible
                if total_words < 20 and chunks:
                    prev_chunk = chunks[-1]
                    # Only merge if it's the same page/section (for context safety)
                    can_merge = False
                    if source_type == "pdf" and prev_chunk.get("page_number") == page_number:
                        can_merge = True
                    elif source_type == "docx" and prev_chunk.get("section_heading") == section_heading:
                        can_merge = True
                        
                    if can_merge:
                        prev_chunk["text"] += "\n" + text
                        prev_chunk["word_count"] = len(prev_chunk["text"].split())
                        # Approximate character offset adjustments
                        prev_chunk["char_end"] += len("\n" + text)
                        continue
                
                # Otherwise, add as new chunk
                chunk_text = text
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "word_count": len(chunk_text.split()),
                    "page_number": page_number,
                    "section_heading": section_heading,
                    "char_start": 0,
                    "char_end": len(chunk_text)
                })
                chunk_index += 1
                continue
                
            # Larger text: apply sliding window (word-based)
            start_word = 0
            while start_word < total_words:
                end_word = min(start_word + chunk_size, total_words)
                chunk_words = words[start_word:end_word]
                chunk_text = " ".join(chunk_words)
                
                # Check for tiny leftover chunks at the end
                if len(chunk_words) < 20 and chunks:
                    prev_chunk = chunks[-1]
                    # Since we are within the same page/section, we can safely merge
                    prev_chunk["text"] += " " + chunk_text
                    prev_chunk["word_count"] = len(prev_chunk["text"].split())
                    prev_chunk["char_end"] += len(" " + chunk_text)
                    break # Reached the end, merging done
                
                # Calculate approximate char_start and char_end
                # Note: this is rough because we lose original whitespace during split/join
                # A more precise method would search for the exact substring
                if start_word == 0:
                    char_start = 0
                else:
                    char_start = len(" ".join(words[:start_word])) + 1
                    
                char_end = char_start + len(chunk_text)
                
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "word_count": len(chunk_words),
                    "page_number": page_number,
                    "section_heading": section_heading,
                    "char_start": char_start,
                    "char_end": char_end
                })
                chunk_index += 1
                
                # Advance the window
                start_word += (chunk_size - overlap)
                
        return chunks
