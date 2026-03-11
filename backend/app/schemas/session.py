"""
Pydantic schemas for Session endpoints — request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Session CRUD ─────────────────────────────────────

class SessionCreate(BaseModel):
    patient_id: UUID
    interviewer_id: Optional[str] = None
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    created_at: datetime
    duration_seconds: Optional[int] = None
    status: str = "pending"  # pending | processing | completed | failed

    class Config:
        from_attributes = True


# ── Analysis Results ─────────────────────────────────

class SessionSummary(BaseModel):
    """Zone A: Session Header data."""
    session_id: UUID
    risk_band: str = "Low Concern"  # Low Concern | Moderate Concern | High Concern
    risk_score: float = Field(ge=0.0, le=1.0, default=0.0)
    summary: str = ""
    duration_seconds: int = 0
    word_count: int = 0


class TimelineDataPoint(BaseModel):
    """Single data point in the behavioral timeline (1s granularity)."""
    timestamp: int  # seconds from start
    audio_pitch: Optional[float] = None
    audio_silence: bool = False
    face_valence: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    flag: Optional[str] = None  # CONTRADICTION | LATENCY | ABSOLUTIST_WORD


class TimelineResponse(BaseModel):
    """Zone B: Behavioral Timeline data."""
    session_id: UUID
    interval_sec: int = 1
    data: List[TimelineDataPoint] = []


class TranscriptSegment(BaseModel):
    """Single segment in the smart transcript."""
    segment_id: int
    timestamp_start: float
    timestamp_end: float
    speaker: str  # "patient" | "interviewer"
    text: str
    highlights: Optional[dict] = None  # filler_words, absolutist_terms, long_pauses
    clinician_note: Optional[str] = None


class TranscriptResponse(BaseModel):
    """Zone C: Smart Transcript data."""
    session_id: UUID
    segments: List[TranscriptSegment] = []


# ── Multimodal Inputs ────────────────────────────────

class SessionTextUpdate(BaseModel):
    """Schema for submitting text input to a session."""
    text: str = Field(..., min_length=1)
    speaker: str = "patient"


# ── Consolidated Results ─────────────────────────────

class SessionResultsResponse(BaseModel):
    """Consolidated response of all multimodal processing results."""
    id: UUID
    status: str
    risk_band: Optional[str] = None
    risk_score: Optional[float] = None
    summary: Optional[str] = None
    
    # Feature blocks
    speech_features: Optional[dict] = None
    nlp_features: Optional[dict] = None
    vision_features: Optional[dict] = None
    fusion_result: Optional[dict] = None
    
    # Metadata
    duration_seconds: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
