"""
Pydantic schemas for real-time streaming events.
All WebSocket messages conform to StreamEvent envelope.
"""

from pydantic import BaseModel
from typing import Optional, List, Any


# ── Envelope ────────────────────────────────────────────────
class StreamEvent(BaseModel):
    """Top-level envelope for all WebSocket JSON messages."""
    type: str          # "transcript" | "audio_features" | "face_data" | "nlp_result" | "fusion_summary" | "error" | "status"
    data: dict = {}


# ── Audio ───────────────────────────────────────────────────
class StreamTranscript(BaseModel):
    text: str
    segment_id: int
    is_partial: bool = False
    word_count: int = 0


class PauseDetail(BaseModel):
    """A single detected pause within a chunk."""
    start_sec: float     # offset within the chunk
    end_sec: float
    duration_sec: float


class StreamAudioFeatures(BaseModel):
    """Per-chunk acoustic features (emitted after each ~3s chunk)."""
    pitch_mean: float
    pitch_std: float
    energy_rms: float                # root-mean-square amplitude
    energy_db: float                 # energy in decibels
    silence_ratio: float
    speech_rate_wpm: float
    pause_count: int
    pauses: List[PauseDetail] = []   # individual pause locations
    word_count: int = 0
    chunk_duration: float
    hesitation_count: int = 0        # filler words: um, uh, like, you know
    hesitation_ratio: float = 0.0    # hesitation_count / word_count


class RollingAudioStats(BaseModel):
    """Aggregated stats over the last ~10s rolling window."""
    window_duration: float
    window_chunks: int
    avg_pitch_mean: float
    avg_pitch_std: float
    avg_energy_rms: float
    avg_energy_db: float
    avg_silence_ratio: float
    avg_speech_rate_wpm: float
    total_pauses_in_window: int
    total_words_in_window: int


class AudioUpdateEvent(BaseModel):
    """Full audio update sent to client: chunk features + rolling stats."""
    chunk: StreamAudioFeatures
    rolling: RollingAudioStats
    cumulative_words: int
    cumulative_pauses: int
    cumulative_duration: float


class StreamAudioResult(BaseModel):
    transcript: StreamTranscript
    features: StreamAudioFeatures


# ── Vision ──────────────────────────────────────────────────
class StreamFaceData(BaseModel):
    timestamp: float
    face_detected: bool
    valence: float
    arousal: float
    smile_score: float
    brow_furrow_score: float
    eye_contact_score: float
    eye_open_ratio: float = 0.0      # avg eye height / face width (for blink detection)
    frame_index: int


# ── NLP ─────────────────────────────────────────────────────
class StreamSentiment(BaseModel):
    polarity: float
    label: str
    confidence: float


class StreamLinguistics(BaseModel):
    absolutist_count: int
    absolutist_words: List[str]
    first_person_pronouns: int
    avoidance_words: List[str]
    sentence_complexity: float


class StreamNLPResult(BaseModel):
    segment_id: int
    transcript: str
    sentiment: StreamSentiment
    features: StreamLinguistics


# ── Fusion ──────────────────────────────────────────────────
class FusionSummary(BaseModel):
    """
    Non-diagnostic behavioral summary.
    All fields are observational — no clinical labels.
    """
    overall_valence: float          # running average
    overall_arousal: float          # running average
    overall_sentiment_polarity: float
    total_absolutist_words: int
    total_first_person_pronouns: int
    avg_speech_rate_wpm: float
    sample_count: int
    observations: List[str]         # human-readable observations, e.g. "elevated speech rate"
    explainability_note: str = (
        "This summary reflects observational metrics derived from audio, visual, "
        "and linguistic features. It does not constitute a clinical diagnosis."
    )
