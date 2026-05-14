"""
Audio Chunker
=============
Groups Whisper transcript segments into fixed-size chunks with word-level overlap
and preserved timestamps. Merges tiny trailing chunks into the previous one.
"""

from typing import List

from app.config import settings


class AudioChunker:
    """Converts a list of Whisper segments into search-friendly chunks."""

    @staticmethod
    def chunk_segments(
        segments: List[dict],
        max_words: int | None = None,
        overlap_words: int | None = None,
    ) -> List[dict]:
        """
        Group segments into chunks of approximately *max_words* words each,
        with *overlap_words* carried from the previous chunk into the next.

        Chunks with fewer than 10 words are merged into the preceding chunk.

        Args:
            segments: List of segment dicts from AudioExtractor.transcribe().
            max_words: Target word count per chunk (default from config).
            overlap_words: Number of trailing words to carry forward (default from config).

        Returns:
            List of chunk dicts, each containing:
                chunk_index, text, timestamp_start, timestamp_end,
                word_count, segment_indices
        """
        if max_words is None:
            max_words = settings.AUDIO_MAX_WORDS_PER_CHUNK
        if overlap_words is None:
            overlap_words = settings.AUDIO_OVERLAP_WORDS

        if not segments:
            return []

        # ── 1. Flatten all words with their segment index ────────────────
        # Each item: (word_str, start, end, segment_index)
        all_words: list[tuple[str, float, float, int]] = []
        for seg in segments:
            for w in seg.get("words", []):
                all_words.append((
                    w["word"],
                    w["start"],
                    w["end"],
                    seg["segment_index"],
                ))

        if not all_words:
            # Edge case: Whisper returned segments but no word-level data.
            # Fall back to treating each segment as a chunk.
            chunks = []
            for seg in segments:
                words_in_seg = seg["text"].split()
                chunks.append({
                    "chunk_index": seg["segment_index"],
                    "text": seg["text"],
                    "timestamp_start": seg["start"],
                    "timestamp_end": seg["end"],
                    "word_count": len(words_in_seg),
                    "segment_indices": [seg["segment_index"]],
                })
            return chunks

        # ── 2. Build raw chunks by sliding a word window ─────────────────
        raw_chunks: list[dict] = []
        start_idx = 0  # index into all_words

        while start_idx < len(all_words):
            end_idx = min(start_idx + max_words, len(all_words))
            window = all_words[start_idx:end_idx]

            text = " ".join(w[0] for w in window)
            ts_start = window[0][1]
            ts_end = window[-1][2]
            seg_indices = sorted(set(w[3] for w in window))

            raw_chunks.append({
                "text": text,
                "timestamp_start": round(ts_start, 3),
                "timestamp_end": round(ts_end, 3),
                "word_count": len(window),
                "segment_indices": seg_indices,
            })

            # Advance by (max_words - overlap_words), but at least 1 word
            step = max(max_words - overlap_words, 1)
            start_idx += step

        # ── 3. Merge tiny trailing chunk (< 10 words) ────────────────────
        if len(raw_chunks) > 1 and raw_chunks[-1]["word_count"] < 10:
            last = raw_chunks.pop()
            prev = raw_chunks[-1]
            prev["text"] = prev["text"] + " " + last["text"]
            prev["timestamp_end"] = last["timestamp_end"]
            prev["word_count"] = len(prev["text"].split())
            prev["segment_indices"] = sorted(
                set(prev["segment_indices"]) | set(last["segment_indices"])
            )

        # ── 4. Assign chunk_index ────────────────────────────────────────
        for idx, chunk in enumerate(raw_chunks):
            chunk["chunk_index"] = idx

        return raw_chunks
