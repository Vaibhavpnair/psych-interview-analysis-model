"""
REST API endpoints for the DSM-5 Level 1 Cross-Cutting Symptom Measure.

Endpoints:
    POST /start              — Start a new questionnaire session
    GET  /{session_id}/current  — Get current question
    POST /{session_id}/answer   — Submit answer, get next question
    GET  /{session_id}/results  — Get domain results + threshold flags
"""

from fastapi import APIRouter, HTTPException

from app.modules.questionnaire.flow_controller import flow_controller
from app.schemas.questionnaire import (
    AnswerSubmission,
    StartSessionResponse,
    SubmitAnswerResponse,
    SessionResultsSchema,
    QuestionSchema,
)

router = APIRouter()


@router.post("/start", response_model=StartSessionResponse)
def start_questionnaire():
    """Start a new DSM-5 Level 1 questionnaire session."""
    session_id, first_question = flow_controller.start_session()
    return StartSessionResponse(
        session_id=session_id,
        first_question=first_question,
    )


@router.get("/{session_id}/current", response_model=QuestionSchema)
def get_current_question(session_id: str):
    """Get the current unanswered question for a session."""
    try:
        question = flow_controller.get_current_question(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if question is None:
        raise HTTPException(status_code=400, detail="Questionnaire already completed")

    return question


@router.post("/{session_id}/answer", response_model=SubmitAnswerResponse)
def submit_answer(session_id: str, body: AnswerSubmission):
    """Submit an answer to the current question and get the next one."""
    try:
        next_question, completed = flow_controller.submit_answer(
            session_id, body.question_id, body.score
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SubmitAnswerResponse(
        accepted=True,
        next_question=next_question,
        completed=completed,
    )


@router.get("/{session_id}/results", response_model=SessionResultsSchema)
def get_results(session_id: str):
    """Get per-domain results and threshold flags for a session."""
    try:
        return flow_controller.get_results(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
