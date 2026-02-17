"""
Vision Processing Module — Main orchestrator.

Combines MediaPipe Face Mesh with OpenCV frame extraction to provide
per-second facial analysis of interview recordings.

Architecture:
    VisionProcessor (this file)
    └── FaceMeshDetector  — Landmark tracking, AU estimation, valence/arousal

Design Principles:
    - Frame extraction at configurable FPS (default: 1fps for efficiency)
    - Per-frame AU/valence/arousal → aggregated into per-second windows
    - Emotion stability scoring across the entire session
    - Neutral baseline comparison for subject-specific calibration
    - Async wrapper for non-blocking FastAPI usage
    - Never raises: all errors return safe empty structures

Output Schema:
    {
        "status": "success" | "partial" | "error",
        "errors": [str],
        "duration_sec": float,
        "frames_analyzed": int,
        "face_detection_rate": float,
        "per_second": [                # Time-series at 1-second granularity
            {
                "time_sec": float,
                "face_detected": bool,
                "action_units": {...},
                "valence": float,
                "arousal": float
            }
        ],
        "aggregate": {
            "valence_mean": float,
            "valence_std": float,
            "arousal_mean": float,
            "arousal_std": float,
            "dominant_aus": [str],      # Top 3 most active AUs
            "au_means": {...}
        },
        "stability": {
            "emotion_stability_score": float,  # 0-1 (1 = very stable)
            "valence_range": float,
            "arousal_range": float,
            "variability_index": float         # 0-1 (1 = high variability)
        },
        "baseline_comparison": {               # Only if baseline provided
            "valence_deviation": float,
            "arousal_deviation": float,
            "au_deviations": {...}
        }
    }
"""
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="vision")


class VisionProcessor:
    """
    Processes video files to extract facial emotion features
    relevant to psychiatric evaluation.

    Pipeline:
        Video File (.mp4/.webm)
        │
        ├─► OpenCV Frame Extraction (1 fps)
        │
        ├─► MediaPipe Face Mesh ──► Landmarks + AUs per frame
        │
        ├─► Aggregation ──────────► Per-second + session summary
        │
        ├─► Stability Scoring ────► Emotion consistency metrics
        │
        └─► Baseline Comparison ──► Deviation from neutral face
                │
                ▼
        Structured JSON Output

    Usage:
        processor = VisionProcessor()
        result = await processor.process("interview.mp4")
        # With neutral baseline:
        result = await processor.process("interview.mp4", baseline={...})
    """

    def __init__(self, analysis_fps: float = 1.0):
        """
        Args:
            analysis_fps: Frames per second to analyze (default 1.0).
                          Lower = faster processing, higher = more granular timeline.
        """
        self.analysis_fps = analysis_fps
        self._detector = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Lazy initialization of FaceMeshDetector.

        Returns:
            True if initialization succeeded.
        """
        if self._initialized:
            return True

        try:
            from app.modules.vision.face_mesh import FaceMeshDetector
            self._detector = FaceMeshDetector()
            success = self._detector.initialize()
            if not success:
                self._detector = None
                logger.warning("FaceMeshDetector failed to initialize")
        except ImportError:
            logger.warning("Vision dependencies not installed (mediapipe/opencv)")
            self._detector = None

        self._initialized = True
        return self._detector is not None

    # ── Async Interface ──────────────────────────────

    async def process(
        self,
        video_path: str,
        baseline: Optional[Dict] = None,
    ) -> Dict:
        """
        Process a video file asynchronously.

        Args:
            video_path: Path to video file (.mp4, .webm, .avi)
            baseline: Optional neutral baseline for comparison
                      {"valence": float, "arousal": float, "au_means": {...}}

        Returns:
            Structured vision analysis result.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self.process_sync,
            video_path,
            baseline,
        )

    # ── Synchronous Interface ────────────────────────

    def process_sync(
        self,
        video_path: str,
        baseline: Optional[Dict] = None,
    ) -> Dict:
        """
        Process a video file synchronously.

        Args:
            video_path: Path to video file
            baseline: Optional neutral baseline dict

        Returns:
            Structured vision analysis result.
        """
        if not video_path or not os.path.isfile(video_path):
            return self._error_result(f"Video file not found: {video_path}")

        if not self._initialized:
            self.initialize()

        if not self._detector:
            return self._error_result("Vision module not available (mediapipe/opencv missing)")

        errors = []

        # ── Step 1: Extract and analyze frames ───────
        try:
            frame_results = self._extract_and_analyze(video_path)
        except Exception as e:
            errors.append(f"Frame extraction error: {e}")
            logger.error(f"Frame extraction failed: {e}", exc_info=True)
            return self._error_result(str(e))

        if not frame_results:
            return self._error_result("No frames could be extracted from video")

        # ── Step 2: Build per-second timeline ────────
        per_second = self._build_per_second(frame_results)

        # ── Step 3: Aggregate features ───────────────
        aggregate = self._aggregate(per_second)

        # ── Step 4: Stability scoring ────────────────
        stability = self._compute_stability(per_second)

        # ── Step 5: Baseline comparison (optional) ───
        baseline_comparison = None
        if baseline:
            baseline_comparison = self._compare_baseline(aggregate, baseline)

        # Detection rate
        detected_frames = sum(1 for f in frame_results if f["face_detected"])
        total_frames = len(frame_results)
        duration = frame_results[-1]["time_sec"] if frame_results else 0.0

        result = {
            "status": "success" if not errors else "partial",
            "errors": errors,
            "duration_sec": round(duration, 3),
            "frames_analyzed": total_frames,
            "face_detection_rate": round(detected_frames / max(total_frames, 1), 3),
            "per_second": per_second,
            "aggregate": aggregate,
            "stability": stability,
        }

        if baseline_comparison:
            result["baseline_comparison"] = baseline_comparison

        logger.info(
            f"Vision analysis complete: {total_frames} frames, "
            f"{duration:.1f}s, detection_rate={result['face_detection_rate']:.0%}"
        )
        return result

    # ── Frame Extraction ─────────────────────────────

    def _extract_and_analyze(self, video_path: str) -> List[Dict]:
        """
        Extract frames at analysis_fps and run face detection on each.

        Returns:
            List of per-frame results with timestamps.
        """
        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(video_fps / self.analysis_fps))

        logger.info(
            f"Processing video: {total_frames} total frames at {video_fps:.1f}fps, "
            f"analyzing every {frame_interval} frames ({self.analysis_fps}fps)"
        )

        results = []
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    time_sec = frame_idx / video_fps
                    detection = self._detector.detect(frame)
                    detection["time_sec"] = round(time_sec, 3)
                    results.append(detection)

                frame_idx += 1
        finally:
            cap.release()

        logger.info(f"Extracted {len(results)} analysis frames from {frame_idx} total")
        return results

    # ── Per-Second Aggregation ───────────────────────

    @staticmethod
    def _build_per_second(frame_results: List[Dict]) -> List[Dict]:
        """
        Group frame results into 1-second windows and average.
        """
        if not frame_results:
            return []

        max_time = int(frame_results[-1]["time_sec"]) + 1
        per_second = []

        for sec in range(max_time):
            # Frames in this second window
            window = [
                f for f in frame_results
                if sec <= f["time_sec"] < sec + 1
            ]

            if not window:
                per_second.append({
                    "time_sec": float(sec),
                    "face_detected": False,
                    "action_units": {
                        "AU4": 0.0, "AU6": 0.0, "AU12": 0.0,
                        "AU15": 0.0, "AU20": 0.0, "AU25": 0.0, "AU45": 0.0,
                    },
                    "valence": 0.0,
                    "arousal": 0.0,
                })
                continue

            detected = [f for f in window if f["face_detected"]]

            if not detected:
                per_second.append({
                    "time_sec": float(sec),
                    "face_detected": False,
                    "action_units": {
                        "AU4": 0.0, "AU6": 0.0, "AU12": 0.0,
                        "AU15": 0.0, "AU20": 0.0, "AU25": 0.0, "AU45": 0.0,
                    },
                    "valence": 0.0,
                    "arousal": 0.0,
                })
                continue

            # Average AUs across frames in this second
            au_keys = detected[0]["action_units"].keys()
            avg_aus = {}
            for key in au_keys:
                vals = [f["action_units"].get(key, 0.0) for f in detected]
                avg_aus[key] = round(float(np.mean(vals)), 3)

            avg_valence = float(np.mean([f["valence"] for f in detected]))
            avg_arousal = float(np.mean([f["arousal"] for f in detected]))

            per_second.append({
                "time_sec": float(sec),
                "face_detected": True,
                "action_units": avg_aus,
                "valence": round(avg_valence, 3),
                "arousal": round(avg_arousal, 3),
            })

        return per_second

    # ── Session Aggregation ──────────────────────────

    @staticmethod
    def _aggregate(per_second: List[Dict]) -> Dict:
        """
        Compute session-level aggregate features.
        """
        detected = [s for s in per_second if s["face_detected"]]

        if not detected:
            return {
                "valence_mean": 0.0, "valence_std": 0.0,
                "arousal_mean": 0.0, "arousal_std": 0.0,
                "dominant_aus": [],
                "au_means": {},
            }

        valences = [s["valence"] for s in detected]
        arousals = [s["arousal"] for s in detected]

        # Mean AU values across session
        au_keys = detected[0]["action_units"].keys()
        au_means = {}
        for key in au_keys:
            vals = [s["action_units"].get(key, 0.0) for s in detected]
            au_means[key] = round(float(np.mean(vals)), 3)

        # Top 3 most active AUs (excluding blink AU45)
        filtered_aus = {k: v for k, v in au_means.items() if k != "AU45"}
        dominant = sorted(filtered_aus, key=filtered_aus.get, reverse=True)[:3]

        return {
            "valence_mean": round(float(np.mean(valences)), 3),
            "valence_std": round(float(np.std(valences)), 3),
            "arousal_mean": round(float(np.mean(arousals)), 3),
            "arousal_std": round(float(np.std(arousals)), 3),
            "dominant_aus": dominant,
            "au_means": au_means,
        }

    # ── Stability Scoring ────────────────────────────

    @staticmethod
    def _compute_stability(per_second: List[Dict]) -> Dict:
        """
        Compute emotion stability metrics.

        Stability Score: 1.0 = face shows same emotion throughout (flat affect).
                         0.0 = wildly variable expression (could be normal or dysregulated).

        Variability Index: inverse of stability. High = lots of expression changes.

        Clinical:
            - Very high stability (> 0.9) + low arousal → flat affect / depression
            - Very low stability (< 0.3) → emotional dysregulation
        """
        detected = [s for s in per_second if s["face_detected"]]

        if len(detected) < 2:
            return {
                "emotion_stability_score": 0.0,
                "valence_range": 0.0,
                "arousal_range": 0.0,
                "variability_index": 0.0,
            }

        valences = [s["valence"] for s in detected]
        arousals = [s["arousal"] for s in detected]

        valence_std = float(np.std(valences))
        arousal_std = float(np.std(arousals))

        valence_range = float(np.max(valences) - np.min(valences))
        arousal_range = float(np.max(arousals) - np.min(arousals))

        # Stability: 1 - normalized_std (max expected std ~0.5)
        combined_std = (valence_std + arousal_std) / 2
        stability = float(np.clip(1.0 - combined_std / 0.5, 0.0, 1.0))

        # Variability: normalized range (max expected range ~2.0 for valence)
        combined_range = (valence_range + arousal_range) / 2
        variability = float(np.clip(combined_range / 1.5, 0.0, 1.0))

        return {
            "emotion_stability_score": round(stability, 3),
            "valence_range": round(valence_range, 3),
            "arousal_range": round(arousal_range, 3),
            "variability_index": round(variability, 3),
        }

    # ── Baseline Comparison ──────────────────────────

    @staticmethod
    def _compare_baseline(aggregate: Dict, baseline: Dict) -> Dict:
        """
        Compare session aggregate against a neutral baseline.

        Baseline should contain:
            {"valence": float, "arousal": float, "au_means": {...}}

        Returns deviation from baseline for each metric.
        Positive deviation = more active than baseline.
        """
        valence_dev = aggregate.get("valence_mean", 0) - baseline.get("valence", 0)
        arousal_dev = aggregate.get("arousal_mean", 0) - baseline.get("arousal", 0)

        au_devs = {}
        baseline_aus = baseline.get("au_means", {})
        session_aus = aggregate.get("au_means", {})

        for key in session_aus:
            session_val = session_aus.get(key, 0)
            baseline_val = baseline_aus.get(key, 0)
            au_devs[key] = round(session_val - baseline_val, 3)

        return {
            "valence_deviation": round(valence_dev, 3),
            "arousal_deviation": round(arousal_dev, 3),
            "au_deviations": au_devs,
        }

    # ── Error Handling ───────────────────────────────

    @staticmethod
    def _error_result(error_msg: str) -> Dict:
        """Return error result structure."""
        return {
            "status": "error",
            "errors": [error_msg],
            "duration_sec": 0.0,
            "frames_analyzed": 0,
            "face_detection_rate": 0.0,
            "per_second": [],
            "aggregate": {
                "valence_mean": 0.0, "valence_std": 0.0,
                "arousal_mean": 0.0, "arousal_std": 0.0,
                "dominant_aus": [],
                "au_means": {},
            },
            "stability": {
                "emotion_stability_score": 0.0,
                "valence_range": 0.0,
                "arousal_range": 0.0,
                "variability_index": 0.0,
            },
        }

    def close(self):
        """Release resources."""
        if self._detector:
            self._detector.close()
