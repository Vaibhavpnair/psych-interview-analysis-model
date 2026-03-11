"""
Pydantic schemas for analysis outputs (risk scoring, flags, features).
"""
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FeatureVector(BaseModel):
    """Normalized feature input for the fusion layer."""
    # Vision
    face_valence: float = Field(0.0, ge=-1.0, le=1.0)
    face_arousal: float = Field(0.0, ge=0.0, le=1.0)

    # Audio
    pitch_variance: float = Field(0.0, ge=0.0, le=1.0)
    silence_ratio: float = Field(0.0, ge=0.0, le=1.0)
    speech_rate_wpm: float = 0.0

    # Text
    sentiment_polarity: float = Field(0.0, ge=-1.0, le=1.0)
    absolutist_count: int = 0
    first_person_ratio: float = 0.0

    # Behavior
    response_latency_sec: float = 0.0


class RiskFlag(BaseModel):
    """Individual flag raised by the fusion engine."""
    type: str  # CONTRADICTION | LATENCY | ABSOLUTIST_WORD | PSYCHOMOTOR
    severity: str  # LOW | MODERATE | HIGH
    description: str


class RiskAssessment(BaseModel):
    """Output of the multimodal fusion layer."""
    session_id: UUID
    band: str  # Low Concern | Moderate Concern | High Concern
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    flags: List[RiskFlag] = []
    top_contributors: List[str] = []  # Explainability: why this score?


class SpeechFeatures(BaseModel):
    """Output of the audio/speech processing module."""
    speech_rate_wpm: float = 0.0
    pitch_mean_hz: float = 0.0
    pitch_std_dev: float = 0.0
    pause_count: int = 0
    avg_pause_duration_ms: float = 0.0
    silence_ratio: float = 0.0
    filler_word_count: int = 0
    filler_words: List[str] = []
    response_latency_ms: float = 0.0


class NLPFeatures(BaseModel):
    """Output of the NLP module."""
    word_count: int = 0
    first_person_ratio: float = 0.0
    absolutist_count: int = 0
    absolutist_terms: List[str] = []
    sentiment_polarity: float = 0.0
    sentiment_label: str = "neutral"
    emotions: Optional[dict] = None  # {sadness: 0.8, anxiety: 0.4, anger: 0.05}
    avoidance_detected: bool = False
    sentence_complexity_score: float = 0.0
