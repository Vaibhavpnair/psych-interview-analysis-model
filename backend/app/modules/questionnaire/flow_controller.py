"""
QuestionFlowController — manages state for DSM-5 Level 1 questionnaire sessions.

In-memory session store. No database required.
No diagnosis logic — only question progression and threshold flagging.
"""

import uuid
import logging
from typing import Dict, Optional

from app.modules.questionnaire.question_bank import (
    question_bank,
    RESPONSE_OPTIONS,
    DOMAIN_INFO,
)
from app.schemas.questionnaire import (
    QuestionSchema,
    ResponseOption,
    DomainResult,
    SessionResultsSchema,
)

logger = logging.getLogger(__name__)


class _SessionState:
    """Internal state for a single questionnaire session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_index = 0
        self.answers: Dict[str, int] = {}   # question_id -> score

    @property
    def is_complete(self) -> bool:
        return self.current_index >= question_bank.total_questions

    @property
    def total_answered(self) -> int:
        return len(self.answers)


class QuestionFlowController:
    """
    Manages questionnaire sessions.

    Usage:
        session_id, first_q = controller.start_session()
        next_q, completed = controller.submit_answer(session_id, question_id, score)
        results = controller.get_results(session_id)
    """

    def __init__(self):
        self._sessions: Dict[str, _SessionState] = {}

    def _build_question_schema(self, index: int) -> Optional[QuestionSchema]:
        """Convert a Question at given index to an API schema."""
        q = question_bank.get_question_at_index(index)
        if q is None:
            return None
        domain_info = question_bank.get_domain_info(q.domain)
        return QuestionSchema(
            id=q.id,
            domain=q.domain,
            domain_label=domain_info.get("label", q.domain),
            text=q.text,
            question_number=index + 1,
            total_questions=question_bank.total_questions,
            response_options=[ResponseOption(**opt) for opt in RESPONSE_OPTIONS],
        )

    def start_session(self) -> tuple[str, QuestionSchema]:
        """Create a new session and return (session_id, first_question)."""
        session_id = str(uuid.uuid4())[:8]
        session = _SessionState(session_id)
        self._sessions[session_id] = session
        first_q = self._build_question_schema(0)
        logger.info(f"Questionnaire session started: {session_id}")
        return session_id, first_q

    def submit_answer(
        self, session_id: str, question_id: str, score: int
    ) -> tuple[Optional[QuestionSchema], bool]:
        """
        Record an answer and advance to next question.

        Returns:
            (next_question, completed)
            next_question is None when completed=True
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        # Validate question exists
        q = question_bank.get_by_id(question_id)
        if q is None:
            raise ValueError(f"Unknown question: {question_id}")

        # Record answer
        session.answers[question_id] = score
        session.current_index += 1

        if session.is_complete:
            logger.info(f"Questionnaire completed: {session_id}")
            return None, True

        next_q = self._build_question_schema(session.current_index)
        return next_q, False

    def get_current_question(self, session_id: str) -> Optional[QuestionSchema]:
        """Get the current unanswered question."""
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        if session.is_complete:
            return None
        return self._build_question_schema(session.current_index)

    def get_results(self, session_id: str) -> SessionResultsSchema:
        """Compute per-domain results and threshold flags."""
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        domains = []
        flagged = []

        for domain in question_bank.domains:
            domain_questions = question_bank.get_by_domain(domain)
            answered_scores = [
                session.answers[q.id]
                for q in domain_questions
                if q.id in session.answers
            ]
            if not answered_scores:
                continue

            max_score = max(answered_scores)
            threshold_type = domain_questions[0].threshold_type
            threshold_value = domain_questions[0].threshold_value
            exceeded = max_score >= threshold_value
            domain_info = question_bank.get_domain_info(domain)

            dr = DomainResult(
                domain=domain,
                domain_label=domain_info.get("label", domain),
                questions_answered=len(answered_scores),
                max_score=max_score,
                threshold_type=threshold_type,
                threshold_value=threshold_value,
                exceeded=exceeded,
            )
            domains.append(dr)
            if exceeded:
                flagged.append(domain)

        return SessionResultsSchema(
            session_id=session_id,
            total_answered=session.total_answered,
            total_questions=question_bank.total_questions,
            completed=session.is_complete,
            domains=domains,
            flagged_domains=flagged,
        )

    def remove_session(self, session_id: str):
        """Clean up a session."""
        self._sessions.pop(session_id, None)


# Singleton
flow_controller = QuestionFlowController()
