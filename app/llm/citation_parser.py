import re
import logging

logger = logging.getLogger(__name__)

class CitationParser:
    def __init__(self):
        # Matches [SOURCE: 1234-abcd-...]
        self.citation_pattern = re.compile(r'\[SOURCE:\s*([a-fA-F0-9\-]+)\]')
        
    def _format_timestamp(self, seconds: float | None) -> str:
        if seconds is None:
            return ""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

    def parse(self, raw_answer: str, chunks: list[dict]) -> dict:
        """Parse raw LLM response for inline citations, replacing them with [1], [2], etc."""
        clean_answer = raw_answer.strip()
        
        # Check for INSUFFICIENT_EVIDENCE
        if clean_answer.startswith("INSUFFICIENT_EVIDENCE") or "INSUFFICIENT_EVIDENCE" in clean_answer:
            return {
                "answer_text": "",
                "annotated_answer": "",
                "cited_chunks": [],
                "citation_count": 0,
                "insufficient_evidence": True
            }

        # Build lookup dict from chunk_id -> chunk
        chunk_lookup = {c.get("chunk_id"): c for c in chunks}
        
        # Find all citation markers
        matches = self.citation_pattern.findall(clean_answer)
        
        # Deduplicate while preserving order of first appearance
        unique_cited_ids = []
        for match in matches:
            if match not in unique_cited_ids:
                unique_cited_ids.append(match)
                
        cited_chunks = []
        annotated_answer = clean_answer
        
        label_index = 1
        for chunk_id in unique_cited_ids:
            if chunk_id in chunk_lookup:
                chunk = chunk_lookup[chunk_id]
                label = f"[{label_index}]"
                
                cited_chunks.append({
                    "chunk_id": chunk_id,
                    "citation_label": label,
                    "modality": chunk.get("modality", "unknown"),
                    "filename": chunk.get("filename", "unknown"),
                    "page_number": chunk.get("page_number"),
                    "timestamp_start": chunk.get("timestamp_start"),
                    "timestamp_end": chunk.get("timestamp_end"),
                    "section_heading": chunk.get("section_heading")
                })
                
                # Replace all occurrences of this chunk_id's citation with the label
                # Use regex sub to ensure we match exactly the source block, including possible spaces
                replace_pattern = re.compile(rf'\[SOURCE:\s*{re.escape(chunk_id)}\]')
                annotated_answer = replace_pattern.sub(label, annotated_answer)
                
                label_index += 1
            else:
                logger.warning(f"[CitationParser] Unresolvable chunk ID in citation: {chunk_id}")
                # Remove unresolvable markers silently
                replace_pattern = re.compile(rf'\[SOURCE:\s*{re.escape(chunk_id)}\]')
                annotated_answer = replace_pattern.sub("", annotated_answer)
                
        # Remove remaining malformed markers if any (e.g., if there were ones we didn't catch due to formatting)
        annotated_answer = self.citation_pattern.sub("", annotated_answer).strip()

        # Generate a clean answer without ANY citation labels for downstream tasks if needed
        # We can just remove the [1], [2] labels from the annotated answer.
        # But wait, user requested answer_text: clean answer, no markers
        # We can strip [1]... out of annotated answer, or strip [SOURCE: ...] out of raw answer
        answer_text = self.citation_pattern.sub("", clean_answer).strip()
        
        return {
            "answer_text": answer_text,
            "annotated_answer": annotated_answer,
            "cited_chunks": cited_chunks,
            "citation_count": len(cited_chunks),
            "insufficient_evidence": False
        }

    def format_citation_list(self, cited_chunks: list[dict]) -> str:
        """Returns a clean numbered reference section."""
        if not cited_chunks:
            return "No sources cited."
            
        lines = []
        for cite in cited_chunks:
            label = cite["citation_label"]
            filename = cite["filename"]
            modality = cite["modality"]
            
            location = ""
            if modality == "text":
                if cite.get("page_number"):
                    location = f"Page {cite['page_number']}"
                elif cite.get("section_heading"):
                    location = f"Section: {cite['section_heading']}"
            elif modality == "audio" or modality == "video":
                start = self._format_timestamp(cite.get("timestamp_start"))
                end = self._format_timestamp(cite.get("timestamp_end"))
                if start and end:
                    location = f"{start} → {end}"
                elif start:
                    location = f"{start}"
            elif modality == "image":
                location = "Image"
                
            if location:
                lines.append(f"{label} {filename} — {location}")
            else:
                lines.append(f"{label} {filename}")
                
        return "\n".join(lines)
