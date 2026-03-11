"""
Face Mesh Detector — MediaPipe-based facial landmark analysis.

Responsibilities:
    - 468 facial landmark detection via MediaPipe Face Mesh
    - Action Unit (AU) estimation from landmark geometry distances
    - Valence/Arousal mapping from AU combinations
    - Per-frame facial feature extraction

Clinical Relevance:
    - Low valence + low arousal → depressive flat affect
    - Inconsistent AU patterns → incongruent affect
    - Minimal facial movement → psychomotor retardation
    - AU4 (brow lowerer) + AU15 (lip corner depressor) → sadness markers

Landmark Reference (MediaPipe 468-point model):
    - Eyes: 33,133 (left/right outer), 159,386 (upper lid), 145,374 (lower lid)
    - Brows: 70,63 (left inner/outer), 300,293 (right inner/outer)
    - Mouth: 13,14 (upper/lower lip center), 61,291 (mouth corners)
    - Nose: 1 (tip), 4 (bridge)
    - Jaw: 152 (chin), 10 (forehead)

Output Schema (per-frame):
    {
        "face_detected": bool,
        "landmarks_count": int,
        "action_units": {
            "AU4":  float,    # Brow Lowerer (0-1)
            "AU6":  float,    # Cheek Raiser (0-1)
            "AU12": float,    # Lip Corner Puller / Smile (0-1)
            "AU15": float,    # Lip Corner Depressor (0-1)
            "AU20": float,    # Lip Stretcher (0-1)
            "AU25": float,    # Lips Part (0-1)
            "AU45": float     # Blink (0-1)
        },
        "valence": float,     # -1.0 (negative) to 1.0 (positive)
        "arousal": float      #  0.0 (calm) to 1.0 (excited)
    }
"""
import logging
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class FaceMeshDetector:
    """
    Detects facial landmarks and estimates Action Units using
    MediaPipe Face Mesh (468 landmarks).

    Action Units are estimated geometrically by computing distances
    between specific landmark pairs and normalizing against facial
    reference distances (inter-pupillary or nose-chin).

    Thread Safety:
        NOT thread-safe. Each thread should use its own instance.
    """

    # ── Landmark Indices ─────────────────────────────
    # MediaPipe Face Mesh 468-point landmark indices

    # Eyes
    LEFT_EYE_UPPER = 159
    LEFT_EYE_LOWER = 145
    RIGHT_EYE_UPPER = 386
    RIGHT_EYE_LOWER = 374
    LEFT_EYE_OUTER = 33
    RIGHT_EYE_OUTER = 263

    # Brows
    LEFT_BROW_INNER = 70
    LEFT_BROW_OUTER = 63
    RIGHT_BROW_INNER = 300
    RIGHT_BROW_OUTER = 293
    LEFT_BROW_TOP = 105
    RIGHT_BROW_TOP = 334

    # Mouth
    UPPER_LIP_CENTER = 13
    LOWER_LIP_CENTER = 14
    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291
    UPPER_LIP_TOP = 0
    LOWER_LIP_BOTTOM = 17

    # Nose
    NOSE_TIP = 1
    NOSE_BRIDGE = 6

    # Reference
    CHIN = 152
    FOREHEAD = 10
    LEFT_CHEEK = 234
    RIGHT_CHEEK = 454

    def __init__(self):
        self._face_mesh = None
        self._available = False

    def initialize(self) -> bool:
        """
        Initialize MediaPipe Face Mesh solution.

        Returns:
            True if initialization succeeded.
        """
        try:
            import mediapipe as mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._available = True
            logger.info("MediaPipe Face Mesh initialized")
            return True
        except ImportError:
            logger.warning("mediapipe not installed — face detection disabled")
            return False
        except Exception as e:
            logger.error(f"Face Mesh initialization failed: {e}")
            return False

    @property
    def is_available(self) -> bool:
        return self._available and self._face_mesh is not None

    def detect(self, frame: np.ndarray) -> Dict:
        """
        Detect face landmarks in a single BGR frame and estimate AUs.

        Args:
            frame: OpenCV BGR image (H x W x 3 numpy array)

        Returns:
            Structured dict with AUs, valence, arousal.
            Returns no-face result if detection fails.
        """
        if not self.is_available:
            return self._no_face_result()

        try:
            import cv2

            # MediaPipe expects RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                return self._no_face_result()

            # Use first detected face
            face = results.multi_face_landmarks[0]
            h, w, _ = frame.shape

            # Convert to numpy array of (x, y, z) in pixel coords
            landmarks = np.array([
                (lm.x * w, lm.y * h, lm.z * w)
                for lm in face.landmark
            ])

            # Calculate reference distance (nose bridge to chin) for normalization
            ref_dist = self._distance(landmarks, self.NOSE_BRIDGE, self.CHIN)
            if ref_dist < 1.0:
                return self._no_face_result()

            # Estimate Action Units from geometry
            action_units = self._estimate_action_units(landmarks, ref_dist)

            # Map AUs to Valence and Arousal
            valence, arousal = self._map_valence_arousal(action_units)

            return {
                "face_detected": True,
                "landmarks_count": len(landmarks),
                "action_units": action_units,
                "valence": round(valence, 3),
                "arousal": round(arousal, 3),
            }

        except Exception as e:
            logger.error(f"Face detection failed: {e}", exc_info=True)
            return self._no_face_result()

    # ── Action Unit Estimation ───────────────────────

    def _estimate_action_units(self, lm: np.ndarray, ref: float) -> Dict:
        """
        Estimate FACS Action Units from landmark geometry.

        Each AU is computed as a normalized distance ratio (0.0 - 1.0).
        These are approximations — not ground truth FACS coding.

        Args:
            lm: Landmark array (468 x 3)
            ref: Reference distance for normalization (nose-to-chin)
        """

        # ── AU4: Brow Lowerer ────────────────────
        # Distance from brow top to eye upper lid (smaller = more brow lowered)
        left_brow_eye = self._distance(lm, self.LEFT_BROW_TOP, self.LEFT_EYE_UPPER)
        right_brow_eye = self._distance(lm, self.RIGHT_BROW_TOP, self.RIGHT_EYE_UPPER)
        avg_brow_eye = (left_brow_eye + right_brow_eye) / 2
        # Typical range: 0.08-0.18 of ref. Lower = more AU4.
        au4 = np.clip(1.0 - (avg_brow_eye / ref - 0.06) / 0.14, 0.0, 1.0)

        # ── AU6: Cheek Raiser ────────────────────
        # Eye opening narrows when cheeks raise (Duchenne smile marker)
        left_eye_open = self._distance(lm, self.LEFT_EYE_UPPER, self.LEFT_EYE_LOWER)
        right_eye_open = self._distance(lm, self.RIGHT_EYE_UPPER, self.RIGHT_EYE_LOWER)
        avg_eye_open = (left_eye_open + right_eye_open) / 2
        # Typical range: 0.02-0.06 of ref. Smaller = more AU6.
        au6 = np.clip(1.0 - (avg_eye_open / ref - 0.01) / 0.06, 0.0, 1.0)

        # ── AU12: Lip Corner Puller (Smile) ──────
        # Mouth width relative to reference
        mouth_width = self._distance(lm, self.MOUTH_LEFT, self.MOUTH_RIGHT)
        # Typical range: 0.25-0.45 of ref. Wider = more smile.
        au12 = np.clip((mouth_width / ref - 0.25) / 0.20, 0.0, 1.0)

        # ── AU15: Lip Corner Depressor ───────────
        # Mouth corners below mouth center (corners droop down)
        mouth_center_y = (lm[self.MOUTH_LEFT][1] + lm[self.MOUTH_RIGHT][1]) / 2
        lip_center_y = lm[self.UPPER_LIP_CENTER][1]
        corner_droop = (mouth_center_y - lip_center_y) / ref
        # Positive = corners below center = frown
        au15 = np.clip(corner_droop / 0.04, 0.0, 1.0)

        # ── AU20: Lip Stretcher ──────────────────
        # Horizontal stretch of lips relative to face width
        face_width = self._distance(lm, self.LEFT_CHEEK, self.RIGHT_CHEEK)
        lip_stretch_ratio = mouth_width / max(face_width, 1.0)
        # Typical range: 0.35-0.55. Higher = more stretch.
        au20 = np.clip((lip_stretch_ratio - 0.35) / 0.20, 0.0, 1.0)

        # ── AU25: Lips Part ──────────────────────
        # Vertical distance between upper and lower lip
        lip_part = self._distance(lm, self.UPPER_LIP_CENTER, self.LOWER_LIP_CENTER)
        # Typical range: 0.01-0.08 of ref.
        au25 = np.clip((lip_part / ref - 0.01) / 0.07, 0.0, 1.0)

        # ── AU45: Blink ──────────────────────────
        # Eye aspect ratio (very small = blink)
        ear = avg_eye_open / ref
        # Typical open: 0.04-0.06. Blink < 0.02.
        au45 = np.clip(1.0 - ear / 0.04, 0.0, 1.0)

        return {
            "AU4": round(float(au4), 3),
            "AU6": round(float(au6), 3),
            "AU12": round(float(au12), 3),
            "AU15": round(float(au15), 3),
            "AU20": round(float(au20), 3),
            "AU25": round(float(au25), 3),
            "AU45": round(float(au45), 3),
        }

    # ── Valence / Arousal Mapping ────────────────────

    @staticmethod
    def _map_valence_arousal(aus: Dict) -> Tuple[float, float]:
        """
        Map Action Units to dimensional emotion (Valence, Arousal).

        Valence: positive (joy) ←→ negative (sadness/anger)
        Arousal: calm ←→ excited/agitated

        Based on simplified Russell's Circumplex Model mapping.
        """
        # Valence: smile (AU12 + AU6) pushes positive,
        #          frown (AU4 + AU15) pushes negative
        positive_signal = (aus.get("AU12", 0) * 0.6 + aus.get("AU6", 0) * 0.4)
        negative_signal = (aus.get("AU4", 0) * 0.5 + aus.get("AU15", 0) * 0.5)
        valence = positive_signal - negative_signal  # Range: -1 to +1

        # Arousal: facial activity level (any AU activation = arousal)
        au_values = [v for k, v in aus.items() if k != "AU45"]  # Exclude blink
        arousal = float(np.mean(au_values)) if au_values else 0.0

        return (
            float(np.clip(valence, -1.0, 1.0)),
            float(np.clip(arousal, 0.0, 1.0)),
        )

    # ── Helpers ──────────────────────────────────────

    @staticmethod
    def _distance(lm: np.ndarray, i: int, j: int) -> float:
        """Euclidean distance between two landmarks (x, y only)."""
        return float(np.linalg.norm(lm[i][:2] - lm[j][:2]))

    @staticmethod
    def _no_face_result() -> Dict:
        """Return result when no face is detected."""
        return {
            "face_detected": False,
            "landmarks_count": 0,
            "action_units": {
                "AU4": 0.0, "AU6": 0.0, "AU12": 0.0,
                "AU15": 0.0, "AU20": 0.0, "AU25": 0.0,
                "AU45": 0.0,
            },
            "valence": 0.0,
            "arousal": 0.0,
        }

    def close(self):
        """Release MediaPipe resources."""
        if self._face_mesh:
            self._face_mesh.close()
            self._face_mesh = None
            self._available = False
