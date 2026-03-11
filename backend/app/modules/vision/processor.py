import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)
from app.schemas.vision import VisionAnalysisResult, FaceFrameData
import time

class VisionProcessor:
    def __init__(self):
        self._mp_face_mesh = None
        self._face_mesh = None
        self.available = True
        # Blink detection state
        self._prev_ear = None
        self._blink_counter = 0
        self._ear_below_threshold = False
        self.EAR_THRESHOLD = 0.018  # Normalized EAR threshold

    def _ensure_face_mesh_loaded(self):
        if self._face_mesh is not None:
            return True
        try:
            import mediapipe as mp
            self._mp_face_mesh = mp.solutions.face_mesh
            self._face_mesh = self._mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.available = True
            return True
        except Exception as e:
            logger.error(f"Vision module initialization failed: {e}")
            self.available = False
            return False

    def process_video(self, video_path: str, session_id: str) -> VisionAnalysisResult:
        if not self._ensure_face_mesh_loaded():
            return VisionAnalysisResult(
                session_id=session_id,
                frames=[],
                average_valence=0.0,
                average_arousal=0.0,
                processing_time=0.0
            )

        # Reset blink state for each video
        self._prev_ear = None
        self._blink_counter = 0
        self._ear_below_threshold = False

        start_time = time.time()
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0  # Fallback for webcam recordings that may report 0
        logger.info(f"Processing video: {video_path}, FPS: {fps}")
        
        frames_data = []
        frame_idx = 0
        
        # Aggregate stats
        total_valence = 0.0
        total_arousal = 0.0
        valid_frames = 0

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break
            
            # Process every Nth frame to save compute (analysis @ 5fps is usually enough)
            stride = max(1, int(fps / 5))
            if frame_idx % stride != 0:
                frame_idx += 1
                continue

            current_time = frame_idx / fps
            
            # Convert BGR to RGB
            image.flags.writeable = False
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self._face_mesh.process(image_rgb)
            
            frame_data = self._analyze_landmarks(results, current_time)
            frames_data.append(frame_data)
            
            if frame_data.face_detected:
                total_valence += frame_data.valence
                total_arousal += frame_data.arousal
                valid_frames += 1
            
            frame_idx += 1

        cap.release()
        
        avg_val = total_valence / valid_frames if valid_frames > 0 else 0.0
        avg_ar = total_arousal / valid_frames if valid_frames > 0 else 0.0
        elapsed = time.time() - start_time

        # Compute advanced metrics
        advanced = self._compute_advanced_metrics(frames_data, elapsed)

        return VisionAnalysisResult(
            session_id=session_id,
            frames=frames_data,
            average_valence=avg_val,
            average_arousal=avg_ar,
            processing_time=elapsed,
            **advanced
        )

    # ── Advanced metric computation ──────────────────────────
    def _compute_advanced_metrics(self, frames: list[FaceFrameData], duration: float) -> dict:
        """Derive the five advanced metrics from collected frame data."""
        valid = [f for f in frames if f.face_detected]
        if not valid:
            return dict(
                facial_variability=0.0,
                expression_stability=0.0,
                emotional_intensity=0.0,
                blink_rate=0.0,
                neutral_deviation=0.0,
            )

        valences = np.array([f.valence for f in valid])
        arousals = np.array([f.arousal for f in valid])
        smiles = np.array([f.smile_score for f in valid])
        brows = np.array([f.brow_furrow_score for f in valid])

        # 1. Facial variability — how much valence fluctuates
        facial_variability = float(np.std(valences))

        # 2. Expression stability — 1 minus combined jitter of smile + brow
        expr_jitter = (np.std(smiles) + np.std(brows)) / 2.0
        expression_stability = float(max(0.0, min(1.0, 1.0 - expr_jitter)))

        # 3. Emotional intensity — average magnitude of affect
        emotional_intensity = float(np.mean(np.abs(valences) + arousals))

        # 4. Blink rate — blinks per minute
        total_blinks = sum(1 for f in valid if f.blink_detected)
        duration_minutes = duration / 60.0 if duration > 0 else 1.0
        blink_rate = float(total_blinks / duration_minutes) if duration_minutes > 0 else 0.0

        # 5. Neutral deviation — average distance from neutral (valence=0, arousal=0.3)
        neutral_deviation = float(np.mean(
            np.sqrt(valences ** 2 + (arousals - 0.3) ** 2)
        ))

        return dict(
            facial_variability=round(facial_variability, 4),
            expression_stability=round(expression_stability, 4),
            emotional_intensity=round(emotional_intensity, 4),
            blink_rate=round(blink_rate, 2),
            neutral_deviation=round(neutral_deviation, 4),
        )

    def _analyze_landmarks(self, results, timestamp: float) -> FaceFrameData:
        if not results.multi_face_landmarks:
            return FaceFrameData(
                timestamp=timestamp, face_detected=False,
                valence=0, arousal=0, smile_score=0,
                brow_furrow_score=0, eye_contact_score=0,
                blink_detected=False
            )

        landmarks = results.multi_face_landmarks[0].landmark
        
        # --- Heuristic Feature Extraction ---
        
        # 1. Smile Score (Mouth width / Face width)
        mouth_width = self._dist(landmarks[61], landmarks[291])
        face_width = self._dist(landmarks[234], landmarks[454])
        smile_ratio = mouth_width / face_width if face_width > 0 else 0
        smile_score = min(max((smile_ratio - 0.35) * 10, 0.0), 1.0)

        # 2. Brow Furrow
        brow_dist = self._dist(landmarks[107], landmarks[336])
        brow_ratio = brow_dist / face_width if face_width > 0 else 0
        brow_furrow_score = min(max((0.35 - brow_ratio) * 10, 0.0), 1.0)
        
        # 3. Eye Openness (Arousal/Alertness)
        left_eye_h = self._dist(landmarks[159], landmarks[145])
        right_eye_h = self._dist(landmarks[386], landmarks[374])
        eye_openness = (left_eye_h + right_eye_h) / (2 * face_width)
        
        # 4. Blink detection via Eye Aspect Ratio (EAR)
        ear = eye_openness  # already normalized by face width
        blink_detected = False
        if self._prev_ear is not None:
            if ear < self.EAR_THRESHOLD and not self._ear_below_threshold:
                # Eye just closed — mark as entering blink
                self._ear_below_threshold = True
            elif ear >= self.EAR_THRESHOLD and self._ear_below_threshold:
                # Eye just reopened — count as one blink
                self._ear_below_threshold = False
                blink_detected = True
                self._blink_counter += 1
        self._prev_ear = ear

        # 5. Proxies for Valence/Arousal
        valence = smile_score - brow_furrow_score
        arousal = min(max(eye_openness * 10, 0.0), 1.0) 

        return FaceFrameData(
            timestamp=timestamp,
            face_detected=True,
            valence=valence,
            arousal=arousal,
            smile_score=smile_score,
            brow_furrow_score=brow_furrow_score,
            eye_contact_score=0.5,  # Placeholder for complex gaze vector math
            blink_detected=blink_detected
        )

    def _dist(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)
