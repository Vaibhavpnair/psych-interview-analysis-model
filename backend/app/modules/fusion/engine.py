"""
IncrementalFusionEngine — merges audio, vision, and NLP signals
into a running behavioral summary. Non-diagnostic, explainable.
"""

import logging
from typing import List

from app.core.session import SessionState
from app.schemas.streaming import (
    FusionSummary,
    StreamAudioResult,
    StreamFaceData,
    StreamNLPResult,
)

logger = logging.getLogger(__name__)


class IncrementalFusionEngine:
    """
    Stateless fusion engine: reads from / writes to SessionState.
    Each update method mutates the session's running counters.
    `get_summary()` computes the snapshot without side effects.
    """

    def update_audio(self, session: SessionState, result: StreamAudioResult):
        """Incorporate a new audio chunk's features."""
        session.fusion_sample_count += 1

        # Track speech rate for averaging
        session.fusion_speech_rate_samples.append(result.features.speech_rate_wpm)

    def update_vision(self, session: SessionState, face_data: StreamFaceData):
        """Incorporate a new face frame's metrics."""
        if not face_data.face_detected:
            return

        session.fusion_valence_sum += face_data.valence
        session.fusion_arousal_sum += face_data.arousal
        session.fusion_sample_count = max(session.fusion_sample_count, 1)

    def update_nlp(self, session: SessionState, nlp_result: StreamNLPResult):
        """Incorporate a new NLP segment's analysis."""
        session.fusion_sentiment_sum += nlp_result.sentiment.polarity
        session.fusion_absolutist_total += nlp_result.features.absolutist_count
        session.fusion_first_person_total += nlp_result.features.first_person_pronouns
        session.sentiment_history.append(nlp_result.sentiment.polarity)

    def get_summary(self, session: SessionState) -> FusionSummary:
        """
        Compute a point-in-time fusion summary from the session's
        accumulated data. No side effects.
        """
        n = max(session.fusion_sample_count, 1)
        n_sentiments = max(len(session.sentiment_history), 1)

        # Averages
        avg_valence = session.fusion_valence_sum / n
        avg_arousal = session.fusion_arousal_sum / n
        avg_sentiment = session.fusion_sentiment_sum / n_sentiments

        # Speech rate
        rate_samples = session.fusion_speech_rate_samples
        avg_rate = (
            sum(rate_samples) / len(rate_samples) if rate_samples else 0.0
        )

        # Generate human-readable observations (non-diagnostic)
        observations = self._generate_observations(
            avg_valence, avg_arousal, avg_sentiment, avg_rate,
            session.fusion_absolutist_total,
            session.fusion_first_person_total,
        )

        return FusionSummary(
            overall_valence=round(avg_valence, 3),
            overall_arousal=round(avg_arousal, 3),
            overall_sentiment_polarity=round(avg_sentiment, 3),
            total_absolutist_words=session.fusion_absolutist_total,
            total_first_person_pronouns=session.fusion_first_person_total,
            avg_speech_rate_wpm=round(avg_rate, 1),
            sample_count=session.fusion_sample_count,
            observations=observations,
        )

    def _generate_observations(
        self,
        valence: float,
        arousal: float,
        sentiment: float,
        speech_rate: float,
        absolutist_count: int,
        first_person_count: int,
    ) -> List[str]:
        """Generate non-diagnostic, explainable observations."""
        obs: List[str] = []

        # Valence
        if valence < -0.3:
            obs.append("Negative facial affect observed (low smile, brow furrowing)")
        elif valence > 0.3:
            obs.append("Positive facial affect observed (frequent smiling)")

        # Arousal
        if arousal > 0.7:
            obs.append("Elevated arousal indicators (wide eye openness)")
        elif arousal < 0.3:
            obs.append("Low arousal indicators (reduced eye openness)")

        # Sentiment
        if sentiment < -0.3:
            obs.append("Negative linguistic sentiment detected in speech content")
        elif sentiment > 0.3:
            obs.append("Positive linguistic sentiment detected in speech content")

        # Speech rate
        if speech_rate > 180:
            obs.append(f"Elevated speech rate ({speech_rate:.0f} WPM)")
        elif 0 < speech_rate < 80:
            obs.append(f"Slow speech rate ({speech_rate:.0f} WPM)")

        # Absolutist language
        if absolutist_count >= 5:
            obs.append(f"Frequent absolutist language ({absolutist_count} instances)")

        # Self-referential
        if first_person_count >= 10:
            obs.append(f"High self-referential language ({first_person_count} first-person pronouns)")

        if not obs:
            obs.append("Behavioral indicators within typical ranges")

        return obs


# Global singleton
fusion_engine = IncrementalFusionEngine()
