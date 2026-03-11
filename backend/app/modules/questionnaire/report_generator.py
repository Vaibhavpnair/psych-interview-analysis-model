"""
ReportGenerator — produces a structured session summary after all 23 questions.

Computes:
  - Risk band (Low / Moderate / High)
  - Overall confidence score
  - Escalation recommendation
  - Behavioral observations
  - Per-domain results (via DomainAggregator)

No diagnosis logic — decision-support only.
"""

import time
import logging
from typing import List, Optional
from dataclasses import dataclass, field

from app.modules.questionnaire.question_engine import QuestionEngine, QuestionResponse
from app.modules.questionnaire.domain_aggregator import DomainAggregator, DomainResult

logger = logging.getLogger(__name__)


@dataclass
class SessionReport:
    """Structured session summary — decision-support only."""
    session_id: str
    completed: bool
    total_questions: int
    total_answered: int
    duration_seconds: float

    risk_band: str              # "Low" | "Moderate" | "High"
    confidence_score: float     # avg confidence_proxy across all questions
    escalation: Optional[str]   # e.g. "Immediate review — suicidal ideation flagged"
    flagged_domains: List[str]  # domain labels that exceeded threshold
    domains: List[dict]         # DomainResult.to_dict() for each domain
    behavioral_summary: List[str]   # human-readable observations
    explainability_note: str = (
        "This report reflects observational metrics derived from audio, visual, "
        "and linguistic features. It is a decision-support tool only and does not "
        "constitute a clinical diagnosis."
    )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "completed": self.completed,
            "total_questions": self.total_questions,
            "total_answered": self.total_answered,
            "duration_seconds": self.duration_seconds,
            "risk_band": self.risk_band,
            "confidence_score": self.confidence_score,
            "escalation": self.escalation,
            "flagged_domains": self.flagged_domains,
            "domains": self.domains,
            "behavioral_summary": self.behavioral_summary,
            "explainability_note": self.explainability_note,
        }


# ── High-Risk Domains ───────────────────────────────────────
_CRITICAL_DOMAINS = {"suicidal_ideation", "psychosis", "substance_use"}


class ReportGenerator:
    """
    Generates a structured session report from assessment results.

    Usage:
        generator = ReportGenerator()
        report = generator.generate(engine, assess_id)
    """

    def __init__(self):
        self._aggregator = DomainAggregator()

    def generate(self, engine: QuestionEngine, assess_id: str) -> SessionReport:
        """Generate the full session report."""
        meta = engine.get_session_meta(assess_id)
        responses = engine.get_responses(assess_id)

        # Domain aggregation
        domain_results = self._aggregator.aggregate(responses)

        # Flagged domains
        flagged = [d for d in domain_results if d.threshold_exceeded]
        flagged_labels = [d.domain_label for d in flagged]

        # Risk band
        risk_band = self._compute_risk_band(domain_results)

        # Confidence score (avg across all questions)
        confidence = (
            sum(r.confidence_proxy for r in responses) / len(responses)
            if responses else 0.0
        )

        # Escalation
        escalation = self._compute_escalation(domain_results)

        # Behavioral summary
        observations = self._generate_observations(responses, domain_results)

        return SessionReport(
            session_id=meta["session_id"],
            completed=meta["completed"],
            total_questions=meta["total_questions"],
            total_answered=meta["total_answered"],
            duration_seconds=meta["duration_seconds"],
            risk_band=risk_band,
            confidence_score=round(confidence, 3),
            escalation=escalation,
            flagged_domains=flagged_labels,
            domains=[d.to_dict() for d in domain_results],
            behavioral_summary=observations,
        )

    @staticmethod
    def _compute_risk_band(domain_results: List[DomainResult]) -> str:
        """
        Risk band logic:
          High:     suicidal ideation flagged OR ≥4 domains exceeded
          Moderate: 2–3 domains exceeded
          Low:      0–1 domains exceeded
        """
        flagged = [d for d in domain_results if d.threshold_exceeded]
        n_flagged = len(flagged)

        # Check critical domains
        critical_flagged = any(
            d.domain in _CRITICAL_DOMAINS and d.threshold_exceeded
            for d in domain_results
        )

        if critical_flagged or n_flagged >= 4:
            return "High"
        elif n_flagged >= 2:
            return "Moderate"
        return "Low"

    @staticmethod
    def _compute_escalation(domain_results: List[DomainResult]) -> Optional[str]:
        """Generate escalation message if critical domains are flagged."""
        critical_flags = []
        for d in domain_results:
            if d.domain in _CRITICAL_DOMAINS and d.threshold_exceeded:
                critical_flags.append(d.domain_label)

        if not critical_flags:
            return None

        labels = ", ".join(critical_flags)
        return f"Immediate review recommended — flagged: {labels}"

    @staticmethod
    def _generate_observations(
        responses: List[QuestionResponse],
        domain_results: List[DomainResult],
    ) -> List[str]:
        """Generate human-readable behavioral observations."""
        obs = []
        if not responses:
            return obs

        # Overall speech rate
        avg_rate = sum(r.avg_speech_rate for r in responses) / len(responses)
        if avg_rate > 170:
            obs.append(f"Elevated average speech rate: {avg_rate:.0f} WPM (may indicate agitation)")
        elif avg_rate < 80 and avg_rate > 0:
            obs.append(f"Reduced average speech rate: {avg_rate:.0f} WPM (may indicate psychomotor slowing)")

        # Hesitation
        avg_hes = sum(r.hesitation_ratio for r in responses) / len(responses)
        if avg_hes > 0.15:
            obs.append(f"High hesitation marker ratio: {avg_hes:.1%} (may indicate uncertainty or cognitive load)")

        # Facial stability
        avg_stability = sum(r.facial_stability for r in responses) / len(responses)
        if avg_stability < 0.5:
            obs.append(f"Low facial stability: {avg_stability:.2f} (frequent expression changes observed)")

        # Emotional intensity
        avg_intensity = sum(r.emotional_intensity for r in responses) / len(responses)
        if avg_intensity > 0.6:
            obs.append(f"High emotional intensity: {avg_intensity:.2f} (elevated affective expression)")

        # Blink rate
        avg_blink = sum(r.blink_rate for r in responses) / len(responses)
        if avg_blink > 25:
            obs.append(f"Elevated blink rate: {avg_blink:.0f}/min (may indicate stress or anxiety)")
        elif avg_blink > 0 and avg_blink < 8:
            obs.append(f"Reduced blink rate: {avg_blink:.0f}/min (may indicate concentration or dissociation)")

        # Confidence
        avg_conf = sum(r.confidence_proxy for r in responses) / len(responses)
        if avg_conf < 0.4:
            obs.append(f"Low overall confidence proxy: {avg_conf:.2f} (multimodal indicators suggest low self-assurance)")

        # Flagged domains summary
        n_flagged = len([d for d in domain_results if d.threshold_exceeded])
        if n_flagged > 0:
            obs.append(f"{n_flagged} of {len(domain_results)} domains exceeded clinical threshold")

        if not obs:
            obs.append("All behavioral metrics are within expected ranges")

        return obs
