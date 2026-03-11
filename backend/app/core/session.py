"""
SessionManager — manages per-session state for real-time streaming.
Each WebSocket connection creates a Session that holds audio buffers,
frame counters, NLP history, fusion state, and a rolling audio window.
"""

import asyncio
import time
import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from fastapi import WebSocket

from app.core.config import (
    AUDIO_SAMPLE_RATE,
    AUDIO_BUFFER_SECONDS,
    MAX_CONCURRENT_SESSIONS,
    ROLLING_MAX_CHUNKS,
)


# ── Rolling Audio Chunk Record ──────────────────────────────
@dataclass
class AudioChunkRecord:
    """Snapshot of one processed audio chunk, kept in the rolling window."""
    segment_id: int
    timestamp: float                    # wall-clock time when processed
    duration: float                     # chunk duration in seconds
    transcript: str
    pitch_mean: float
    pitch_std: float
    energy_rms: float
    energy_db: float
    silence_ratio: float
    speech_rate_wpm: float
    pause_count: int
    pauses: List[dict] = field(default_factory=list)  # [{start, end, duration}, ...]
    word_count: int = 0


@dataclass
class SessionState:
    """Per-session mutable state."""
    session_id: str
    websocket: WebSocket
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    # Audio buffer — accumulates PCM float32 samples (pre-processing)
    audio_buffer: bytes = b""
    audio_segment_counter: int = 0

    # Rolling window of processed audio chunks (last ~10 seconds)
    rolling_audio_chunks: deque = field(
        default_factory=lambda: deque(maxlen=ROLLING_MAX_CHUNKS)
    )

    # Cumulative audio totals (all-session, never evicted)
    total_word_count: int = 0
    total_pause_count: int = 0
    total_audio_duration: float = 0.0

    # Vision
    frame_counter: int = 0

    # NLP running history
    all_transcripts: list = field(default_factory=list)
    sentiment_history: list = field(default_factory=list)

    # Fusion running averages
    fusion_valence_sum: float = 0.0
    fusion_arousal_sum: float = 0.0
    fusion_sentiment_sum: float = 0.0
    fusion_sample_count: int = 0
    fusion_absolutist_total: int = 0
    fusion_first_person_total: int = 0
    fusion_speech_rate_samples: list = field(default_factory=list)

    # Control
    is_recording: bool = False
    audio_queue: Optional[asyncio.Queue] = field(default=None)
    video_queue: Optional[asyncio.Queue] = field(default=None)

    def touch(self):
        self.last_activity = time.time()

    @property
    def audio_buffer_duration(self) -> float:
        """Duration of buffered audio in seconds."""
        num_samples = len(self.audio_buffer) // 4
        return num_samples / AUDIO_SAMPLE_RATE if AUDIO_SAMPLE_RATE > 0 else 0.0

    def append_audio(self, pcm_bytes: bytes):
        """Append raw PCM bytes to the audio buffer."""
        self.audio_buffer += pcm_bytes
        self.touch()

    def flush_audio_buffer(self) -> bytes:
        """Return and clear the audio buffer."""
        data = self.audio_buffer
        self.audio_buffer = b""
        return data

    # ── Rolling buffer helpers ──────────────────────────────

    def push_audio_chunk(self, record: AudioChunkRecord):
        """Add a processed chunk to the rolling window and update totals."""
        self.rolling_audio_chunks.append(record)
        self.total_word_count += record.word_count
        self.total_pause_count += record.pause_count
        self.total_audio_duration += record.duration

    def get_rolling_stats(self) -> dict:
        """Compute aggregated statistics over the rolling window."""
        chunks = list(self.rolling_audio_chunks)
        if not chunks:
            return {
                "window_duration": 0.0,
                "window_chunks": 0,
                "avg_pitch_mean": 0.0,
                "avg_pitch_std": 0.0,
                "avg_energy_rms": 0.0,
                "avg_energy_db": 0.0,
                "avg_silence_ratio": 0.0,
                "avg_speech_rate_wpm": 0.0,
                "total_pauses_in_window": 0,
                "total_words_in_window": 0,
            }

        n = len(chunks)
        window_dur = sum(c.duration for c in chunks)
        return {
            "window_duration": round(window_dur, 2),
            "window_chunks": n,
            "avg_pitch_mean": round(sum(c.pitch_mean for c in chunks) / n, 2),
            "avg_pitch_std": round(sum(c.pitch_std for c in chunks) / n, 2),
            "avg_energy_rms": round(sum(c.energy_rms for c in chunks) / n, 4),
            "avg_energy_db": round(sum(c.energy_db for c in chunks) / n, 2),
            "avg_silence_ratio": round(sum(c.silence_ratio for c in chunks) / n, 3),
            "avg_speech_rate_wpm": round(sum(c.speech_rate_wpm for c in chunks) / n, 1),
            "total_pauses_in_window": sum(c.pause_count for c in chunks),
            "total_words_in_window": sum(c.word_count for c in chunks),
        }

    def reset(self):
        """Reset all session state (for re-use or cleanup)."""
        self.audio_buffer = b""
        self.audio_segment_counter = 0
        self.rolling_audio_chunks.clear()
        self.total_word_count = 0
        self.total_pause_count = 0
        self.total_audio_duration = 0.0
        self.frame_counter = 0
        self.all_transcripts.clear()
        self.sentiment_history.clear()
        self.fusion_valence_sum = 0.0
        self.fusion_arousal_sum = 0.0
        self.fusion_sentiment_sum = 0.0
        self.fusion_sample_count = 0
        self.fusion_absolutist_total = 0
        self.fusion_first_person_total = 0
        self.fusion_speech_rate_samples.clear()


class SessionManager:
    """Manages all active streaming sessions."""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    def create_session(self, session_id: str, websocket: WebSocket) -> SessionState:
        if len(self._sessions) >= MAX_CONCURRENT_SESSIONS:
            raise RuntimeError(
                f"Max concurrent sessions ({MAX_CONCURRENT_SESSIONS}) reached"
            )
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.websocket = websocket
            session.touch()
            return session

        from app.core.config import AUDIO_CHUNK_MAX_QUEUE, VIDEO_FRAME_MAX_QUEUE

        session = SessionState(
            session_id=session_id,
            websocket=websocket,
            audio_queue=asyncio.Queue(maxsize=AUDIO_CHUNK_MAX_QUEUE),
            video_queue=asyncio.Queue(maxsize=VIDEO_FRAME_MAX_QUEUE),
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def remove_session(self, session_id: str):
        session = self._sessions.pop(session_id, None)
        if session:
            session.reset()

    def all_sessions(self):
        return list(self._sessions.values())


# Global singleton
session_manager = SessionManager()
