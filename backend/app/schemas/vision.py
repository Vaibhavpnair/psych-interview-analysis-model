from pydantic import BaseModel
from typing import List, Optional

class FaceFrameData(BaseModel):
    timestamp: float
    face_detected: bool
    valence: float # -1.0 (Sad/Angry) to 1.0 (Happy)
    arousal: float # 0.0 (Calm) to 1.0 (Excited/Stressed) - Proxy via eye widening/movement
    smile_score: float
    brow_furrow_score: float
    eye_contact_score: float # Proxy using gaze direction
    blink_detected: bool = False

class VisionAnalysisResult(BaseModel):
    session_id: str
    frames: List[FaceFrameData]
    average_valence: float
    average_arousal: float
    processing_time: float
    # ── Advanced metrics ──
    facial_variability: float = 0.0      # std-dev of valence across frames
    expression_stability: float = 0.0    # 1 − (std-dev of smile + brow)
    emotional_intensity: float = 0.0     # mean(|valence| + arousal)
    blink_rate: float = 0.0              # estimated blinks per minute
    neutral_deviation: float = 0.0       # avg distance of expression from neutral
