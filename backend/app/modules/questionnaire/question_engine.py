"""
QuestionEngine — orchestrates a structured assessment session with
per-question multimodal capture (audio + vision + optional NLP).

Each question gets its own accumulators. When the clinician submits a
self-report score, the engine snapshots the accumulated data into a
QuestionResponse, resets accumulators, and advances to the next question.

Enhanced with:
  - Hesitation markers (from audio)
  - Blink rate estimation (from eye_open_ratio samples)
  - Facial stability (1 - std(valence))
  - Emotional intensity (mean(|valence| + arousal) / 2)
  - Confidence proxy (composite multimodal signal)
  - Pause/resume and clinician override support

No diagnosis logic — decision-support only.
"""

import time
import uuid
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.modules.questionnaire.question_bank import (
    question_bank,
    RESPONSE_OPTIONS,
    DOMAIN_INFO,
    Question,
)

logger = logging.getLogger(__name__)


# ── Per-Question Accumulators ──────────────────────────────
@dataclass
class _QuestionAccumulator:
    """Running sums for multimodal data while a question is active."""
    started_at: float = field(default_factory=time.time)

    # Audio accumulators
    audio_segments: int = 0
    pitch_sum: float = 0.0
    pitch_std_sum: float = 0.0
    energy_rms_sum: float = 0.0
    energy_db_sum: float = 0.0
    speech_rate_sum: float = 0.0
    silence_ratio_sum: float = 0.0
    pause_count_total: int = 0
    word_count_total: int = 0
    hesitation_count_total: int = 0
    transcripts: List[str] = field(default_factory=list)

    # Vision accumulators
    video_frames: int = 0
    face_detected_frames: int = 0
    valence_sum: float = 0.0
    arousal_sum: float = 0.0
    smile_sum: float = 0.0
    brow_furrow_sum: float = 0.0
    # Sample-level lists for derived metrics
    eye_open_samples: List[float] = field(default_factory=list)
    valence_samples: List[float] = field(default_factory=list)
    arousal_samples: List[float] = field(default_factory=list)

    # NLP accumulators
    sentiment_sum: float = 0.0
    sentiment_count: int = 0
    absolutist_count: int = 0
    first_person_count: int = 0

    # Pause state
    is_paused: bool = False
    pause_start: Optional[float] = None
    total_pause_time: float = 0.0


# ── Per-Question Snapshot ──────────────────────────────────
@dataclass
class QuestionResponse:
    """Finalized per-question data after the clinician submits a score."""
    question_id: str
    domain: str
    question_text: str
    self_report_score: int  # 0–4

    # Timing
    duration_seconds: float

    # Audio summary
    transcript: str
    audio_segments: int
    avg_pitch: float
    pitch_variance: float
    avg_energy_rms: float
    avg_energy_db: float
    avg_speech_rate: float
    avg_silence_ratio: float
    total_pauses: int
    total_words: int
    hesitation_count: int
    hesitation_ratio: float

    # Vision summary
    video_frames: int
    face_detected_frames: int
    avg_valence: float
    avg_arousal: float
    avg_smile: float
    avg_brow_furrow: float
    blink_rate: float            # estimated blinks per minute
    facial_stability: float      # 0 = unstable, 1 = stable
    emotional_intensity: float   # mean(|valence| + arousal) / 2

    # NLP summary
    avg_sentiment: float
    absolutist_words: int
    first_person_pronouns: int

    # Composite
    confidence_proxy: float      # 0–1 multimodal confidence signal


# ── Derived Metric Helpers ─────────────────────────────────
def _estimate_blink_rate(eye_open_samples: List[float], duration_sec: float) -> float:
    """
    Estimate blink rate from eye_open_ratio samples.
    A blink is a sample where eye_open_ratio drops below a threshold
    relative to the running median.
    """
    if len(eye_open_samples) < 5 or duration_sec <= 0:
        return 0.0

    import numpy as np
    arr = np.array(eye_open_samples)
    median_open = np.median(arr)
    if median_open <= 0:
        return 0.0

    # Blink = eye_open_ratio < 50% of median
    threshold = median_open * 0.5
    blink_frames = int(np.sum(arr < threshold))

    # Convert to blinks per minute
    fps = len(eye_open_samples) / duration_sec if duration_sec > 0 else 5
    # A typical blink lasts 300-400ms at 5fps ≈ 1-2 frames
    blink_count = max(blink_frames // 2, blink_frames)  # rough estimate
    blinks_per_min = (blink_count / duration_sec) * 60 if duration_sec > 0 else 0.0
    return round(blinks_per_min, 1)


def _compute_facial_stability(valence_samples: List[float]) -> float:
    """1 - std(valence), clamped to [0, 1]. Higher = more stable."""
    if len(valence_samples) < 2:
        return 1.0
    import numpy as np
    std = float(np.std(valence_samples))
    return round(max(0.0, min(1.0, 1.0 - std)), 3)


def _compute_emotional_intensity(valence_samples: List[float], arousal_samples: List[float]) -> float:
    """mean(|valence| + arousal) / 2, clamped to [0, 1]."""
    if not valence_samples or not arousal_samples:
        return 0.0
    import numpy as np
    abs_val = np.mean(np.abs(valence_samples))
    avg_aro = np.mean(arousal_samples)
    intensity = (abs_val + avg_aro) / 2.0
    return round(max(0.0, min(1.0, intensity)), 3)


def _compute_confidence_proxy(
    speech_rate: float,
    hesitation_ratio: float,
    facial_stability: float,
    pitch_variance: float,
    silence_ratio: float,
) -> float:
    """
    Composite confidence proxy (0–1). Higher = more confident.
    Based on: low hesitation, moderate speech rate, stable face, low pitch variance.
    """
    # Speech rate score: optimal ~120-160 WPM
    if speech_rate <= 0:
        rate_score = 0.5
    elif 120 <= speech_rate <= 160:
        rate_score = 1.0
    elif speech_rate < 120:
        rate_score = max(0.3, speech_rate / 120)
    else:
        rate_score = max(0.3, 1.0 - (speech_rate - 160) / 200)

    # Hesitation score: lower is better
    hes_score = max(0.0, 1.0 - hesitation_ratio * 5)

    # Pitch variance score: lower is more confident (but 0 = no speech)
    pv_score = max(0.0, 1.0 - min(pitch_variance / 80, 1.0)) if pitch_variance > 0 else 0.5

    # Silence score: moderate silence is fine, high is less confident
    sil_score = max(0.0, 1.0 - silence_ratio * 2)

    # Weighted composite
    proxy = (
        0.25 * rate_score +
        0.25 * hes_score +
        0.20 * facial_stability +
        0.15 * pv_score +
        0.15 * sil_score
    )
    return round(max(0.0, min(1.0, proxy)), 3)


# ── Assessment Session State ──────────────────────────────
class _AssessmentSession:
    """State for one full assessment run through 23 questions."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.current_index = 0
        self.responses: List[QuestionResponse] = []
        self.accumulator = _QuestionAccumulator()
        self.is_paused = False

    @property
    def is_complete(self) -> bool:
        return self.current_index >= question_bank.total_questions

    @property
    def current_question(self) -> Optional[Question]:
        return question_bank.get_question_at_index(self.current_index)

    def reset_accumulator(self):
        self.accumulator = _QuestionAccumulator()


# ── QuestionEngine ─────────────────────────────────────────
class QuestionEngine:
    """Manages assessment sessions with per-question multimodal storage."""

    def __init__(self):
        self._sessions: Dict[str, _AssessmentSession] = {}

    def start_assessment(self) -> tuple:
        session_id = f"assess-{uuid.uuid4().hex[:8]}"
        session = _AssessmentSession(session_id)
        self._sessions[session_id] = session
        logger.info(f"Assessment started: {session_id}")
        return session_id, session.current_question

    def get_session(self, session_id: str) -> Optional[_AssessmentSession]:
        return self._sessions.get(session_id)

    def get_current_question(self, session_id: str) -> Optional[Question]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        return session.current_question

    # ── Pause / Resume ──────────────────────────────────────

    def pause(self, session_id: str):
        session = self._sessions.get(session_id)
        if session and not session.is_paused:
            session.is_paused = True
            session.accumulator.is_paused = True
            session.accumulator.pause_start = time.time()
            logger.info(f"Assessment paused: {session_id}")

    def resume(self, session_id: str):
        session = self._sessions.get(session_id)
        if session and session.is_paused:
            session.is_paused = False
            session.accumulator.is_paused = False
            if session.accumulator.pause_start:
                session.accumulator.total_pause_time += time.time() - session.accumulator.pause_start
                session.accumulator.pause_start = None
            logger.info(f"Assessment resumed: {session_id}")

    # ── Multimodal Accumulators ─────────────────────────────

    def accumulate_audio(self, session_id: str, features: dict):
        session = self._sessions.get(session_id)
        if not session or session.is_complete or session.is_paused:
            return

        acc = session.accumulator
        acc.audio_segments += 1
        acc.pitch_sum += features.get("pitch_mean", 0.0)
        acc.pitch_std_sum += features.get("pitch_std", 0.0)
        acc.energy_rms_sum += features.get("energy_rms", 0.0)
        acc.energy_db_sum += features.get("energy_db", 0.0)
        acc.speech_rate_sum += features.get("speech_rate_wpm", 0.0)
        acc.silence_ratio_sum += features.get("silence_ratio", 0.0)
        acc.pause_count_total += features.get("pause_count", 0)
        acc.word_count_total += features.get("word_count", 0)
        acc.hesitation_count_total += features.get("hesitation_count", 0)

    def accumulate_transcript(self, session_id: str, text: str):
        session = self._sessions.get(session_id)
        if not session or session.is_complete or session.is_paused:
            return
        if text and text.strip():
            session.accumulator.transcripts.append(text.strip())

    def accumulate_vision(self, session_id: str, face_data: dict):
        session = self._sessions.get(session_id)
        if not session or session.is_complete or session.is_paused:
            return

        acc = session.accumulator
        acc.video_frames += 1

        if face_data.get("face_detected", False):
            acc.face_detected_frames += 1
            val = face_data.get("valence", 0.0)
            aro = face_data.get("arousal", 0.0)
            acc.valence_sum += val
            acc.arousal_sum += aro
            acc.smile_sum += face_data.get("smile_score", 0.0)
            acc.brow_furrow_sum += face_data.get("brow_furrow_score", 0.0)

            # Sample-level for derived metrics
            acc.valence_samples.append(val)
            acc.arousal_samples.append(aro)
            acc.eye_open_samples.append(face_data.get("eye_open_ratio", 0.0))

    def accumulate_nlp(self, session_id: str, nlp_data: dict):
        session = self._sessions.get(session_id)
        if not session or session.is_complete or session.is_paused:
            return

        acc = session.accumulator
        sentiment = nlp_data.get("sentiment", {})
        features = nlp_data.get("features", {})

        acc.sentiment_sum += sentiment.get("polarity", 0.0)
        acc.sentiment_count += 1
        acc.absolutist_count += features.get("absolutist_count", 0)
        acc.first_person_count += features.get("first_person_pronouns", 0)

    # ── Question Completion ──────────────────────────────────

    def complete_question(self, session_id: str, score: int) -> tuple:
        """Snapshot accumulated data, store as QuestionResponse, advance."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Assessment session not found: {session_id}")
        if session.is_complete:
            raise ValueError("Assessment already completed")

        q = session.current_question
        acc = session.accumulator
        raw_duration = time.time() - acc.started_at
        duration = raw_duration - acc.total_pause_time

        # Compute averages
        n_audio = max(acc.audio_segments, 1)
        n_face = max(acc.face_detected_frames, 1)
        n_sent = max(acc.sentiment_count, 1)

        avg_pitch = acc.pitch_sum / n_audio
        pitch_variance = acc.pitch_std_sum / n_audio
        avg_speech_rate = acc.speech_rate_sum / n_audio
        avg_silence_ratio = acc.silence_ratio_sum / n_audio
        hesitation_ratio = (
            acc.hesitation_count_total / acc.word_count_total
            if acc.word_count_total > 0 else 0.0
        )

        # Derived vision metrics
        blink_rate = _estimate_blink_rate(acc.eye_open_samples, duration)
        facial_stability = _compute_facial_stability(acc.valence_samples)
        emotional_intensity = _compute_emotional_intensity(
            acc.valence_samples, acc.arousal_samples
        )

        # Confidence proxy
        confidence_proxy = _compute_confidence_proxy(
            avg_speech_rate, hesitation_ratio, facial_stability,
            pitch_variance, avg_silence_ratio
        )

        response = QuestionResponse(
            question_id=q.id,
            domain=q.domain,
            question_text=q.text,
            self_report_score=score,
            duration_seconds=round(duration, 2),
            transcript=" ".join(acc.transcripts),
            audio_segments=acc.audio_segments,
            avg_pitch=round(avg_pitch, 2),
            pitch_variance=round(pitch_variance, 2),
            avg_energy_rms=round(acc.energy_rms_sum / n_audio, 4),
            avg_energy_db=round(acc.energy_db_sum / n_audio, 2),
            avg_speech_rate=round(avg_speech_rate, 1),
            avg_silence_ratio=round(avg_silence_ratio, 3),
            total_pauses=acc.pause_count_total,
            total_words=acc.word_count_total,
            hesitation_count=acc.hesitation_count_total,
            hesitation_ratio=round(hesitation_ratio, 3),
            video_frames=acc.video_frames,
            face_detected_frames=acc.face_detected_frames,
            avg_valence=round(acc.valence_sum / n_face, 3),
            avg_arousal=round(acc.arousal_sum / n_face, 3),
            avg_smile=round(acc.smile_sum / n_face, 3),
            avg_brow_furrow=round(acc.brow_furrow_sum / n_face, 3),
            blink_rate=blink_rate,
            facial_stability=facial_stability,
            emotional_intensity=emotional_intensity,
            avg_sentiment=round(acc.sentiment_sum / n_sent, 3),
            absolutist_words=acc.absolutist_count,
            first_person_pronouns=acc.first_person_count,
            confidence_proxy=confidence_proxy,
        )

        session.responses.append(response)
        session.current_index += 1
        session.reset_accumulator()

        if session.is_complete:
            logger.info(f"Assessment completed: {session_id}")
            return None, True

        return session.current_question, False

    # ── Clinician Override ────────────────────────────────────

    def override_answer(self, session_id: str, question_id: str, new_score: int):
        """Clinician overrides a previously submitted answer's self-report score."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Assessment session not found: {session_id}")

        for resp in session.responses:
            if resp.question_id == question_id:
                resp.self_report_score = max(0, min(4, new_score))
                logger.info(f"Override Q {question_id} → score {new_score}")
                return True
        raise ValueError(f"Question {question_id} not yet answered")

    def skip_question(self, session_id: str) -> tuple:
        """Skip current question (score = -1 indicates skipped)."""
        session = self._sessions.get(session_id)
        if not session or session.is_complete:
            raise ValueError("Cannot skip")
        return self.complete_question(session_id, score=-1)

    # ── Results ──────────────────────────────────────────────

    def get_responses(self, session_id: str) -> List[QuestionResponse]:
        """Get all per-question responses."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return session.responses

    def get_session_meta(self, session_id: str) -> dict:
        """Get session metadata."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        return {
            "session_id": session_id,
            "total_questions": question_bank.total_questions,
            "total_answered": len(session.responses),
            "completed": session.is_complete,
            "duration_seconds": round(time.time() - session.created_at, 2),
            "is_paused": session.is_paused,
        }

    def remove_session(self, session_id: str):
        self._sessions.pop(session_id, None)


# Singleton
question_engine = QuestionEngine()
