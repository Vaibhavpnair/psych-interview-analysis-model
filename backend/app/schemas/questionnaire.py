"""
Pydantic schemas for the DSM-5 Level 1 Cross-Cutting questionnaire API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ResponseOption(BaseModel):
    value: int
    label: str
    description: str


class QuestionSchema(BaseModel):
    id: str
    domain: str
    domain_label: str
    text: str
    question_number: int = Field(..., description="1-indexed position in the measure")
    total_questions: int
    response_options: List[ResponseOption]


class AnswerSubmission(BaseModel):
    question_id: str
    score: int = Field(..., ge=0, le=4, description="0=None, 1=Slight, 2=Mild, 3=Moderate, 4=Severe")


class StartSessionResponse(BaseModel):
    session_id: str
    first_question: QuestionSchema


class SubmitAnswerResponse(BaseModel):
    accepted: bool
    next_question: Optional[QuestionSchema] = None
    completed: bool = False


class DomainResult(BaseModel):
    domain: str
    domain_label: str
    questions_answered: int
    max_score: int = Field(..., description="Highest score among questions in this domain")
    threshold_type: str
    threshold_value: int
    exceeded: bool = Field(..., description="True if max_score >= threshold_value")


class SessionResultsSchema(BaseModel):
    session_id: str
    total_answered: int
    total_questions: int
    completed: bool
    domains: List[DomainResult]
    flagged_domains: List[str] = Field(
        ..., description="Domain names where threshold was exceeded"
    )
