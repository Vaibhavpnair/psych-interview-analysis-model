"""
Sentiment Analyzer — VADER + HuggingFace emotion classification.

Architecture:
    Layer 1: VADER (always available, lightweight, rule-based polarity)
    Layer 2: HuggingFace Transformer (optional, GPU/CPU emotion classification)

Model Loading Strategy:
    - Models are loaded ONCE on first call and cached as instance attributes.
    - The transformer pipeline is optional — if unavailable, VADER alone is used.
    - Thread-safe for read operations after initialization.

Clinical Relevance:
    - Persistent negative polarity → depressive cognition
    - Emotional category distribution → affect range assessment
    - Compound score trajectory → mood tracking across sessions

Output Schema:
    {
        "polarity": {
            "positive": float,
            "negative": float,
            "neutral": float,
            "compound": float       # -1.0 (most negative) to 1.0 (most positive)
        },
        "label": str,               # "positive" | "negative" | "neutral"
        "emotions": {
            "anger": float,
            "disgust": float,
            "fear": float,
            "joy": float,
            "sadness": float,
            "surprise": float,
            "neutral": float
        },
        "emotion_model_used": bool
    }
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Dual-layer sentiment and emotion analyzer.

    Layer 1 (VADER): Fast, rule-based polarity scoring. Always available.
    Layer 2 (Transformer): HuggingFace distilRoBERTa emotion classifier. Optional.

    The transformer model (j-hartmann/emotion-english-distilroberta-base) is
    loaded once and reused across requests — never reloaded per call.
    """

    # Default emotion categories (match HuggingFace model output)
    EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]

    def __init__(self, use_transformer: bool = True):
        """
        Args:
            use_transformer: Whether to attempt loading the HuggingFace emotion model.
                             Set False for lightweight mode (VADER only).
        """
        self._use_transformer = use_transformer
        self._vader = None
        self._transformer = None
        self._models_loaded = False

    def _load_models(self):
        """
        Load sentiment models (called once, cached for lifetime of instance).
        """
        if self._models_loaded:
            return

        # ── Layer 1: VADER (lightweight, always attempted) ──
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer loaded")
        except ImportError:
            logger.warning("vaderSentiment not installed — polarity analysis degraded")

        # ── Layer 2: HuggingFace Transformer (optional) ──
        if self._use_transformer:
            try:
                from transformers import pipeline
                self._transformer = pipeline(
                    "text-classification",
                    model="j-hartmann/emotion-english-distilroberta-base",
                    top_k=None,
                    device=-1,  # CPU — use 0 for GPU
                )
                logger.info("HuggingFace emotion transformer loaded")
            except Exception as e:
                logger.info(f"Transformer emotion model not loaded (optional): {e}")

        self._models_loaded = True

    @property
    def is_available(self) -> bool:
        """True if at least VADER is loaded."""
        if not self._models_loaded:
            self._load_models()
        return self._vader is not None

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment and emotion of a text string.

        Args:
            text: Input text to analyze.

        Returns:
            Structured dict with polarity scores, label, and emotion distribution.
            Returns empty result if no models available (never raises).
        """
        if not self._models_loaded:
            self._load_models()

        if not text or not text.strip():
            return self._empty_result()

        text = text.strip()
        result = self._empty_result()

        # ── Layer 1: VADER Polarity ──────────────────
        if self._vader:
            try:
                scores = self._vader.polarity_scores(text)
                result["polarity"] = {
                    "positive": round(scores.get("pos", 0.0), 4),
                    "negative": round(scores.get("neg", 0.0), 4),
                    "neutral": round(scores.get("neu", 0.0), 4),
                    "compound": round(scores.get("compound", 0.0), 4),
                }

                # Determine label from compound score
                compound = scores.get("compound", 0.0)
                if compound >= 0.05:
                    result["label"] = "positive"
                elif compound <= -0.05:
                    result["label"] = "negative"
                else:
                    result["label"] = "neutral"

            except Exception as e:
                logger.error(f"VADER analysis failed: {e}")

        # ── Layer 2: Transformer Emotions ────────────
        if self._transformer:
            try:
                # Truncate to avoid transformer max length issues
                truncated = text[:512]
                predictions = self._transformer(truncated)

                if predictions and isinstance(predictions[0], list):
                    emotions = {}
                    for pred in predictions[0]:
                        label = pred["label"].lower()
                        score = round(pred["score"], 4)
                        emotions[label] = score

                    result["emotions"] = emotions
                    result["emotion_model_used"] = True

            except Exception as e:
                logger.error(f"Transformer emotion analysis failed: {e}")

        return result

    def analyze_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for each transcript segment independently.

        Args:
            segments: List of dicts with at least {"text": str, "start": float, "end": float}

        Returns:
            List of dicts, each with original segment data + sentiment analysis.
        """
        results = []
        for seg in segments:
            text = seg.get("text", "")
            sentiment = self.analyze(text)
            results.append({
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "text": text,
                "sentiment": sentiment,
            })
        return results

    @staticmethod
    def _empty_result() -> Dict:
        """Return empty sentiment structure."""
        return {
            "polarity": {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "compound": 0.0,
            },
            "label": "neutral",
            "emotions": {label: 0.0 for label in SentimentAnalyzer.EMOTION_LABELS},
            "emotion_model_used": False,
        }
