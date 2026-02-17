"""
NLP Processing Module — Main orchestrator.

Combines sentiment analysis and lexical feature extraction into a
single NLPProcessor class with structured JSON output.

Architecture:
    NLPProcessor (this file)
    ├── SentimentAnalyzer  — VADER polarity + HuggingFace emotions
    └── LexicalAnalyzer    — Pronouns, absolutist, avoidance, crisis, syntax

Design Principles:
    - Singleton model loading: transformer loaded once, cached for lifetime
    - Graceful degradation: works with VADER alone if transformers unavailable
    - Supports both full-text and per-segment (timestamped) analysis
    - Never raises: all errors handled, returns empty structures
    - FastAPI compatible: async wrapper for non-blocking endpoint usage

Output Schema:
    {
        "status": "success" | "partial" | "error",
        "errors": [str],
        "sentiment": {
            "polarity": {...},
            "label": str,
            "emotions": {...},
            "emotion_model_used": bool
        },
        "lexical": {
            "pronoun_analysis": {...},
            "absolutist_words": {...},
            "avoidance_phrases": {...},
            "crisis_indicators": {...},
            "syntax": {...}
        },
        "segment_analysis": [         # Per-segment breakdown (if segments provided)
            {
                "start": float,
                "end": float,
                "text": str,
                "sentiment": {...}
            }
        ],
        "meta": {
            "total_words": int,
            "total_sentences": int,
            "crisis_detected": bool,
            "dominant_emotion": str
        }
    }
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Thread pool for CPU-bound NLP work (transformer inference)
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="nlp")


class NLPProcessor:
    """
    Processes text for clinically relevant NLP features.

    Pipeline:
        Text Input (full transcript or segments)
        │
        ├─► SentimentAnalyzer ──► Polarity + Emotion Scores
        │
        ├─► LexicalAnalyzer ───► Pronouns, Absolutist, Crisis, Syntax
        │
        └─► Meta Calculation ──► Dominant emotion, crisis flag
                │
                ▼
        Structured JSON Output

    Usage:
        processor = NLPProcessor()
        result = await processor.process(text)
        # or with timestamped segments:
        result = await processor.process(text, segments=[...])
        # or synchronously:
        result = processor.process_sync(text)
    """

    def __init__(self, use_transformer: bool = True):
        """
        Args:
            use_transformer: Whether to load the HuggingFace emotion model.
                             Set False for lightweight / test mode.
        """
        self._use_transformer = use_transformer
        self._sentiment_analyzer = None
        self._lexical_analyzer = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Lazy initialization of sub-modules.
        Called automatically on first process() call.

        Returns:
            True if at least one sub-module initialized.
        """
        if self._initialized:
            return True

        errors = []

        # Initialize sentiment analyzer
        try:
            from app.modules.nlp.sentiment import SentimentAnalyzer
            self._sentiment_analyzer = SentimentAnalyzer(
                use_transformer=self._use_transformer
            )
            # Trigger model loading now (not on first request)
            if not self._sentiment_analyzer.is_available:
                errors.append("Sentiment models failed to load")
        except ImportError as e:
            errors.append(f"Sentiment dependencies missing: {e}")
            self._sentiment_analyzer = None

        # Initialize lexical analyzer
        try:
            from app.modules.nlp.lexical import LexicalAnalyzer
            self._lexical_analyzer = LexicalAnalyzer()
        except ImportError as e:
            errors.append(f"Lexical dependencies missing: {e}")
            self._lexical_analyzer = None

        self._initialized = True

        if errors:
            logger.warning(f"NLPProcessor partial init: {'; '.join(errors)}")
        else:
            logger.info("NLPProcessor fully initialized")

        return self._sentiment_analyzer is not None or self._lexical_analyzer is not None

    # ── Async Interface ──────────────────────────────

    async def process(
        self,
        text: str,
        segments: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Process text asynchronously (non-blocking for FastAPI).

        Args:
            text: Full transcript text
            segments: Optional list of timestamped segments
                      [{"text": str, "start": float, "end": float}, ...]

        Returns:
            Structured NLP analysis result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self.process_sync,
            text,
            segments,
        )

    # ── Synchronous Interface ────────────────────────

    def process_sync(
        self,
        text: str,
        segments: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Process text synchronously.

        Args:
            text: Full transcript text
            segments: Optional list of timestamped segments

        Returns:
            Structured NLP analysis result
        """
        if not text or not text.strip():
            return self._error_result("Empty text input")

        # Ensure initialization
        if not self._initialized:
            self.initialize()

        errors = []
        sentiment_result = None
        lexical_result = None
        segment_analysis = []

        # ── Step 1: Full-text Sentiment ──────────────
        if self._sentiment_analyzer:
            try:
                sentiment_result = self._sentiment_analyzer.analyze(text)
            except Exception as e:
                errors.append(f"Sentiment error: {e}")
                logger.error(f"Sentiment analysis failed: {e}", exc_info=True)
        else:
            errors.append("Sentiment analyzer not available")

        # ── Step 2: Lexical Features ─────────────────
        if self._lexical_analyzer:
            try:
                lexical_result = self._lexical_analyzer.analyze(text)
            except Exception as e:
                errors.append(f"Lexical error: {e}")
                logger.error(f"Lexical analysis failed: {e}", exc_info=True)
        else:
            errors.append("Lexical analyzer not available")

        # ── Step 3: Per-Segment Sentiment (optional) ─
        if segments and self._sentiment_analyzer:
            try:
                segment_analysis = self._sentiment_analyzer.analyze_segments(segments)
            except Exception as e:
                errors.append(f"Segment analysis error: {e}")
                logger.error(f"Segment sentiment failed: {e}", exc_info=True)

        # Use empty defaults if modules failed
        if sentiment_result is None:
            from app.modules.nlp.sentiment import SentimentAnalyzer
            sentiment_result = SentimentAnalyzer._empty_result()

        if lexical_result is None:
            from app.modules.nlp.lexical import LexicalAnalyzer
            lexical_result = LexicalAnalyzer._empty_result()

        # ── Step 4: Meta Summary ─────────────────────
        meta = self._calculate_meta(sentiment_result, lexical_result)

        # Determine status
        if not errors:
            status = "success"
        elif sentiment_result or lexical_result:
            status = "partial"
        else:
            status = "error"

        return {
            "status": status,
            "errors": errors,
            "sentiment": sentiment_result,
            "lexical": lexical_result,
            "segment_analysis": segment_analysis,
            "meta": meta,
        }

    # ── Meta Calculation ─────────────────────────────

    @staticmethod
    def _calculate_meta(sentiment: Dict, lexical: Dict) -> Dict:
        """
        Calculate high-level meta-summary from sentiment and lexical results.
        """
        # Dominant emotion
        emotions = sentiment.get("emotions", {})
        dominant_emotion = "neutral"
        if emotions:
            dominant_emotion = max(emotions, key=emotions.get)

        # Crisis flag
        crisis = lexical.get("crisis_indicators", {})
        crisis_detected = crisis.get("detected", False)

        # Word and sentence counts from syntax
        syntax = lexical.get("syntax", {})

        return {
            "total_words": syntax.get("total_words", 0),
            "total_sentences": syntax.get("total_sentences", 0),
            "crisis_detected": crisis_detected,
            "dominant_emotion": dominant_emotion,
        }

    # ── Error Handling ───────────────────────────────

    @staticmethod
    def _error_result(error_msg: str) -> Dict:
        """Return error result structure."""
        from app.modules.nlp.sentiment import SentimentAnalyzer
        from app.modules.nlp.lexical import LexicalAnalyzer

        return {
            "status": "error",
            "errors": [error_msg],
            "sentiment": SentimentAnalyzer._empty_result(),
            "lexical": LexicalAnalyzer._empty_result(),
            "segment_analysis": [],
            "meta": {
                "total_words": 0,
                "total_sentences": 0,
                "crisis_detected": False,
                "dominant_emotion": "neutral",
            },
        }
