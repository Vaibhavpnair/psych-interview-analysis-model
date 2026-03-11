"""
Centralized configuration for the real-time streaming pipeline.
All tunable constants in one place.
"""

# --- Audio Streaming ---
AUDIO_SAMPLE_RATE = 16000           # Hz — Whisper expects 16kHz mono
AUDIO_BUFFER_SECONDS = 3.0         # accumulate this much audio before transcribing
AUDIO_CHUNK_MAX_QUEUE = 20         # max queued audio chunks before dropping
WHISPER_MODEL_SIZE = "base"        # "tiny" | "base" | "small" | "medium"

# --- Rolling Buffer & Aggregation ---
ROLLING_BUFFER_SECONDS = 10.0      # keep last N seconds for rolling metrics
ROLLING_MAX_CHUNKS = 10            # max chunks retained in the rolling window

# --- Pause Detection ---
PAUSE_MIN_DURATION_SEC = 0.3       # minimum gap to count as a pause
PAUSE_SILENCE_TOP_DB = 20          # librosa split threshold (dB below peak)

# --- Energy ---
ENERGY_REF_DB = -20.0              # reference level for dB normalization

# --- Video Streaming ---
VIDEO_TARGET_FPS = 5               # max frames/sec we process
VIDEO_FRAME_MAX_QUEUE = 10         # max queued video frames before dropping
VIDEO_JPEG_QUALITY = 70            # JPEG decode quality hint (client-side)

# --- NLP ---
NLP_SPACY_MODEL = "en_core_web_sm"

# --- Fusion ---
FUSION_EMIT_INTERVAL_SECONDS = 2.0 # how often to push fused summary to client
FUSION_EMA_ALPHA = 0.3             # exponential moving average smoothing

# --- WebSocket Protocol ---
WS_HEADER_AUDIO = 0x01
WS_HEADER_VIDEO = 0x02

# --- General ---
MAX_CONCURRENT_SESSIONS = 10
SESSION_TIMEOUT_SECONDS = 3600     # auto-cleanup after 1 hour idle
