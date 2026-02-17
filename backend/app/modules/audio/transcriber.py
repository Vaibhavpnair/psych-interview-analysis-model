"""
Whisper Transcriber — OpenAI Whisper wrapper for speech-to-text.

Responsibilities:
    - Load local Whisper model (configurable size)
    - Transcribe audio with word-level timestamps
    - Extract per-segment metadata (start, end, text, word timings)
    - Detect spoken language automatically

Output Schema:
    {
        "text": str,              # Full transcript
        "language": str,          # Detected language code
        "duration_sec": float,    # Total audio duration
        "segments": [
            {
                "id": int,
                "start": float,
                "end": float,
                "text": str,
                "words": [{"word": str, "start": float, "end": float, "probability": float}],
                "avg_logprob": float,
                "no_speech_prob": float
            }
        ]
    }
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Transcribes audio using OpenAI Whisper (local model).
    Returns text with word-level timestamps for timeline synchronization.

    Thread Safety:
        NOT thread-safe. Each thread should use its own instance.
        For async usage, run in an executor (see AudioProcessor).
    """

    def __init__(self, model_size: str = "base"):
        """
        Args:
            model_size: Whisper model variant — "tiny", "base", "small", "medium", "large".
                        Larger models are more accurate but slower.
        """
        self.model_size = model_size
        self.model = None
        self._available = False

    def load_model(self) -> bool:
        """
        Load Whisper model into memory.

        Returns:
            True if model loaded successfully, False otherwise.
        """
        if self.model is not None:
            return True

        try:
            import whisper
            logger.info(f"Loading Whisper model '{self.model_size}'...")
            self.model = whisper.load_model(self.model_size)
            self._available = True
            logger.info(f"Whisper model '{self.model_size}' loaded successfully")
            return True
        except ImportError:
            logger.warning("openai-whisper not installed — transcription disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._available and self.model is not None

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict:
        """
        Transcribe an audio file with word-level timestamps.

        Args:
            audio_path: Absolute path to audio file (.wav, .mp4, .webm, .mp3)
            language: Optional language code (e.g., "en"). Auto-detected if None.

        Returns:
            Structured dict with full text, segments, word timings, and metadata.
            Returns empty result on failure (never raises).
        """
        if not self.is_available:
            if not self.load_model():
                return self._empty_result()

        try:
            logger.info(f"Transcribing: {audio_path}")

            # Build transcription options
            options = {
                "word_timestamps": True,
                "verbose": False,
            }
            if language:
                options["language"] = language

            result = self.model.transcribe(audio_path, **options)

            # Parse segments with word-level detail
            segments = []
            for seg in result.get("segments", []):
                words = []
                for w in seg.get("words", []):
                    words.append({
                        "word": w.get("word", "").strip(),
                        "start": round(w.get("start", 0.0), 3),
                        "end": round(w.get("end", 0.0), 3),
                        "probability": round(w.get("probability", 0.0), 3),
                    })

                segments.append({
                    "id": seg.get("id", 0),
                    "start": round(seg.get("start", 0.0), 3),
                    "end": round(seg.get("end", 0.0), 3),
                    "text": seg.get("text", "").strip(),
                    "words": words,
                    "avg_logprob": round(seg.get("avg_logprob", 0.0), 4),
                    "no_speech_prob": round(seg.get("no_speech_prob", 0.0), 4),
                })

            # Calculate total duration
            duration = segments[-1]["end"] if segments else 0.0

            transcript = {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "en"),
                "duration_sec": round(duration, 3),
                "segments": segments,
                "segment_count": len(segments),
            }

            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"{duration:.1f}s, language={transcript['language']}"
            )
            return transcript

        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            return self._empty_result()

    @staticmethod
    def _empty_result() -> Dict:
        """Return empty transcript structure (safe for downstream consumers)."""
        return {
            "text": "",
            "language": "unknown",
            "duration_sec": 0.0,
            "segments": [],
            "segment_count": 0,
        }
