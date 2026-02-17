"""
Contradiction Detector — Cross-modal mismatch identification.

Identifies inconsistencies between modalities that may indicate:
    - Incongruent affect (saying "I'm fine" while showing sadness)
    - Emotional masking (positive words + flat/negative facial affect)
    - Dissociation indicators (monotone delivery + distressing content)

Clinical Relevance:
    Cross-modal contradictions are significant clinical markers. Patients
    may verbally deny distress while nonverbal channels reveal it. These
    mismatches should be flagged for clinician attention.

Contradiction Types:
    1. TEXT_VS_FACE — Verbal sentiment contradicts facial valence
    2. AUDIO_VS_TEXT — Prosody contradicts linguistic content
    3. FACE_VS_AUDIO — Facial arousal contradicts vocal arousal
    4. MASKING — Positive language + negative nonverbal signals

Output Schema:
    {
        "contradictions": [
            {
                "type": str,
                "modalities": [str, str],
                "description": str,
                "severity": str,            # "LOW" | "MODERATE" | "HIGH"
                "clinical_note": str,
                "evidence": {
                    "modality_a": {label: str, value: float},
                    "modality_b": {label: str, value: float}
                }
            }
        ],
        "contradiction_count": int,
        "highest_severity": str,
        "overall_incongruence_score": float   # 0-1
    }
"""
import logging
from typing import Dict, List

import numpy as np

logger = logging.getLogger(__name__)


# Mismatch thresholds (tunable)
TEXT_FACE_THRESHOLD = 0.4       # Min polarity-valence gap to flag
AUDIO_TEXT_THRESHOLD = 0.3      # Monotone prosody + negative content gap
FACE_AUDIO_THRESHOLD = 0.35    # Face arousal vs vocal energy gap
MASKING_THRESHOLD = 0.3         # Positive words + negative face gap


class ContradictionDetector:
    """
    Detects cross-modal contradictions between text, audio, and vision.

    Each detection rule compares features from two modalities and
    flags significant mismatches with severity levels and clinical notes.
    """

    def detect(
        self,
        audio: Dict,
        nlp: Dict,
        vision: Dict,
    ) -> Dict:
        """
        Run all contradiction detection rules.

        Args:
            audio: Output from AudioProcessor
            nlp: Output from NLPProcessor
            vision: Output from VisionProcessor

        Returns:
            Structured contradiction report.
        """
        contradictions = []

        # ── Rule 1: Text Sentiment vs Facial Valence ─
        self._check_text_vs_face(nlp, vision, contradictions)

        # ── Rule 2: Audio Prosody vs Text Content ────
        self._check_audio_vs_text(audio, nlp, contradictions)

        # ── Rule 3: Facial Arousal vs Vocal Energy ───
        self._check_face_vs_audio(vision, audio, contradictions)

        # ── Rule 4: Emotional Masking ────────────────
        self._check_masking(nlp, vision, audio, contradictions)

        # Overall incongruence score
        if contradictions:
            severity_weights = {"LOW": 0.2, "MODERATE": 0.5, "HIGH": 0.9}
            weighted = [severity_weights.get(c["severity"], 0.3) for c in contradictions]
            incongruence = float(np.clip(np.mean(weighted), 0.0, 1.0))
            highest = max(contradictions, key=lambda c: severity_weights.get(c["severity"], 0))
            highest_severity = highest["severity"]
        else:
            incongruence = 0.0
            highest_severity = "NONE"

        return {
            "contradictions": contradictions,
            "contradiction_count": len(contradictions),
            "highest_severity": highest_severity,
            "overall_incongruence_score": round(incongruence, 3),
        }

    # ── Detection Rules ──────────────────────────────

    def _check_text_vs_face(self, nlp: Dict, vision: Dict, out: List):
        """
        Detect: Positive/neutral language + negative facial affect (or vice versa).

        Example: Patient says "I'm doing fine" while face shows AU4 + AU15 (sadness).
        """
        compound = nlp.get("sentiment", {}).get("polarity", {}).get("compound", 0)
        valence = vision.get("aggregate", {}).get("valence_mean", 0)

        gap = compound - valence  # positive gap = text positive, face negative

        if abs(gap) > TEXT_FACE_THRESHOLD:
            if gap > 0:
                desc = "Positive verbal sentiment contradicts negative facial expression"
                clinical = "Patient may be masking negative emotions or minimizing distress"
            else:
                desc = "Negative verbal sentiment contradicts positive/neutral facial expression"
                clinical = "Verbal expression may not represent actual emotional state"

            severity = "HIGH" if abs(gap) > 0.7 else "MODERATE"

            out.append({
                "type": "TEXT_VS_FACE",
                "modalities": ["NLP", "Vision"],
                "description": desc,
                "severity": severity,
                "clinical_note": clinical,
                "evidence": {
                    "modality_a": {"label": "text_sentiment", "value": round(compound, 3)},
                    "modality_b": {"label": "facial_valence", "value": round(valence, 3)},
                },
            })

    def _check_audio_vs_text(self, audio: Dict, nlp: Dict, out: List):
        """
        Detect: Monotone/flat prosody + emotionally charged text content.

        Example: Patient discusses traumatic experience in completely flat voice.
        """
        prosody = audio.get("prosody", {})
        pitch_std = prosody.get("pitch", {}).get("std_hz", 20)
        energy_std = prosody.get("energy", {}).get("std_db", 5)

        # Normalized monotone score (low pitch + energy variance)
        monotone = float(np.clip(1.0 - (pitch_std / 30.0), 0.0, 1.0))

        # Text emotional intensity
        emotions = nlp.get("sentiment", {}).get("emotions", {})
        max_emotion = max(emotions.values()) if emotions else 0
        neutral_score = emotions.get("neutral", 0.5)
        emotional_intensity = max_emotion * (1 - neutral_score)

        gap = monotone - (1 - emotional_intensity)

        if monotone > 0.6 and emotional_intensity > 0.4 and gap > AUDIO_TEXT_THRESHOLD:
            severity = "HIGH" if gap > 0.5 else "MODERATE"

            out.append({
                "type": "AUDIO_VS_TEXT",
                "modalities": ["Audio", "NLP"],
                "description": "Monotone vocal delivery contradicts emotionally charged content",
                "severity": severity,
                "clinical_note": (
                    "Flat prosody with emotional content may indicate "
                    "emotional suppression, dissociation, or psychomotor retardation"
                ),
                "evidence": {
                    "modality_a": {"label": "monotone_score", "value": round(monotone, 3)},
                    "modality_b": {"label": "emotional_intensity", "value": round(emotional_intensity, 3)},
                },
            })

    def _check_face_vs_audio(self, vision: Dict, audio: Dict, out: List):
        """
        Detect: High facial arousal + low vocal energy (or vice versa).

        Example: Agitated facial expression but very quiet, slow speech.
        """
        face_arousal = vision.get("aggregate", {}).get("arousal_mean", 0.3)
        prosody = audio.get("prosody", {})
        energy_range = prosody.get("energy", {}).get("dynamic_range_db", 15)

        # Normalize vocal energy (typical range 10-40 dB)
        vocal_energy = float(np.clip(energy_range / 35.0, 0.0, 1.0))

        gap = abs(face_arousal - vocal_energy)

        if gap > FACE_AUDIO_THRESHOLD:
            if face_arousal > vocal_energy:
                desc = "Facial agitation contradicts calm/flat vocal delivery"
                clinical = "Internal agitation may not be expressed vocally — assess for anxiety"
            else:
                desc = "Vocal agitation contradicts calm facial expression"
                clinical = "Patient may be controlling facial expression while vocally distressed"

            severity = "MODERATE" if gap < 0.5 else "HIGH"

            out.append({
                "type": "FACE_VS_AUDIO",
                "modalities": ["Vision", "Audio"],
                "description": desc,
                "severity": severity,
                "clinical_note": clinical,
                "evidence": {
                    "modality_a": {"label": "facial_arousal", "value": round(face_arousal, 3)},
                    "modality_b": {"label": "vocal_energy", "value": round(vocal_energy, 3)},
                },
            })

    def _check_masking(self, nlp: Dict, vision: Dict, audio: Dict, out: List):
        """
        Detect: Emotional masking — positive language + multiple negative nonverbal signals.

        This is the most clinically significant contradiction pattern.
        """
        compound = nlp.get("sentiment", {}).get("polarity", {}).get("compound", 0)
        valence = vision.get("aggregate", {}).get("valence_mean", 0)
        prosody = audio.get("prosody", {})
        silence_ratio = prosody.get("silence", {}).get("ratio", 0)

        # Masking: positive words + negative face + high silence
        if compound > 0.1 and valence < -0.1 and silence_ratio > 0.3:
            gap = compound - valence
            if gap > MASKING_THRESHOLD:
                out.append({
                    "type": "MASKING",
                    "modalities": ["NLP", "Vision", "Audio"],
                    "description": "Potential emotional masking: positive language with negative nonverbal signals",
                    "severity": "HIGH",
                    "clinical_note": (
                        "Patient presents positively verbally but nonverbal channels suggest "
                        "distress. This pattern may indicate social desirability bias, "
                        "minimization of symptoms, or difficulty expressing emotions."
                    ),
                    "evidence": {
                        "modality_a": {"label": "text_sentiment", "value": round(compound, 3)},
                        "modality_b": {"label": "facial_valence", "value": round(valence, 3)},
                    },
                })
