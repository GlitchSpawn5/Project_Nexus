import logging

logger = logging.getLogger(__name__)

class PromptBuilder:
    def build_system_prompt(self) -> str:
        return (
            "You are NEXUS, a precise research assistant. You answer questions strictly\n"
            "using the evidence chunks provided to you. Follow these rules without exception:\n\n"
            "1. Answer ONLY from the provided evidence. Never use outside knowledge.\n"
            "2. After every factual claim, add an inline citation in this exact format: [SOURCE: chunk_id]\n"
            "3. If the evidence does not contain enough information to answer, respond with\n"
            "   exactly this single word: INSUFFICIENT_EVIDENCE\n"
            "4. Do not speculate, infer beyond what is stated, or fill gaps with assumptions.\n"
            "5. Be concise. Do not repeat the question. Do not add a preamble."
        )

    def _format_timestamp(self, seconds: float | None) -> str:
        if seconds is None:
            return ""
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"

    def build_user_prompt(self, query: str, chunks: list[dict], evidence_chains: list[dict] | None = None) -> str:
        # Token budget management (approximate by word count)
        MAX_WORDS = 5000
        
        # Determine which chunks are part of evidence_chains so we never drop them
        protected_chunk_ids = set()
        if evidence_chains:
            for chain in evidence_chains:
                protected_chunk_ids.add(chain.get("root_chunk_id"))
                for linked in chain.get("linked_chunks", []):
                    protected_chunk_ids.add(linked.get("chunk_id"))

        total_words = sum(len(c.get("text", "").split()) for c in chunks)
        
        if total_words > MAX_WORDS:
            # Sort chunks by score (ascending) so we can drop lowest-scoring first
            # Assuming 'score' is in the dict, default to 0 if not present
            sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0.0))
            chunks_to_keep = []
            
            # Start keeping highest scoring, drop lowest until budget is met
            # Let's iterate from highest to lowest and accumulate words
            sorted_chunks.reverse() # Now highest to lowest
            
            accumulated_words = 0
            for chunk in sorted_chunks:
                chunk_words = len(chunk.get("text", "").split())
                is_protected = chunk.get("chunk_id") in protected_chunk_ids
                
                if accumulated_words + chunk_words <= MAX_WORDS or is_protected:
                    chunks_to_keep.append(chunk)
                    accumulated_words += chunk_words
                else:
                    # Skip this chunk as it exceeds budget and is not protected
                    pass
            
            num_dropped = len(chunks) - len(chunks_to_keep)
            if num_dropped > 0:
                logger.warning(f"[PromptBuilder] Truncated {num_dropped} chunks to fit token budget")
            
            chunks = chunks_to_keep

        # Now build the prompt string
        prompt_lines = [f"QUERY: {query}\n", "── EVIDENCE ──────────────────────────────────────────\n"]

        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            modality = chunk.get("modality", "unknown")
            filename = chunk.get("filename", "unknown")
            
            # Formatting location
            location = ""
            if modality == "text":
                if chunk.get("page_number"):
                    location = f"page {chunk['page_number']}"
                elif chunk.get("section_heading"):
                    location = f"section: {chunk['section_heading']}"
                else:
                    location = "document"
            elif modality == "audio" or modality == "video":
                start_fmt = self._format_timestamp(chunk.get("timestamp_start"))
                end_fmt = self._format_timestamp(chunk.get("timestamp_end"))
                if start_fmt and end_fmt:
                    location = f"{start_fmt} → {end_fmt}"
                elif start_fmt:
                    location = f"{start_fmt}"
                else:
                    location = "audio"
            elif modality == "image":
                location = "image"
            else:
                location = "unknown"

            text = chunk.get("text", "")
            
            prompt_lines.append(f"[CHUNK {chunk_id} | {modality} | {filename} | {location}]")
            prompt_lines.append(f"{text}\n")

        if evidence_chains:
            prompt_lines.append("── LINKED EVIDENCE (cross-modal connections) ─────────\n")
            for chain in evidence_chains:
                root_chunk_id = chain.get("root_chunk_id")
                for linked in chain.get("linked_chunks", []):
                    linked_id = linked.get("chunk_id")
                    link_type = linked.get("link_type", "unknown")
                    strength = linked.get("strength", 0.0)
                    text_preview = linked.get("text_preview", "")
                    
                    prompt_lines.append(f"[CHAIN {root_chunk_id} → {linked_id} | {link_type} | strength {strength:.2f}]")
                    prompt_lines.append(f"{text_preview}\n")
        
        prompt_lines.append("─────────────────────────────────────────────────────")
        prompt_lines.append("Answer the query using ONLY the evidence above.")
        prompt_lines.append("Cite every factual claim with [SOURCE: chunk_id].")

        return "\n".join(prompt_lines)
