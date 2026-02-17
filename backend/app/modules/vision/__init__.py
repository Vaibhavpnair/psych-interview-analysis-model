"""
Vision Processing Module.

Usage:
    from app.modules.vision import VisionProcessor

    processor = VisionProcessor(analysis_fps=1.0)
    result = await processor.process("interview.mp4")
    # With neutral baseline comparison:
    result = await processor.process("interview.mp4", baseline={
        "valence": 0.05, "arousal": 0.15,
        "au_means": {"AU4": 0.1, "AU12": 0.2, ...}
    })
    # or synchronously:
    result = processor.process_sync("interview.mp4")
"""
from app.modules.vision.processor import VisionProcessor

__all__ = ["VisionProcessor"]
