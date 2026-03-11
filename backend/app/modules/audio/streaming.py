"""
StreamingAudioProcessor — enhanced real-time audio chunk processor.

For each ~3s PCM chunk:
  1. Whisper transcription (in executor, non-blocking)
  2. Acoustic feature extraction:
     - Pitch (F0) mean & variance via pYIN
     - RMS energy + dB energy
     - Silence ratio
     - Individual pause detection with timestamps
     - Speech rate (WPM)
  3. Returns StreamAudioResult for the chunk

Designed to run in a ThreadPoolExecutor (CPU-bound).
"""

import numpy as np
import logging
import time
from typing import Optional, List, Tuple

from app.schemas.streaming import (
    StreamAudioResult,
    StreamTranscript,
    StreamAudioFeatures,
    PauseDetail,
)
from app.core.config import (
    AUDIO_SAMPLE_RATE,
    WHISPER_MODEL_SIZE,
    PAUSE_MIN_DURATION_SEC,
    PAUSE_SILENCE_TOP_DB,
)

logger = logging.getLogger(__name__)


class StreamingAudioProcessor:
    """
    Processes buffered audio chunks (~3 seconds) for:
    1. Speech-to-text via Whisper (chunked inference)
    2. Rich acoustic feature extraction via librosa
    """

    def __init__(self):
        self._whisper_model = None
        self.available = False

    # ── Model Lifecycle ─────────────────────────────────────

    def preload(self):
        """Pre-load the Whisper model at startup (called once)."""
        try:
            import whisper
            logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}'...")
            self._whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
            self.available = True
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper: {e}")
            self.available = False

    # ── Main Entry Point ────────────────────────────────────

    def process_chunk(
        self, pcm_bytes: bytes, segment_id: int
    ) -> Optional[StreamAudioResult]:
        """
        Process a chunk of raw PCM float32 audio.
        This method is BLOCKING — run it in an executor.

        Args:
            pcm_bytes: raw float32 PCM at 16kHz mono
            segment_id: incrementing segment counter

        Returns:
            StreamAudioResult with transcript + acoustic features, or None
        """
        if not self.available or self._whisper_model is None:
            logger.warning("Whisper model not available, skipping audio chunk.")
            return None

        try:
            # Convert bytes → numpy float32 array
            audio_np = np.frombuffer(pcm_bytes, dtype=np.float32).copy()

            if len(audio_np) < AUDIO_SAMPLE_RATE * 0.5:
                return None  # less than 0.5s — skip

            chunk_duration = len(audio_np) / AUDIO_SAMPLE_RATE

            # 1. Whisper transcription (blocking)
            transcript_text = self._transcribe(audio_np)
            word_count = len(transcript_text.split()) if transcript_text else 0

            # 2. Full acoustic feature extraction
            features = self._extract_features(
                audio_np, transcript_text, chunk_duration
            )

            return StreamAudioResult(
                transcript=StreamTranscript(
                    text=transcript_text,
                    segment_id=segment_id,
                    is_partial=False,
                    word_count=word_count,
                ),
                features=features,
            )
        except Exception as e:
            logger.error(f"Audio chunk processing failed: {e}", exc_info=True)
            return None

    # ── Whisper Transcription ───────────────────────────────

    def _transcribe(self, audio_np: np.ndarray) -> str:
        """Run Whisper on a numpy float32 array (16kHz mono)."""
        result = self._whisper_model.transcribe(
            audio_np,
            language="en",
            fp16=False,  # CPU-safe
        )
        return result.get("text", "").strip()

    # ── Feature Extraction ──────────────────────────────────

    def _extract_features(
        self, audio_np: np.ndarray, transcript: str, chunk_duration: float
    ) -> StreamAudioFeatures:
        """
        Extract all acoustic features from one audio chunk:
          - Pitch (F0) mean & std via pYIN
          - RMS energy & dB energy
          - Silence ratio
          - Individual pauses (with start/end/duration)
          - Speech rate (WPM)
          - Hesitation markers (filler words)
        """
        import librosa

        sr = AUDIO_SAMPLE_RATE

        # ── Pitch (F0) via pYIN ─────────────────────────────
        pitch_mean, pitch_std = self._extract_pitch(audio_np, sr)

        # ── Energy (RMS & dB) ───────────────────────────────
        energy_rms, energy_db = self._extract_energy(audio_np)

        # ── Silence & Pause Detection ───────────────────────
        silence_ratio, pauses = self._detect_pauses(audio_np, sr, chunk_duration)

        # ── Speech Rate ─────────────────────────────────────
        word_count = len(transcript.split()) if transcript else 0
        speech_rate = (
            (word_count / (chunk_duration / 60.0)) if chunk_duration > 0 else 0.0
        )

        # ── Hesitation Markers ──────────────────────────────
        hesitation_count, hesitation_ratio = self._detect_hesitations(transcript, word_count)

        return StreamAudioFeatures(
            pitch_mean=round(pitch_mean, 2),
            pitch_std=round(pitch_std, 2),
            energy_rms=round(energy_rms, 6),
            energy_db=round(energy_db, 2),
            silence_ratio=round(silence_ratio, 3),
            speech_rate_wpm=round(speech_rate, 1),
            pause_count=len(pauses),
            pauses=pauses,
            word_count=word_count,
            chunk_duration=round(chunk_duration, 2),
            hesitation_count=hesitation_count,
            hesitation_ratio=round(hesitation_ratio, 3),
        )

    # ── Pitch ───────────────────────────────────────────────

    @staticmethod
    def _extract_pitch(audio_np: np.ndarray, sr: int) -> Tuple[float, float]:
        """Extract fundamental frequency (F0) mean and std deviation."""
        import librosa

        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio_np,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=sr,
            )
            valid_f0 = f0[~np.isnan(f0)]
            if len(valid_f0) > 0:
                return float(np.mean(valid_f0)), float(np.std(valid_f0))
        except Exception as e:
            logger.debug(f"Pitch extraction failed: {e}")
        return 0.0, 0.0

    # ── Energy ──────────────────────────────────────────────

    @staticmethod
    def _extract_energy(audio_np: np.ndarray) -> Tuple[float, float]:
        """
        Compute RMS energy and dB energy for the chunk.
        RMS is the raw amplitude measure; dB uses 20*log10(rms).
        """
        rms = float(np.sqrt(np.mean(audio_np ** 2)))
        # Avoid log(0)
        db = float(20 * np.log10(rms + 1e-10))
        return rms, db

    # ── Pause Detection ─────────────────────────────────────

    @staticmethod
    def _detect_pauses(
        audio_np: np.ndarray, sr: int, chunk_duration: float
    ) -> Tuple[float, List[PauseDetail]]:
        """
        Detect pauses (silent intervals) within the chunk.

        Returns:
            (silence_ratio, list_of_PauseDetail)
        """
        import librosa

        try:
            # Split audio into non-silent intervals
            non_silent = librosa.effects.split(
                audio_np, top_db=PAUSE_SILENCE_TOP_DB
            )

            if len(non_silent) == 0:
                # Entire chunk is silence
                return 1.0, [
                    PauseDetail(
                        start_sec=0.0,
                        end_sec=round(chunk_duration, 3),
                        duration_sec=round(chunk_duration, 3),
                    )
                ]

            # Compute silence ratio
            non_silent_dur = sum((e - s) / sr for s, e in non_silent)
            silence_ratio = max(0.0, 1.0 - (non_silent_dur / chunk_duration))

            # Find gaps between non-silent segments → pauses
            pauses: List[PauseDetail] = []
            for i in range(1, len(non_silent)):
                gap_start = non_silent[i - 1][1] / sr   # end of previous segment
                gap_end = non_silent[i][0] / sr          # start of next segment
                gap_dur = gap_end - gap_start

                if gap_dur >= PAUSE_MIN_DURATION_SEC:
                    pauses.append(PauseDetail(
                        start_sec=round(gap_start, 3),
                        end_sec=round(gap_end, 3),
                        duration_sec=round(gap_dur, 3),
                    ))

            return silence_ratio, pauses

        except Exception as e:
            logger.debug(f"Pause detection failed: {e}")
            return 0.0, []

    # ── Hesitation Markers ──────────────────────────────────

    @staticmethod
    def _detect_hesitations(transcript: str, word_count: int) -> Tuple[int, float]:
        """
        Count filler/hesitation words in transcript.

        Returns:
            (hesitation_count, hesitation_ratio)
        """
        if not transcript or word_count == 0:
            return 0, 0.0

        import re
        text_lower = transcript.lower()

        # Multi-word fillers (check first)
        MULTI_WORD_FILLERS = ["you know", "i mean", "sort of", "kind of"]
        count = 0
        for filler in MULTI_WORD_FILLERS:
            count += len(re.findall(r'\b' + re.escape(filler) + r'\b', text_lower))

        # Single-word fillers
        SINGLE_FILLERS = {"um", "uh", "uhm", "hmm", "hm", "er", "ah", "like", "well", "so"}
        words = re.findall(r'\b\w+\b', text_lower)
        for w in words:
            if w in SINGLE_FILLERS:
                count += 1

        ratio = count / word_count if word_count > 0 else 0.0
        return count, ratio
