"""
Audio Processing Module — Main orchestrator.

Combines Whisper speech-to-text and Librosa prosody analysis into a
single, clean AudioProcessor class with async-compatible interface.

Architecture:
    AudioProcessor (this file)
    ├── WhisperTranscriber  — STT with word timestamps
    └── ProsodyAnalyzer     — Pitch, energy, silence metrics

Design Principles:
    - Lazy loading: ML models only load on first use
    - Graceful degradation: works with partial dependencies
    - Non-blocking: async wrapper runs CPU-bound work in thread pool
    - Never raises: all errors handled internally, returns empty structures

Output Schema:
    {
        "status": "success" | "partial" | "error",
        "errors": [str],
        "transcript": { ... },     # From WhisperTranscriber
        "prosody": { ... },        # From ProsodyAnalyzer
        "speech_features": {
            "speech_rate_wpm": float,
            "speech_rate_wps": float,
            "total_words": int,
            "total_duration_sec": float,
            "speech_duration_sec": float,
            "filler_words": {
                "count": int,
                "rate_per_minute": float,
                "found": [str],
                "details": {"um": int, "uh": int, ...}
            },
            "response_latency_ms": float,
            "avg_segment_length_words": float
        }
    }
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Thread pool for CPU-bound audio processing
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="audio")

# ── Filler Word Dictionary ───────────────────────────
# Common disfluencies tracked in psychiatric speech analysis
FILLER_WORDS = [
    "um", "uh", "uhm", "hmm",
    "like", "you know", "basically", "actually",
    "i mean", "sort of", "kind of", "right",
]


class AudioProcessor:
    """
    Processes audio files to extract speech features relevant to
    psychiatric evaluation.

    Pipeline:
        Audio File (.wav/.mp4/.webm)
        │
        ├─► Whisper STT ──► Transcript + Word Timestamps
        │
        ├─► Librosa ──────► Pitch, Energy, Silence, Pauses
        │
        └─► Feature Calc ─► Speech Rate, Fillers, Latency
                │
                ▼
        Structured JSON Output

    Usage:
        processor = AudioProcessor()
        result = await processor.process(audio_path)
        # or synchronously:
        result = processor.process_sync(audio_path)
    """

    def __init__(self, whisper_model_size: str = "base"):
        """
        Args:
            whisper_model_size: Whisper variant — "tiny", "base", "small", "medium", "large"
        """
        self.whisper_model_size = whisper_model_size
        self._transcriber = None
        self._prosody_analyzer = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Lazy initialization of sub-modules.
        Called automatically on first process() call.

        Returns:
            True if at least one sub-module initialized successfully.
        """
        if self._initialized:
            return True

        errors = []

        # Initialize Whisper transcriber
        try:
            from app.modules.audio.transcriber import WhisperTranscriber
            self._transcriber = WhisperTranscriber(model_size=self.whisper_model_size)
            loaded = self._transcriber.load_model()
            if not loaded:
                errors.append("Whisper model failed to load")
                self._transcriber = None
        except ImportError:
            errors.append("openai-whisper not installed")
            self._transcriber = None

        # Initialize prosody analyzer (no heavy model — always available if librosa exists)
        try:
            from app.modules.audio.prosody import ProsodyAnalyzer
            self._prosody_analyzer = ProsodyAnalyzer()
        except ImportError:
            errors.append("librosa not installed")
            self._prosody_analyzer = None

        self._initialized = True

        if errors:
            logger.warning(f"AudioProcessor partial init: {'; '.join(errors)}")
        else:
            logger.info("AudioProcessor fully initialized")

        return self._transcriber is not None or self._prosody_analyzer is not None

    # ── Async Interface ──────────────────────────────

    async def process(self, audio_path: str, language: Optional[str] = None) -> Dict:
        """
        Process an audio file asynchronously.
        Offloads CPU-bound Whisper/Librosa work to a thread pool.

        Args:
            audio_path: Path to audio file
            language: Optional language code for Whisper

        Returns:
            Structured analysis result (see module docstring for schema)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self.process_sync,
            audio_path,
            language,
        )

    # ── Synchronous Interface ────────────────────────

    def process_sync(self, audio_path: str, language: Optional[str] = None) -> Dict:
        """
        Process an audio file synchronously.

        Args:
            audio_path: Path to audio file
            language: Optional language code for Whisper

        Returns:
            Structured analysis result (see module docstring for schema)
        """
        # Validate input
        if not audio_path or not os.path.isfile(audio_path):
            return self._error_result(f"File not found: {audio_path}")

        # Ensure initialization
        if not self._initialized:
            self.initialize()

        errors = []
        transcript = None
        prosody = None

        # ── Step 1: Transcribe with Whisper ──────────
        if self._transcriber and self._transcriber.is_available:
            try:
                transcript = self._transcriber.transcribe(audio_path, language=language)
                logger.info(f"Transcription: {transcript.get('segment_count', 0)} segments")
            except Exception as e:
                errors.append(f"Transcription error: {e}")
                logger.error(f"Transcription failed: {e}", exc_info=True)
        else:
            errors.append("Whisper transcriber not available")

        # ── Step 2: Prosody Analysis with Librosa ────
        if self._prosody_analyzer:
            try:
                prosody = self._prosody_analyzer.analyze(audio_path)
                logger.info(f"Prosody: pitch_mean={prosody.get('pitch', {}).get('mean_hz', 0):.1f}Hz")
            except Exception as e:
                errors.append(f"Prosody error: {e}")
                logger.error(f"Prosody analysis failed: {e}", exc_info=True)
        else:
            errors.append("Prosody analyzer not available")

        # Use empty defaults if either module failed
        if transcript is None:
            from app.modules.audio.transcriber import WhisperTranscriber
            transcript = WhisperTranscriber._empty_result()

        if prosody is None:
            from app.modules.audio.prosody import ProsodyAnalyzer
            prosody = ProsodyAnalyzer._empty_result()

        # ── Step 3: Calculate Speech Features ────────
        speech_features = self._calculate_speech_features(transcript, prosody)

        # Determine overall status
        if not errors:
            status = "success"
        elif transcript.get("segment_count", 0) > 0 or prosody.get("duration_sec", 0) > 0:
            status = "partial"
        else:
            status = "error"

        return {
            "status": status,
            "errors": errors,
            "transcript": transcript,
            "prosody": prosody,
            "speech_features": speech_features,
        }

    # ── Feature Calculation ──────────────────────────

    def _calculate_speech_features(self, transcript: Dict, prosody: Dict) -> Dict:
        """
        Calculate high-level speech features from raw transcript and prosody data.

        Features:
            - Speech rate (WPM and WPS)
            - Filler word detection with frequency and per-word breakdown
            - Response latency (time before first speech)
            - Average segment length
        """
        segments = transcript.get("segments", [])
        full_text = transcript.get("text", "").lower()
        total_duration = max(
            transcript.get("duration_sec", 0),
            prosody.get("duration_sec", 0),
            0.01,  # Avoid division by zero
        )

        # ── Word Count ────────────────────────────
        words = full_text.split()
        total_words = len(words)

        # ── Speech Rate ───────────────────────────
        speech_duration = prosody.get("silence", {}).get("speech_duration_sec", total_duration)
        speech_duration = max(speech_duration, 0.01)

        speech_rate_wpm = (total_words / speech_duration) * 60
        speech_rate_wps = total_words / speech_duration

        # ── Filler Word Detection ─────────────────
        filler_details = {}
        filler_total = 0
        for fw in FILLER_WORDS:
            # Count occurrences (multi-word fillers need phrase search)
            if " " in fw:
                count = full_text.count(fw)
            else:
                count = words.count(fw)

            if count > 0:
                filler_details[fw] = count
                filler_total += count

        filler_rate = (filler_total / max(total_duration / 60, 0.01))

        # ── Response Latency ──────────────────────
        # Time from start of audio to first speech segment
        response_latency_ms = 0.0
        if segments:
            response_latency_ms = segments[0].get("start", 0.0) * 1000

        # ── Average Segment Length ────────────────
        segment_word_counts = []
        for seg in segments:
            seg_words = len(seg.get("text", "").split())
            segment_word_counts.append(seg_words)

        avg_segment_length = (
            sum(segment_word_counts) / len(segment_word_counts)
            if segment_word_counts else 0.0
        )

        return {
            "speech_rate_wpm": round(speech_rate_wpm, 1),
            "speech_rate_wps": round(speech_rate_wps, 2),
            "total_words": total_words,
            "total_duration_sec": round(total_duration, 3),
            "speech_duration_sec": round(speech_duration, 3),
            "filler_words": {
                "count": filler_total,
                "rate_per_minute": round(filler_rate, 2),
                "found": list(filler_details.keys()),
                "details": filler_details,
            },
            "response_latency_ms": round(response_latency_ms, 1),
            "avg_segment_length_words": round(avg_segment_length, 1),
        }

    # ── Error Handling ───────────────────────────────

    @staticmethod
    def _error_result(error_msg: str) -> Dict:
        """Return error result structure."""
        from app.modules.audio.transcriber import WhisperTranscriber
        from app.modules.audio.prosody import ProsodyAnalyzer

        return {
            "status": "error",
            "errors": [error_msg],
            "transcript": WhisperTranscriber._empty_result(),
            "prosody": ProsodyAnalyzer._empty_result(),
            "speech_features": {
                "speech_rate_wpm": 0.0,
                "speech_rate_wps": 0.0,
                "total_words": 0,
                "total_duration_sec": 0.0,
                "speech_duration_sec": 0.0,
                "filler_words": {
                    "count": 0,
                    "rate_per_minute": 0.0,
                    "found": [],
                    "details": {},
                },
                "response_latency_ms": 0.0,
                "avg_segment_length_words": 0.0,
            },
        }
