import os
import time
import librosa
import numpy as np
from typing import Dict, Any
from app.schemas.audio import AudioAnalysisResult, AcousticFeatures, AudioSegment, WordLevelData

# Filler / hesitation words to detect
HESITATION_WORDS = {
    "um", "uh", "uhm", "hmm", "hm", "er", "ah", "like",
    "you know", "i mean", "sort of", "kind of", "basically",
}

class AudioProcessor:
    def __init__(self, model_size="base"):
        self.model_size = model_size
        self._model = None
        self.available = True

    def _ensure_model_loaded(self):
        if self._model is not None:
            return True
        try:
            import whisper
            self._model = whisper.load_model(self.model_size)
            self.available = True
            return True
        except Exception as e:
            print(f"Audio module initialization failed: {e}")
            self.available = False
            return False

    def process_file(self, file_path: str, session_id: str) -> AudioAnalysisResult:
        if not self._ensure_model_loaded():
            return AudioAnalysisResult(
                session_id=session_id,
                segments=[],
                features=AcousticFeatures(
                    pitch_mean=0.0, pitch_std=0.0, silence_ratio=0.0,
                    speech_rate_wpm=0.0, pause_count=0,
                ),
                processing_time=0.0
            )

        t0 = time.time()

        # 1. Transcription
        transcription = self._model.transcribe(file_path, word_timestamps=True)
        segments = self._parse_segments(transcription["segments"])
        
        # 2. Acoustic Analysis
        y, sr = librosa.load(file_path)
        features = self._extract_acoustic_features(y, sr, segments)

        elapsed = time.time() - t0

        return AudioAnalysisResult(
            session_id=session_id,
            segments=segments,
            features=features,
            processing_time=round(elapsed, 2),
        )

    def _parse_segments(self, raw_segments: list) -> list[AudioSegment]:
        parsed = []
        for i, seg in enumerate(raw_segments):
            words = [
                WordLevelData(
                    word=w["word"], 
                    start=w["start"], 
                    end=w["end"], 
                    confidence=w["probability"]
                ) for w in seg.get("words", [])
            ]
            
            parsed.append(AudioSegment(
                id=i,
                start_time=seg["start"],
                end_time=seg["end"],
                transcript=seg["text"],
                words=words
            ))
        return parsed

    def _extract_acoustic_features(
        self, y: np.ndarray, sr: int, segments: list[AudioSegment]
    ) -> AcousticFeatures:
        # ── Pitch (F0) ──
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7')
        )
        valid_f0 = f0[~np.isnan(f0)]
        
        pitch_mean = float(np.mean(valid_f0)) if len(valid_f0) > 0 else 0.0
        pitch_std = float(np.std(valid_f0)) if len(valid_f0) > 0 else 0.0

        # ── Silence & Pauses ──
        non_silent_intervals = librosa.effects.split(y, top_db=20)
        total_duration = librosa.get_duration(y=y, sr=sr)
        non_silent_duration = sum([(end - start) / sr for start, end in non_silent_intervals])
        silence_ratio = 1.0 - (non_silent_duration / total_duration) if total_duration > 0 else 0.0

        # ── Word count ──
        all_words = [w for s in segments for w in s.words]
        total_words = len(all_words)

        # ── Speech rate (WPM) ──
        speech_rate = (total_words / (total_duration / 60)) if total_duration > 0 else 0

        # ── Pause count ──
        pause_count = max(0, len(segments) - 1)

        # ── Pause rate (pauses per minute) ──
        duration_min = total_duration / 60.0 if total_duration > 0 else 1.0
        pause_rate = float(pause_count / duration_min) if duration_min > 0 else 0.0

        # ── Hesitation markers ──
        hesitation_count = 0
        for w in all_words:
            cleaned = w.word.strip().lower().strip(".,!?")
            if cleaned in HESITATION_WORDS:
                hesitation_count += 1
        # Also check bigrams in transcript
        for seg in segments:
            text_lower = seg.transcript.lower()
            for filler in ("you know", "i mean", "sort of", "kind of"):
                hesitation_count += text_lower.count(filler)

        # ── Confidence level (average Whisper word confidence) ──
        if all_words:
            confidence_level = float(np.mean([w.confidence for w in all_words]))
        else:
            confidence_level = 0.0

        # ── Tension index (normalized composite of pitch + variability) ──
        # Higher pitch + higher variability = higher tension
        tension_index = (pitch_mean / 100.0) + (pitch_std / 50.0)
        tension_index = min(max(tension_index, 0.0), 10.0)  # clamp

        # ── Response delay (time to first speech onset) ──
        if segments and len(segments) > 0:
            response_delay = float(segments[0].start_time)
        else:
            response_delay = float(total_duration)

        return AcousticFeatures(
            pitch_mean=round(pitch_mean, 2),
            pitch_std=round(pitch_std, 2),
            silence_ratio=round(silence_ratio, 4),
            speech_rate_wpm=round(speech_rate, 1),
            pause_count=pause_count,
            word_count=total_words,
            hesitation_markers=hesitation_count,
            confidence_level=round(confidence_level, 4),
            tension_index=round(tension_index, 3),
            response_delay=round(response_delay, 2),
            pause_rate=round(pause_rate, 2),
        )
