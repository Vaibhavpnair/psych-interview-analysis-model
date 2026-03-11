"""
Audio Processing Module.

Usage:
    from app.modules.audio import AudioProcessor

    processor = AudioProcessor(whisper_model_size="base")
    result = await processor.process("interview.wav")
    # or synchronously:
    result = processor.process_sync("interview.wav")
"""
from app.modules.audio.processor import AudioProcessor

__all__ = ["AudioProcessor"]
