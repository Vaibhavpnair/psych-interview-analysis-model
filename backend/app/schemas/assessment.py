"""
Pydantic schemas for the structured assessment API.
Used for serializing assessment results — the WebSocket endpoint
sends JSON directly so these serve as documentation and validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class QuestionDelivery(BaseModel):
    """A question sent to the frontend."""
    id: str
    domain: str
    domain_label: str
    text: str
    question_number: int
    total_questions: int
    response_options: List[Dict[str, Any]]


class QuestionAudioSummary(BaseModel):
    segments: int = 0
    avg_pitch: float = 0.0
    avg_energy_rms: float = 0.0
    avg_speech_rate: float = 0.0
    total_words: int = 0
    total_pauses: int = 0


class QuestionVisionSummary(BaseModel):
    frames: int = 0
    face_detected_frames: int = 0
    avg_valence: float = 0.0
    avg_arousal: float = 0.0
    avg_smile: float = 0.0
    avg_brow_furrow: float = 0.0


class QuestionNLPSummary(BaseModel):
    avg_sentiment: float = 0.0
    absolutist_words: int = 0
    first_person_pronouns: int = 0


class QuestionResultSchema(BaseModel):
    question_id: str
    text: str
    self_report_score: int
    transcript: str
    duration_seconds: float
    audio: QuestionAudioSummary
    vision: QuestionVisionSummary
    nlp: QuestionNLPSummary


class DomainResultSchema(BaseModel):
    domain: str
    domain_label: str
    threshold_type: str
    threshold_value: int
    max_self_report: int
    exceeded: bool
    questions_count: int
    avg_valence: float
    avg_arousal: float
    avg_sentiment: float
    avg_speech_rate: float
    questions: List[QuestionResultSchema]


class AssessmentResultsSchema(BaseModel):
    session_id: str
    total_questions: int
    total_answered: int
    completed: bool
    duration_seconds: float
    domains: List[DomainResultSchema]
    flagged_domains: List[str]
