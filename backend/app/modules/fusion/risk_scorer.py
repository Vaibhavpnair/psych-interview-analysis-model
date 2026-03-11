"""
Risk Scorer — Weighted behavioral risk assessment.

Computes sub-scores from multimodal features and combines them into
a single risk score with explainability.

Strategy:
    1. Compute domain sub-scores (psychomotor, cognitive, affective, behavioral)
    2. Apply configurable weights to each domain
    3. Apply crisis override (any crisis keyword → immediate HIGH)
    4. Generate human-readable contributor explanations

IMPORTANT: This is a DECISION-SUPPORT tool. It does NOT diagnose.
    Output must always be framed as "behavioral concern indicators"
    and never as clinical diagnoses.

Sub-Score Domains:
    ┌─────────────────────┬──────────────────────────────────┬────────┐
    │ Domain              │ Features Used                    │ Weight │
    ├─────────────────────┼──────────────────────────────────┼────────┤
    │ Psychomotor         │ Silence ratio, pitch variance,   │  0.30  │
    │                     │ speech rate, facial stability     │        │
    ├─────────────────────┼──────────────────────────────────┼────────┤
    │ Cognitive           │ Negative sentiment, absolutist   │  0.25  │
    │                     │ words, sentence variability       │        │
    ├─────────────────────┼──────────────────────────────────┼────────┤
    │ Affective           │ Valence (face), emotion dist,    │  0.25  │
    │                     │ arousal, self-focus ratio         │        │
    ├─────────────────────┼──────────────────────────────────┼────────┤
    │ Behavioral          │ Filler rate, response latency,   │  0.20  │
    │                     │ avoidance phrases, pauses         │        │
    └─────────────────────┴──────────────────────────────────┴────────┘

Output Schema:
    {
        "raw_score": float,         # 0.0 - 1.0
        "risk_band": str,           # "Low Concern" | "Moderate Concern" | "High Concern"
        "sub_scores": {
            "psychomotor": float,
            "cognitive": float,
            "affective": float,
            "behavioral": float
        },
        "flags": [
            {"type": str, "severity": str, "description": str}
        ],
        "contributors": [str],      # Human-readable explanations
        "crisis_override": bool
    }
"""
import logging
from typing import Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ── Configurable Weights ─────────────────────────────

DOMAIN_WEIGHTS = {
    "psychomotor": 0.30,
    "cognitive": 0.25,
    "affective": 0.25,
    "behavioral": 0.20,
}

# Risk band thresholds
BAND_THRESHOLDS = {
    "high": 0.65,
    "moderate": 0.35,
}


class RiskScorer:
    """
    Calculates behavioral risk scores from multimodal features.

    Uses a hybrid approach:
        - Rule-based flags for specific clinical indicators
        - Weighted numerical scoring for overall risk assessment
        - Crisis keyword override for immediate safety escalation

    This is NOT a diagnostic tool. Outputs are framed as behavioral
    concern indicators to support clinical decision-making.
    """

    def __init__(self, weights: Dict = None):
        """
        Args:
            weights: Optional custom domain weights. Must sum to 1.0.
        """
        self.weights = weights or DOMAIN_WEIGHTS

    def calculate(
        self,
        audio: Dict,
        nlp: Dict,
        vision: Dict,
    ) -> Dict:
        """
        Calculate risk score from multimodal features.

        Args:
            audio: Output from AudioProcessor.speech_features
            nlp: Output from NLPProcessor (sentiment + lexical)
            vision: Output from VisionProcessor (aggregate + stability)

        Returns:
            Structured risk assessment with score, band, flags, and explanations.
        """
        flags = []
        contributors = []

        # ── Domain Sub-Scores ────────────────────────

        psychomotor = self._score_psychomotor(audio, vision, flags, contributors)
        cognitive = self._score_cognitive(nlp, flags, contributors)
        affective = self._score_affective(nlp, vision, flags, contributors)
        behavioral = self._score_behavioral(audio, nlp, flags, contributors)

        sub_scores = {
            "psychomotor": round(psychomotor, 3),
            "cognitive": round(cognitive, 3),
            "affective": round(affective, 3),
            "behavioral": round(behavioral, 3),
        }

        # ── Weighted Combination ─────────────────────

        raw_score = (
            psychomotor * self.weights["psychomotor"]
            + cognitive * self.weights["cognitive"]
            + affective * self.weights["affective"]
            + behavioral * self.weights["behavioral"]
        )

        # ── Crisis Override ──────────────────────────
        crisis = nlp.get("lexical", {}).get("crisis_indicators", {})
        crisis_detected = crisis.get("detected", False)

        if crisis_detected:
            raw_score = max(raw_score, 0.85)
            flags.append({
                "type": "CRISIS",
                "severity": crisis.get("severity", "CRITICAL"),
                "description": (
                    f"Crisis language detected: {', '.join(crisis.get('keywords_found', []))}"
                ),
            })
            contributors.append("⚠️ CRISIS: Safety-related language detected — immediate review required")

        # ── Risk Band ────────────────────────────────
        raw_score = float(np.clip(raw_score, 0.0, 1.0))

        if raw_score >= BAND_THRESHOLDS["high"]:
            risk_band = "High Concern"
        elif raw_score >= BAND_THRESHOLDS["moderate"]:
            risk_band = "Moderate Concern"
        else:
            risk_band = "Low Concern"

        return {
            "raw_score": round(raw_score, 3),
            "risk_band": risk_band,
            "sub_scores": sub_scores,
            "flags": flags,
            "contributors": contributors,
            "crisis_override": crisis_detected,
        }

    # ── Domain Scoring Functions ─────────────────────

    def _score_psychomotor(
        self, audio: Dict, vision: Dict, flags: List, contributors: List
    ) -> float:
        """
        Psychomotor retardation indicators.

        High score = concerning level of motor/speech slowing.
        """
        speech = audio.get("speech_features", audio)
        prosody = audio.get("prosody", {})
        stability = vision.get("stability", {})

        # Speech rate: normal 120-160 WPM, below 80 is concerning
        speech_rate = speech.get("speech_rate_wpm", 120)
        rate_score = float(np.clip(1.0 - (speech_rate / 120.0), 0.0, 1.0))

        # Silence ratio: > 0.4 is concerning
        silence_ratio = prosody.get("silence", {}).get("ratio", 0)
        silence_score = float(np.clip(silence_ratio / 0.6, 0.0, 1.0))

        # Pitch variance: low variance = monotone = psychomotor slowing
        pitch_std = prosody.get("pitch", {}).get("std_hz", 20)
        pitch_score = float(np.clip(1.0 - (pitch_std / 40.0), 0.0, 1.0))

        # Facial stability: very high stability = flat affect
        emotion_stability = stability.get("emotion_stability_score", 0.5)
        face_flat_score = float(np.clip((emotion_stability - 0.7) / 0.3, 0.0, 1.0))

        score = (
            rate_score * 0.25
            + silence_score * 0.30
            + pitch_score * 0.25
            + face_flat_score * 0.20
        )

        if score > 0.55:
            severity = "HIGH" if score > 0.75 else "MODERATE"
            flags.append({
                "type": "PSYCHOMOTOR",
                "severity": severity,
                "description": f"Psychomotor retardation indicators (score: {score:.2f})",
            })
            details = []
            if rate_score > 0.4:
                details.append(f"slow speech ({speech_rate:.0f} WPM)")
            if silence_score > 0.4:
                details.append(f"high silence ({silence_ratio:.0%})")
            if pitch_score > 0.4:
                details.append(f"low pitch variance ({pitch_std:.1f} Hz)")
            if face_flat_score > 0.3:
                details.append("flat facial affect")
            contributors.append(f"Psychomotor: {', '.join(details)}")

        return score

    def _score_cognitive(
        self, nlp: Dict, flags: List, contributors: List
    ) -> float:
        """
        Cognitive distortion indicators.

        High score = concerning level of negative/rigid thinking.
        """
        sentiment = nlp.get("sentiment", {})
        lexical = nlp.get("lexical", {})

        # Negative sentiment: compound < -0.3 is concerning
        compound = sentiment.get("polarity", {}).get("compound", 0)
        neg_score = float(np.clip(abs(min(compound, 0)) / 0.6, 0.0, 1.0))

        # Absolutist words: > 3 per 100 words is elevated
        abs_freq = lexical.get("absolutist_words", {}).get("frequency", 0)
        abs_score = float(np.clip(abs_freq / 5.0, 0.0, 1.0))

        # Sentence variability: low std = rigid thought patterns
        sent_std = lexical.get("syntax", {}).get("sentence_length_std", 5)
        rigidity_score = float(np.clip(1.0 - (sent_std / 8.0), 0.0, 1.0))

        # Dominant negative emotion
        emotions = sentiment.get("emotions", {})
        sadness = emotions.get("sadness", 0)
        fear = emotions.get("fear", 0)
        neg_emotion_score = float(np.clip((sadness + fear) / 1.0, 0.0, 1.0))

        score = (
            neg_score * 0.35
            + abs_score * 0.20
            + rigidity_score * 0.15
            + neg_emotion_score * 0.30
        )

        if score > 0.5:
            severity = "HIGH" if score > 0.7 else "MODERATE"
            flags.append({
                "type": "COGNITIVE",
                "severity": severity,
                "description": f"Cognitive distortion indicators (score: {score:.2f})",
            })
            details = []
            if neg_score > 0.4:
                details.append(f"negative sentiment ({compound:.2f})")
            if abs_score > 0.3:
                details.append(f"absolutist language ({abs_freq:.1f}/100 words)")
            if neg_emotion_score > 0.4:
                details.append(f"sadness/fear ({sadness:.2f}/{fear:.2f})")
            contributors.append(f"Cognitive: {', '.join(details)}")

        return score

    def _score_affective(
        self, nlp: Dict, vision: Dict, flags: List, contributors: List
    ) -> float:
        """
        Affective dysregulation indicators.

        Combines facial affect with linguistic self-focus.
        """
        aggregate = vision.get("aggregate", {})
        lexical = nlp.get("lexical", {})

        # Facial valence: persistent negative valence
        valence = aggregate.get("valence_mean", 0)
        neg_valence_score = float(np.clip(abs(min(valence, 0)) / 0.5, 0.0, 1.0))

        # Low arousal: emotional blunting
        arousal = aggregate.get("arousal_mean", 0.3)
        low_arousal_score = float(np.clip(1.0 - (arousal / 0.4), 0.0, 1.0))

        # Self-focus: elevated first-person pronoun ratio
        self_focus = lexical.get("pronoun_analysis", {}).get("self_focus_score", 0)

        score = (
            neg_valence_score * 0.40
            + low_arousal_score * 0.30
            + self_focus * 0.30
        )

        if score > 0.5:
            severity = "HIGH" if score > 0.7 else "MODERATE"
            flags.append({
                "type": "AFFECTIVE",
                "severity": severity,
                "description": f"Affective concern indicators (score: {score:.2f})",
            })
            details = []
            if neg_valence_score > 0.3:
                details.append(f"negative facial affect (valence: {valence:.2f})")
            if low_arousal_score > 0.3:
                details.append(f"low arousal ({arousal:.2f})")
            if self_focus > 0.5:
                details.append(f"elevated self-focus ({self_focus:.2f})")
            contributors.append(f"Affective: {', '.join(details)}")

        return score

    def _score_behavioral(
        self, audio: Dict, nlp: Dict, flags: List, contributors: List
    ) -> float:
        """
        Behavioral pattern indicators.

        Captures avoidance, disfluency, and response patterns.
        """
        speech = audio.get("speech_features", audio)
        prosody = audio.get("prosody", {})
        lexical = nlp.get("lexical", {})

        # Filler word rate: > 5/min is elevated
        filler_rate = speech.get("filler_words", {}).get("rate_per_minute", 0)
        filler_score = float(np.clip(filler_rate / 8.0, 0.0, 1.0))

        # Response latency: > 3s initial delay is concerning
        latency_ms = speech.get("response_latency_ms", 0)
        latency_score = float(np.clip((latency_ms - 1000) / 4000, 0.0, 1.0))

        # Long pauses: more than 3 pauses > 2s
        long_pauses = prosody.get("pauses", {}).get("long_pause_count", 0)
        pause_score = float(np.clip(long_pauses / 5.0, 0.0, 1.0))

        # Avoidance phrases
        avoidance_count = lexical.get("avoidance_phrases", {}).get("count", 0)
        avoidance_score = float(np.clip(avoidance_count / 5.0, 0.0, 1.0))

        score = (
            filler_score * 0.20
            + latency_score * 0.25
            + pause_score * 0.25
            + avoidance_score * 0.30
        )

        if score > 0.5:
            severity = "HIGH" if score > 0.7 else "MODERATE"
            flags.append({
                "type": "BEHAVIORAL",
                "severity": severity,
                "description": f"Behavioral pattern indicators (score: {score:.2f})",
            })
            details = []
            if filler_score > 0.3:
                details.append(f"high filler rate ({filler_rate:.1f}/min)")
            if latency_score > 0.3:
                details.append(f"delayed responses ({latency_ms:.0f}ms)")
            if pause_score > 0.3:
                details.append(f"{long_pauses} long pauses")
            if avoidance_score > 0.3:
                details.append(f"{avoidance_count} avoidance phrases")
            contributors.append(f"Behavioral: {', '.join(details)}")

        return score
