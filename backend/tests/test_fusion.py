"""
Tests for the Multimodal Fusion engine.
"""
import pytest
from app.modules.fusion.engine import FusionEngine


class TestFusionEngine:
    """Test the fusion risk scoring logic."""

    def setup_method(self):
        self.engine = FusionEngine()

    def test_low_risk_normal_features(self):
        result = self.engine.fuse(
            vision_features={"avg_valence": 0.3, "avg_arousal": 0.4},
            audio_features={"silence_ratio": 0.15, "pitch_std": 25, "speech_rate_wpm": 130},
            nlp_features={"sentiment_polarity": 0.2, "absolutist_count": 0, "crisis_detected": False},
        )
        assert result["risk_assessment"]["band"] == "Low Concern"
        assert result["risk_assessment"]["score"] < 0.4

    def test_high_risk_crisis_language(self):
        result = self.engine.fuse(
            nlp_features={"sentiment_polarity": -0.9, "absolutist_count": 5, "crisis_detected": True},
        )
        assert result["risk_assessment"]["band"] == "High Concern"
        assert result["risk_assessment"]["score"] > 0.75

    def test_contradiction_detection(self):
        result = self.engine.fuse(
            vision_features={"avg_valence": 0.6},  # smiling
            nlp_features={"sentiment_polarity": -0.8, "absolutist_count": 2, "crisis_detected": False},
        )
        contradiction_flags = [f for f in result["flags"] if f["type"] == "CONTRADICTION"]
        assert len(contradiction_flags) > 0
