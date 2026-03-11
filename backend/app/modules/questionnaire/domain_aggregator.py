"""
DomainAggregator — groups per-question QuestionResponses by DSM-5 domain,
computes domain-level scores, behavioral_intensity_index, and threshold flags.

No diagnosis logic — decision-support only.
"""

import logging
from typing import List, Dict
from dataclasses import dataclass, field

from app.modules.questionnaire.question_bank import (
    question_bank,
    DOMAIN_INFO,
)
from app.modules.questionnaire.question_engine import QuestionResponse

logger = logging.getLogger(__name__)


@dataclass
class DomainResult:
    """Aggregated result for a single psychiatric domain."""
    domain: str
    domain_label: str
    threshold_type: str
    threshold_value: int
    highest_score: int
    threshold_exceeded: bool
    behavioral_intensity_index: float   # avg emotional_intensity across domain questions
    avg_confidence_proxy: float
    avg_valence: float
    avg_arousal: float
    avg_sentiment: float
    avg_speech_rate: float
    avg_hesitation_ratio: float
    avg_facial_stability: float
    avg_blink_rate: float
    total_words: int
    total_pauses: int
    questions_count: int
    recommendation: str
    questions: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "domain_label": self.domain_label,
            "threshold_type": self.threshold_type,
            "threshold_value": self.threshold_value,
            "highest_score": self.highest_score,
            "threshold_exceeded": self.threshold_exceeded,
            "behavioral_intensity_index": self.behavioral_intensity_index,
            "avg_confidence_proxy": self.avg_confidence_proxy,
            "avg_valence": self.avg_valence,
            "avg_arousal": self.avg_arousal,
            "avg_sentiment": self.avg_sentiment,
            "avg_speech_rate": self.avg_speech_rate,
            "avg_hesitation_ratio": self.avg_hesitation_ratio,
            "avg_facial_stability": self.avg_facial_stability,
            "avg_blink_rate": self.avg_blink_rate,
            "total_words": self.total_words,
            "total_pauses": self.total_pauses,
            "questions_count": self.questions_count,
            "recommendation": self.recommendation,
            "questions": self.questions,
        }


def _question_response_to_dict(r: QuestionResponse) -> dict:
    """Serialize a QuestionResponse for inclusion in domain results."""
    return {
        "question_id": r.question_id,
        "text": r.question_text,
        "self_report_score": r.self_report_score,
        "transcript": r.transcript,
        "duration_seconds": r.duration_seconds,
        "audio": {
            "segments": r.audio_segments,
            "avg_pitch": r.avg_pitch,
            "pitch_variance": r.pitch_variance,
            "avg_energy_rms": r.avg_energy_rms,
            "avg_speech_rate": r.avg_speech_rate,
            "total_words": r.total_words,
            "total_pauses": r.total_pauses,
            "hesitation_count": r.hesitation_count,
            "hesitation_ratio": r.hesitation_ratio,
        },
        "vision": {
            "frames": r.video_frames,
            "face_detected_frames": r.face_detected_frames,
            "avg_valence": r.avg_valence,
            "avg_arousal": r.avg_arousal,
            "avg_smile": r.avg_smile,
            "avg_brow_furrow": r.avg_brow_furrow,
            "blink_rate": r.blink_rate,
            "facial_stability": r.facial_stability,
            "emotional_intensity": r.emotional_intensity,
        },
        "nlp": {
            "avg_sentiment": r.avg_sentiment,
            "absolutist_words": r.absolutist_words,
            "first_person_pronouns": r.first_person_pronouns,
        },
        "confidence_proxy": r.confidence_proxy,
    }


class DomainAggregator:
    """
    Groups QuestionResponses by domain, computes aggregate metrics.

    Usage:
        aggregator = DomainAggregator()
        results = aggregator.aggregate(responses)
        # results: List[DomainResult]
    """

    def aggregate(self, responses: List[QuestionResponse]) -> List[DomainResult]:
        """Group responses by domain and compute per-domain aggregates."""

        # Group by domain
        domain_map: Dict[str, List[QuestionResponse]] = {}
        for r in responses:
            domain_map.setdefault(r.domain, []).append(r)

        results = []
        for domain_key, domain_responses in domain_map.items():
            domain_info = DOMAIN_INFO.get(domain_key, {})
            domain_questions = question_bank.get_by_domain(domain_key)
            q0 = domain_questions[0] if domain_questions else None

            n = len(domain_responses)
            highest = max(r.self_report_score for r in domain_responses)
            threshold_type = q0.threshold_type if q0 else "mild"
            threshold_value = q0.threshold_value if q0 else 2
            exceeded = highest >= threshold_value

            # Averages
            avg_valence = sum(r.avg_valence for r in domain_responses) / n
            avg_arousal = sum(r.avg_arousal for r in domain_responses) / n
            avg_sentiment = sum(r.avg_sentiment for r in domain_responses) / n
            avg_speech_rate = sum(r.avg_speech_rate for r in domain_responses) / n
            avg_hesitation = sum(r.hesitation_ratio for r in domain_responses) / n
            avg_stability = sum(r.facial_stability for r in domain_responses) / n
            avg_confidence = sum(r.confidence_proxy for r in domain_responses) / n
            avg_blink = sum(r.blink_rate for r in domain_responses) / n

            # Behavioral intensity index
            bii = sum(r.emotional_intensity for r in domain_responses) / n

            # Recommendation
            if exceeded:
                recommendation = "Further clinical inquiry advised"
            else:
                recommendation = "Within expected range — no immediate action required"

            result = DomainResult(
                domain=domain_key,
                domain_label=domain_info.get("label", domain_key),
                threshold_type=threshold_type,
                threshold_value=threshold_value,
                highest_score=highest,
                threshold_exceeded=exceeded,
                behavioral_intensity_index=round(bii, 3),
                avg_confidence_proxy=round(avg_confidence, 3),
                avg_valence=round(avg_valence, 3),
                avg_arousal=round(avg_arousal, 3),
                avg_sentiment=round(avg_sentiment, 3),
                avg_speech_rate=round(avg_speech_rate, 1),
                avg_hesitation_ratio=round(avg_hesitation, 3),
                avg_facial_stability=round(avg_stability, 3),
                avg_blink_rate=round(avg_blink, 1),
                total_words=sum(r.total_words for r in domain_responses),
                total_pauses=sum(r.total_pauses for r in domain_responses),
                questions_count=n,
                recommendation=recommendation,
                questions=[_question_response_to_dict(r) for r in domain_responses],
            )
            results.append(result)

        return results
