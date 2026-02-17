"""
Lexical Analyzer — Rule-based linguistic feature extraction.

Extracts clinically relevant linguistic markers from text using
pattern matching and optional spaCy tokenization.

Clinical Relevance:
    - High first-person singular ratio → rumination, self-focus
    - Absolutist words ("always", "never") → cognitive distortion
    - Avoidance phrases → psychological avoidance / deflection
    - Crisis keywords → IMMEDIATE safety concern (override all other scoring)
    - Low sentence length variability → restricted thought patterns

Dependencies:
    - spaCy (optional): Better tokenization and POS tagging
    - Falls back to regex if spaCy is unavailable

Output Schema:
    {
        "pronoun_analysis": {
            "first_person_singular_count": int,
            "first_person_plural_count": int,
            "total_pronouns": int,
            "first_person_ratio": float,
            "self_focus_score": float       # 0.0-1.0 normalized
        },
        "absolutist_words": {
            "count": int,
            "frequency": float,             # per 100 words
            "found": [str]
        },
        "avoidance_phrases": {
            "count": int,
            "found": [str]
        },
        "crisis_indicators": {
            "detected": bool,
            "keywords_found": [str],
            "severity": str                 # "NONE" | "MODERATE" | "CRITICAL"
        },
        "syntax": {
            "total_sentences": int,
            "avg_sentence_length": float,
            "sentence_length_std": float,   # Variability
            "total_words": int
        }
    }
"""
import logging
import re
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


# ── Clinical Dictionaries ────────────────────────────

FIRST_PERSON_SINGULAR = {"i", "me", "my", "mine", "myself"}
FIRST_PERSON_PLURAL = {"we", "us", "our", "ours", "ourselves"}

ABSOLUTIST_WORDS = {
    "always", "never", "nothing", "everything", "completely",
    "totally", "absolutely", "entirely", "impossible", "definitely",
    "constantly", "forever", "nobody", "everyone", "all",
    "none", "every", "must", "certainly", "perfectly",
}

AVOIDANCE_PHRASES = [
    "i don't know",
    "i'm not sure",
    "i can't remember",
    "it doesn't matter",
    "whatever",
    "i don't want to talk about",
    "let's move on",
    "i'd rather not",
    "it's fine",
    "i guess",
    "not really",
    "sort of",
    "maybe",
    "i suppose",
]

# CRITICAL: These trigger immediate safety flags
CRISIS_KEYWORDS = {
    # Suicidal ideation
    "kill myself", "end my life", "want to die", "better off dead",
    "suicidal", "suicide", "no reason to live", "can't go on",
    "end it all", "not worth living",
    # Self-harm
    "hurt myself", "self-harm", "cut myself", "harm myself",
    # Homicidal ideation
    "kill someone", "hurt someone", "want to hurt",
}


class LexicalAnalyzer:
    """
    Extracts clinically significant linguistic features from text.

    Uses spaCy for tokenization when available, falls back to regex.
    All dictionaries are defined at module level for easy modification.

    Thread Safety:
        Safe for concurrent reads after initialization.
    """

    def __init__(self):
        self._nlp = None        # spaCy model (optional)
        self._spacy_loaded = False

    def _load_spacy(self):
        """Attempt to load spaCy model (called once)."""
        if self._spacy_loaded:
            return

        try:
            import spacy
            self._nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded for lexical analysis")
        except (ImportError, OSError):
            logger.warning("spaCy not available — using regex fallback for tokenization")

        self._spacy_loaded = True

    def analyze(self, text: str) -> Dict:
        """
        Extract all linguistic features from text.

        Args:
            text: Input text to analyze.

        Returns:
            Structured dict with pronoun, absolutist, avoidance, crisis, and syntax features.
            Returns empty result if text is empty (never raises).
        """
        if not text or not text.strip():
            return self._empty_result()

        if not self._spacy_loaded:
            self._load_spacy()

        text = text.strip()
        text_lower = text.lower()

        # Tokenize
        words = self._tokenize(text)
        words_lower = [w.lower() for w in words]
        sentences = self._split_sentences(text)

        # ── Analysis ──────────────────────────────
        pronoun_analysis = self._analyze_pronouns(words_lower)
        absolutist_result = self._analyze_absolutist(words_lower)
        avoidance_result = self._analyze_avoidance(text_lower)
        crisis_result = self._detect_crisis(text_lower)
        syntax_result = self._analyze_syntax(sentences, words)

        return {
            "pronoun_analysis": pronoun_analysis,
            "absolutist_words": absolutist_result,
            "avoidance_phrases": avoidance_result,
            "crisis_indicators": crisis_result,
            "syntax": syntax_result,
        }

    # ── Pronoun Analysis ─────────────────────────────

    def _analyze_pronouns(self, words: List[str]) -> Dict:
        """
        Analyze first-person pronoun usage.

        Clinical: Elevated first-person singular ratio correlates with
        depression and rumination (Rude et al., 2004).
        """
        fps_count = sum(1 for w in words if w in FIRST_PERSON_SINGULAR)
        fpp_count = sum(1 for w in words if w in FIRST_PERSON_PLURAL)
        total_words = max(len(words), 1)

        # All pronouns (approximation: any word in either set)
        total_pronouns = fps_count + fpp_count

        # Self-focus score: first-person singular as fraction of all words
        # Normalized: typical range 0.04-0.12; > 0.10 is elevated
        first_person_ratio = fps_count / total_words
        self_focus_score = min(first_person_ratio / 0.12, 1.0)  # Normalize to 0-1

        return {
            "first_person_singular_count": fps_count,
            "first_person_plural_count": fpp_count,
            "total_pronouns": total_pronouns,
            "first_person_ratio": round(first_person_ratio, 4),
            "self_focus_score": round(self_focus_score, 3),
        }

    # ── Absolutist Words ─────────────────────────────

    def _analyze_absolutist(self, words: List[str]) -> Dict:
        """
        Detect absolutist/all-or-nothing language.

        Clinical: Elevated absolutist word usage is a marker of cognitive
        distortion common in depression, anxiety, and BPD (Al-Mosaiwi & Johnstone, 2018).
        """
        found = []
        count = 0
        for w in words:
            if w in ABSOLUTIST_WORDS:
                count += 1
                if w not in found:
                    found.append(w)

        total_words = max(len(words), 1)
        frequency = (count / total_words) * 100  # per 100 words

        return {
            "count": count,
            "frequency": round(frequency, 2),
            "found": found,
        }

    # ── Avoidance Phrases ────────────────────────────

    def _analyze_avoidance(self, text_lower: str) -> Dict:
        """
        Detect avoidance/deflection language patterns.

        Clinical: Avoidance language can indicate psychological avoidance,
        dissociation, or reluctance to engage with distressing topics.
        """
        found = []
        for phrase in AVOIDANCE_PHRASES:
            if phrase in text_lower:
                found.append(phrase)

        return {
            "count": len(found),
            "found": found,
        }

    # ── Crisis Detection ─────────────────────────────

    def _detect_crisis(self, text_lower: str) -> Dict:
        """
        Detect crisis/safety keywords.

        ⚠️  CRITICAL: Any match here should trigger immediate clinician alerting.
        This overrides all other risk scoring.
        """
        found = []
        for keyword in CRISIS_KEYWORDS:
            if keyword in text_lower:
                found.append(keyword)

        if not found:
            severity = "NONE"
        elif any(kw in found for kw in {"suicidal", "suicide", "kill myself", "end my life", "want to die"}):
            severity = "CRITICAL"
        else:
            severity = "MODERATE"

        return {
            "detected": len(found) > 0,
            "keywords_found": found,
            "severity": severity,
        }

    # ── Syntax Analysis ──────────────────────────────

    def _analyze_syntax(self, sentences: List[str], words: List[str]) -> Dict:
        """
        Analyze sentence structure and variability.

        Clinical: Low sentence length variability can indicate restricted
        thought patterns or psychomotor retardation.
        """
        total_words = len(words)
        total_sentences = max(len(sentences), 1)

        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

        if not sentence_lengths:
            return {
                "total_sentences": 0,
                "avg_sentence_length": 0.0,
                "sentence_length_std": 0.0,
                "total_words": total_words,
            }

        return {
            "total_sentences": len(sentence_lengths),
            "avg_sentence_length": round(float(np.mean(sentence_lengths)), 1),
            "sentence_length_std": round(float(np.std(sentence_lengths)), 2),
            "total_words": total_words,
        }

    # ── Tokenization Helpers ─────────────────────────

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text using spaCy or regex fallback."""
        if self._nlp:
            doc = self._nlp(text)
            return [token.text for token in doc if not token.is_space]

        # Regex fallback: split on whitespace + punctuation boundaries
        return re.findall(r"\b\w+(?:'\w+)?\b", text)

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using spaCy or regex fallback."""
        if self._nlp:
            doc = self._nlp(text)
            return [sent.text.strip() for sent in doc.sents]

        # Regex fallback: split on sentence-ending punctuation
        return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

    # ── Empty Result ─────────────────────────────────

    @staticmethod
    def _empty_result() -> Dict:
        """Return empty lexical analysis structure."""
        return {
            "pronoun_analysis": {
                "first_person_singular_count": 0,
                "first_person_plural_count": 0,
                "total_pronouns": 0,
                "first_person_ratio": 0.0,
                "self_focus_score": 0.0,
            },
            "absolutist_words": {
                "count": 0,
                "frequency": 0.0,
                "found": [],
            },
            "avoidance_phrases": {
                "count": 0,
                "found": [],
            },
            "crisis_indicators": {
                "detected": False,
                "keywords_found": [],
                "severity": "NONE",
            },
            "syntax": {
                "total_sentences": 0,
                "avg_sentence_length": 0.0,
                "sentence_length_std": 0.0,
                "total_words": 0,
            },
        }
