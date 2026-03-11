from pydantic import BaseModel
from typing import List, Optional

class WordLevelData(BaseModel):
    word: str
    start: float
    end: float
    confidence: float

class AudioSegment(BaseModel):
    id: int
    start_time: float
    end_time: float
    transcript: str
    words: List[WordLevelData]

class AcousticFeatures(BaseModel):
    pitch_mean: float
    pitch_std: float
    silence_ratio: float
    speech_rate_wpm: float
    pause_count: int
    # ── Extended metrics ──
    word_count: int = 0
    hesitation_markers: int = 0       # count of filler words (um, uh, hmm…)
    confidence_level: float = 0.0     # average word-level confidence from Whisper
    tension_index: float = 0.0        # composite of pitch + variability
    response_delay: float = 0.0       # seconds until first speech onset
    pause_rate: float = 0.0           # pauses per minute of speech

class AudioAnalysisResult(BaseModel):
    session_id: str
    segments: List[AudioSegment]
    features: AcousticFeatures
    processing_time: float
