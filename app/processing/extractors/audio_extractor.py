"""
Audio Extractor
===============
Wraps OpenAI Whisper for speech-to-text transcription with word-level timestamps,
and mutagen for audio file metadata extraction.
"""

import logging
import os
from typing import Optional

import torch
import whisper

from app.config import settings

logger = logging.getLogger(__name__)

# Ensure Whisper can locate ffmpeg for audio decoding.
# imageio-ffmpeg bundles a standalone binary with a non-standard name
# (e.g. ffmpeg-win-x86_64-v7.1.exe), so we monkeypatch whisper.audio
# to use the full path instead of relying on PATH lookups.
try:
    import imageio_ffmpeg as _ioff
    import whisper.audio as _wa
    import subprocess
    import numpy as np

    _FFMPEG_EXE = _ioff.get_ffmpeg_exe()

    def _patched_load_audio(file: str, sr: int = 16000):
        """Load audio using imageio-ffmpeg's bundled ffmpeg."""
        cmd = [
            _FFMPEG_EXE,
            "-nostdin",
            "-threads", "0",
            "-i", file,
            "-f", "s16le",
            "-ac", "1",
            "-acodec", "pcm_s16le",
            "-ar", str(sr),
            "-",
        ]
        out = subprocess.run(cmd, capture_output=True, check=True).stdout
        return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

    _wa.load_audio = _patched_load_audio
    logger.info(f"Whisper audio loader patched to use: {_FFMPEG_EXE}")
except ImportError:
    pass


class AudioExtractor:
    """Transcribes audio/video files using OpenAI Whisper and extracts metadata via mutagen."""

    def __init__(self):
        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_size = settings.WHISPER_MODEL
        logger.info(f"Loading Whisper model '{model_size}' on device: {self.device}")

        self.model = whisper.load_model(model_size, device=self.device)
        logger.info(f"Whisper model '{model_size}' loaded successfully on {self.device}")

    # ── Transcription ──────────────────────────────────────────────────────

    def transcribe(self, file_path: str) -> dict:
        """
        Transcribe an audio or video file with word-level timestamps.

        Args:
            file_path (str): Absolute path to the audio/video file.

        Returns:
            dict: Structured transcript with segments and word timestamps.

        Raises:
            ValueError: If the file cannot be decoded as audio.
        """
        try:
            result = self.model.transcribe(
                file_path,
                word_timestamps=True,
                verbose=False,
            )
        except Exception as e:
            raise ValueError(f"Failed to transcribe '{file_path}': {e}")

        # Build structured output
        language = result.get("language", "unknown")
        full_text = result.get("text", "").strip()

        segments = []
        for idx, seg in enumerate(result.get("segments", [])):
            words = []
            for w in seg.get("words", []):
                words.append({
                    "word": w.get("word", "").strip(),
                    "start": round(w.get("start", 0.0), 3),
                    "end": round(w.get("end", 0.0), 3),
                })

            segments.append({
                "segment_index": idx,
                "text": seg.get("text", "").strip(),
                "start": round(seg.get("start", 0.0), 3),
                "end": round(seg.get("end", 0.0), 3),
                "words": words,
            })

        # Derive total duration from the last segment end, or 0
        duration_seconds = segments[-1]["end"] if segments else 0.0

        return {
            "language": language,
            "duration_seconds": round(duration_seconds, 3),
            "full_text": full_text,
            "segments": segments,
        }

    # ── Metadata Extraction ────────────────────────────────────────────────

    @staticmethod
    def extract_metadata(file_path: str) -> dict:
        """
        Use mutagen to read audio file metadata.

        Returns safe defaults if mutagen cannot parse the file — never crashes.
        """
        defaults = {
            "duration_seconds": None,
            "sample_rate": None,
            "channels": None,
            "bitrate": None,
            "format": "unknown",
        }

        try:
            from mutagen import File as MutagenFile

            mf = MutagenFile(file_path)
            if mf is None:
                logger.warning(f"mutagen could not identify file: {file_path}")
                return defaults

            info = mf.info
            defaults["duration_seconds"] = round(info.length, 3) if hasattr(info, "length") else None
            defaults["sample_rate"] = getattr(info, "sample_rate", None)
            defaults["channels"] = getattr(info, "channels", None)

            # Bitrate is in bits/s for MP3; mutagen stores it differently per format
            bitrate = getattr(info, "bitrate", None)
            if bitrate is not None:
                defaults["bitrate"] = int(bitrate)

            # Derive format from the mutagen type name (e.g. "MP3", "FLAC", "OggVorbis")
            defaults["format"] = type(mf).__name__

        except Exception as e:
            logger.warning(f"mutagen metadata extraction failed for {file_path}: {e}")

        return defaults
