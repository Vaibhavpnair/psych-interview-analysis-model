"""
Pydantic schemas for Patient endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PatientCreate(BaseModel):
    anonymous_id: str  # Anonymized patient identifier
    age_range: Optional[str] = None  # e.g., "25-30"
    gender: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(BaseModel):
    id: UUID
    anonymous_id: str
    age_range: Optional[str] = None
    gender: Optional[str] = None
    created_at: datetime
    total_sessions: int = 0

    class Config:
        from_attributes = True


class SessionBrief(BaseModel):
    """Brief session info for patient history."""
    session_id: UUID
    date: datetime
    risk_band: str
    risk_score: float


class PatientHistory(BaseModel):
    """Cross-session trend data for a patient."""
    patient_id: UUID
    total_sessions: int = 0
    sessions: List[SessionBrief] = []
    trend_summary: str = ""
