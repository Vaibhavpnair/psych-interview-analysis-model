"""
Prosody Analyzer — Librosa-based acoustic feature extraction.

Responsibilities:
    - Pitch (F0) extraction via pyin algorithm
    - Silence and pause detection with configurable thresholds
    - Energy/intensity envelope analysis
    - Jitter estimation (pitch-to-pitch variation)

Clinical Relevance:
    - Low pitch variance → emotional blunting / flat affect
    - High silence ratio → psychomotor retardation
    - Long pauses → processing delay, cognitive load
    - Low energy variance → monotone delivery

Output Schema:
    {
        "duration_sec": float,
        "pitch": {
            "mean_hz": float,
            "std_hz": float,
            "min_hz": float,
            "max_hz": float,
            "range_hz": float,
            "jitter": float,           # Frame-to-frame pitch instability
            "voiced_fraction": float    # % of frames with detectable pitch
        },
        "energy": {
            "mean_db": float,
            "std_db": float,
            "dynamic_range_db": float
        },
        "pauses": {
            "count": int,
            "total_duration_sec": float,
            "avg_duration_ms": float,
            "max_duration_ms": float,
            "long_pause_count": int     # Pauses > 2 seconds
        },
        "silence": {
            "ratio": float,            # silence / total duration
            "speech_duration_sec": float
        }
    }
"""
import logging
from typing import Dict

import numpy as np

logger = logging.getLogger(__name__)


class ProsodyAnalyzer:
    """
    Extracts acoustic/prosodic features from audio using Librosa.

    All methods are CPU-bound and synchronous. For async usage,
    run via asyncio.to_thread() or a ThreadPoolExecutor.
    """

    # Minimum pause duration to count (seconds)
    MIN_PAUSE_SEC = 0.2
    # Threshold for "long" pause (seconds)
    LONG_PAUSE_SEC = 2.0

    def __init__(self, sr: int = 22050, silence_threshold_db: float = -40.0):
        """
        Args:
            sr: Target sample rate for analysis.
            silence_threshold_db: dB threshold for silence detection (relative to peak).
        """
        self.sr = sr
        self.silence_threshold_db = silence_threshold_db

    def analyze(self, audio_path: str) -> Dict:
        """
        Extract all prosodic features from an audio file.

        Args:
            audio_path: Path to audio file (.wav, .mp4, .webm)

        Returns:
            Structured dict with pitch, energy, pause, and silence metrics.
            Returns empty result on failure (never raises).
        """
        try:
            import librosa

            # ── Load Audio ────────────────────────────
            y, sr = librosa.load(audio_path, sr=self.sr)
            duration = librosa.get_duration(y=y, sr=sr)

            if duration < 0.5:
                logger.warning(f"Audio too short ({duration:.2f}s), skipping prosody analysis")
                return self._empty_result(duration)

            # ── Pitch (F0) via pyin ───────────────────
            pitch_features = self._extract_pitch(y, sr)

            # ── Energy / Intensity ────────────────────
            energy_features = self._extract_energy(y)

            # ── Silence & Pause Detection ─────────────
            intervals = librosa.effects.split(y, top_db=abs(self.silence_threshold_db))
            pause_features = self._analyze_pauses(intervals, duration, sr)
            silence_features = self._analyze_silence(intervals, duration, sr)

            result = {
                "duration_sec": round(duration, 3),
                "pitch": pitch_features,
                "energy": energy_features,
                "pauses": pause_features,
                "silence": silence_features,
            }

            logger.info(
                f"Prosody analysis complete: {duration:.1f}s, "
                f"pitch_mean={pitch_features['mean_hz']:.1f}Hz, "
                f"silence_ratio={silence_features['ratio']:.2f}"
            )
            return result

        except ImportError:
            logger.warning("librosa not installed — prosody analysis disabled")
            return self._empty_result()
        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            return self._empty_result()
        except Exception as e:
            logger.error(f"Prosody analysis failed: {e}", exc_info=True)
            return self._empty_result()

    def _extract_pitch(self, y: np.ndarray, sr: int) -> Dict:
        """
        Extract F0 (fundamental frequency) using Librosa's pyin algorithm.

        pyin is preferred over yin for clinical analysis because it provides
        probabilistic voicing detection, reducing false pitch estimates.
        """
        import librosa

        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=librosa.note_to_hz("C2"),   # ~65 Hz (low male voice)
            fmax=librosa.note_to_hz("C7"),    # ~2093 Hz (high female voice)
            sr=sr,
        )

        # Filter to voiced frames only (where pitch was detected)
        f0_voiced = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        total_frames = len(f0) if f0 is not None else 1

        if len(f0_voiced) < 2:
            return {
                "mean_hz": 0.0,
                "std_hz": 0.0,
                "min_hz": 0.0,
                "max_hz": 0.0,
                "range_hz": 0.0,
                "jitter": 0.0,
                "voiced_fraction": 0.0,
            }

        # Jitter: mean absolute difference between consecutive pitch values
        # Clinical: high jitter can indicate vocal tremor or emotional distress
        pitch_diffs = np.abs(np.diff(f0_voiced))
        jitter = float(np.mean(pitch_diffs) / np.mean(f0_voiced)) if np.mean(f0_voiced) > 0 else 0.0

        return {
            "mean_hz": round(float(np.mean(f0_voiced)), 2),
            "std_hz": round(float(np.std(f0_voiced)), 2),
            "min_hz": round(float(np.min(f0_voiced)), 2),
            "max_hz": round(float(np.max(f0_voiced)), 2),
            "range_hz": round(float(np.max(f0_voiced) - np.min(f0_voiced)), 2),
            "jitter": round(jitter, 4),
            "voiced_fraction": round(len(f0_voiced) / total_frames, 3),
        }

    def _extract_energy(self, y: np.ndarray) -> Dict:
        """
        Extract RMS energy envelope (intensity proxy).

        Clinical: Low energy variance → monotone delivery.
        """
        import librosa

        rms = librosa.feature.rms(y=y)[0]

        if len(rms) == 0:
            return {"mean_db": 0.0, "std_db": 0.0, "dynamic_range_db": 0.0}

        # Convert to dB scale (avoid log(0))
        rms_db = librosa.amplitude_to_db(rms, ref=np.max(rms))

        return {
            "mean_db": round(float(np.mean(rms_db)), 2),
            "std_db": round(float(np.std(rms_db)), 2),
            "dynamic_range_db": round(float(np.max(rms_db) - np.min(rms_db)), 2),
        }

    def _analyze_pauses(self, intervals: np.ndarray, duration: float, sr: int) -> Dict:
        """
        Analyze gaps between speech segments as pauses.

        A pause is a silence gap > MIN_PAUSE_SEC between two speech segments.
        """
        if len(intervals) < 2:
            return {
                "count": 0,
                "total_duration_sec": 0.0,
                "avg_duration_ms": 0.0,
                "max_duration_ms": 0.0,
                "long_pause_count": 0,
            }

        pauses = []
        for i in range(1, len(intervals)):
            gap_start = intervals[i - 1][1]
            gap_end = intervals[i][0]
            pause_sec = (gap_end - gap_start) / sr

            if pause_sec > self.MIN_PAUSE_SEC:
                pauses.append(pause_sec)

        if not pauses:
            return {
                "count": 0,
                "total_duration_sec": 0.0,
                "avg_duration_ms": 0.0,
                "max_duration_ms": 0.0,
                "long_pause_count": 0,
            }

        return {
            "count": len(pauses),
            "total_duration_sec": round(sum(pauses), 3),
            "avg_duration_ms": round(float(np.mean(pauses)) * 1000, 1),
            "max_duration_ms": round(float(np.max(pauses)) * 1000, 1),
            "long_pause_count": sum(1 for p in pauses if p > self.LONG_PAUSE_SEC),
        }

    def _analyze_silence(self, intervals: np.ndarray, duration: float, sr: int) -> Dict:
        """Calculate overall silence vs speech ratio."""
        if len(intervals) == 0:
            return {"ratio": 1.0, "speech_duration_sec": 0.0}

        speech_duration = sum((end - start) / sr for start, end in intervals)
        silence_ratio = max(0.0, (duration - speech_duration) / max(duration, 0.01))

        return {
            "ratio": round(silence_ratio, 3),
            "speech_duration_sec": round(speech_duration, 3),
        }

    @staticmethod
    def _empty_result(duration: float = 0.0) -> Dict:
        """Return empty prosody structure (safe for downstream consumers)."""
        return {
            "duration_sec": round(duration, 3),
            "pitch": {
                "mean_hz": 0.0, "std_hz": 0.0, "min_hz": 0.0,
                "max_hz": 0.0, "range_hz": 0.0, "jitter": 0.0,
                "voiced_fraction": 0.0,
            },
            "energy": {
                "mean_db": 0.0, "std_db": 0.0, "dynamic_range_db": 0.0,
            },
            "pauses": {
                "count": 0, "total_duration_sec": 0.0,
                "avg_duration_ms": 0.0, "max_duration_ms": 0.0,
                "long_pause_count": 0,
            },
            "silence": {
                "ratio": 0.0, "speech_duration_sec": 0.0,
            },
        }
