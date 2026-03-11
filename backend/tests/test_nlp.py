"""
Tests for the NLP lexical analysis module.
"""
import pytest
from app.modules.nlp.lexical import LexicalAnalyzer


class TestLexicalAnalyzer:
    """Test lexical feature extraction with clinical patterns."""

    def setup_method(self):
        self.analyzer = LexicalAnalyzer()

    def test_empty_text(self):
        result = self.analyzer.analyze("")
        assert result["word_count"] == 0

    def test_first_person_detection(self):
        text = "I feel like I am always tired and my energy is gone."
        result = self.analyzer.analyze(text)
        assert result["first_person_count"] >= 3
        assert result["first_person_ratio"] > 0.1

    def test_absolutist_detection(self):
        text = "Nothing ever changes and I will never get better. Everything is hopeless."
        result = self.analyzer.analyze(text)
        assert result["absolutist_count"] >= 3
        assert "never" in result["absolutist_terms"]

    def test_avoidance_detection(self):
        text = "I don't know, maybe we can skip this question."
        result = self.analyzer.analyze(text)
        assert result["avoidance_detected"] is True

    def test_crisis_detection(self):
        text = "I just want to die and end my life."
        result = self.analyzer.analyze(text)
        assert result["crisis_detected"] is True

    def test_no_crisis_in_normal_text(self):
        text = "I had a good day today and enjoyed my lunch."
        result = self.analyzer.analyze(text)
        assert result["crisis_detected"] is False
