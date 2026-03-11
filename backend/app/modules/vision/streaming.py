"""
StreamingVisionProcessor — processes single JPEG frames from webcam.
Uses MediaPipe FaceMesh for landmark extraction (same heuristics as VisionProcessor).
Lightweight enough to run on the async event loop.
"""

import cv2
import numpy as np
import logging
import time

from app.schemas.streaming import StreamFaceData

logger = logging.getLogger(__name__)


class StreamingVisionProcessor:
    """Processes individual JPEG frames for facial landmark analysis."""

    def __init__(self):
        self._mp_face_mesh = None
        self._face_mesh = None
        self.available = False

    def preload(self):
        """Pre-load MediaPipe FaceMesh at startup."""
        try:
            import mediapipe as mp
            self._mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                static_image_mode=True,  # each frame is independent
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.available = True
            logger.info("MediaPipe FaceMesh loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load MediaPipe: {e}")
            self.available = False

    def process_frame(self, jpeg_bytes: bytes, frame_index: int) -> StreamFaceData:
        """
        Process a single JPEG frame.

        Args:
            jpeg_bytes: raw JPEG image bytes
            frame_index: incrementing frame counter

        Returns:
            StreamFaceData with facial metrics
        """
        timestamp = time.time()

        if not self.available or self._face_mesh is None:
            return StreamFaceData(
                timestamp=timestamp,
                face_detected=False,
                valence=0.0,
                arousal=0.0,
                smile_score=0.0,
                brow_furrow_score=0.0,
                eye_contact_score=0.0,
                frame_index=frame_index,
            )

        try:
            # Decode JPEG → numpy BGR
            nparr = np.frombuffer(jpeg_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode JPEG frame")

            # BGR → RGB for MediaPipe
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            results = self._face_mesh.process(image_rgb)

            return self._analyze_landmarks(results, timestamp, frame_index)

        except Exception as e:
            logger.error(f"Frame processing failed: {e}")
            return StreamFaceData(
                timestamp=timestamp,
                face_detected=False,
                valence=0.0,
                arousal=0.0,
                smile_score=0.0,
                brow_furrow_score=0.0,
                eye_contact_score=0.0,
                frame_index=frame_index,
            )

    def _analyze_landmarks(self, results, timestamp: float, frame_index: int) -> StreamFaceData:
        """Extract heuristic facial features from MediaPipe landmarks."""
        if not results.multi_face_landmarks:
            return StreamFaceData(
                timestamp=timestamp,
                face_detected=False,
                valence=0.0,
                arousal=0.0,
                smile_score=0.0,
                brow_furrow_score=0.0,
                eye_contact_score=0.0,
                eye_open_ratio=0.0,
                frame_index=frame_index,
            )

        landmarks = results.multi_face_landmarks[0].landmark

        # Smile Score (mouth width / face width)
        mouth_width = self._dist(landmarks[61], landmarks[291])
        face_width = self._dist(landmarks[234], landmarks[454])
        smile_ratio = mouth_width / face_width if face_width > 0 else 0
        smile_score = min(max((smile_ratio - 0.35) * 10, 0.0), 1.0)

        # Brow Furrow (narrower = furrowed)
        brow_dist = self._dist(landmarks[107], landmarks[336])
        brow_ratio = brow_dist / face_width if face_width > 0 else 0
        brow_furrow_score = min(max((0.35 - brow_ratio) * 10, 0.0), 1.0)

        # Eye Openness (arousal proxy + blink detection)
        left_eye_h = self._dist(landmarks[159], landmarks[145])
        right_eye_h = self._dist(landmarks[386], landmarks[374])
        eye_openness = (left_eye_h + right_eye_h) / (2 * face_width) if face_width > 0 else 0
        eye_open_ratio = round(eye_openness, 4)

        # Derived metrics
        valence = smile_score - brow_furrow_score
        arousal = min(max(eye_openness * 10, 0.0), 1.0)

        return StreamFaceData(
            timestamp=timestamp,
            face_detected=True,
            valence=round(valence, 3),
            arousal=round(arousal, 3),
            smile_score=round(smile_score, 3),
            brow_furrow_score=round(brow_furrow_score, 3),
            eye_contact_score=0.5,  # placeholder for gaze vector
            eye_open_ratio=eye_open_ratio,
            frame_index=frame_index,
        )

    @staticmethod
    def _dist(p1, p2) -> float:
        return float(np.sqrt(
            (p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2
        ))
