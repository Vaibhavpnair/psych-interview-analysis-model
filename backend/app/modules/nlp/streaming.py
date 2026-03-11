"""
StreamingNLPProcessor — processes individual transcript segments.
Wraps the existing NLPProcessor logic for per-segment streaming.
Maintains running sentiment average across the session.
"""

import logging
from typing import Optional

from app.modules.nlp.processor import NLPProcessor
from app.schemas.streaming import StreamNLPResult, StreamSentiment, StreamLinguistics

logger = logging.getLogger(__name__)


class StreamingNLPProcessor:
    """Thin streaming wrapper around NLPProcessor."""

    def __init__(self):
        self._processor = NLPProcessor()

    def process_segment(
        self, transcript: str, session_id: str, segment_id: int
    ) -> Optional[StreamNLPResult]:
        """
        Analyze a single transcript segment.

        Args:
            transcript: text from one Whisper chunk
            session_id: current session identifier
            segment_id: incrementing segment counter

        Returns:
            StreamNLPResult or None if transcript is empty
        """
        if not transcript or not transcript.strip():
            return None

        try:
            result = self._processor.analyze_text(transcript, session_id, segment_id)

            return StreamNLPResult(
                segment_id=segment_id,
                transcript=transcript,
                sentiment=StreamSentiment(
                    polarity=result.sentiment.polarity,
                    label=result.sentiment.label,
                    confidence=result.sentiment.confidence,
                ),
                features=StreamLinguistics(
                    absolutist_count=result.features.absolutist_count,
                    absolutist_words=result.features.absolutist_words,
                    first_person_pronouns=result.features.first_person_pronouns,
                    avoidance_words=result.features.avoidance_words,
                    sentence_complexity=result.features.sentence_complexity,
                ),
            )
        except Exception as e:
            logger.error(f"NLP segment processing failed: {e}")
            return None
