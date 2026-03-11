"""
NLP Processing Module.

Usage:
    from app.modules.nlp import NLPProcessor

    processor = NLPProcessor(use_transformer=True)
    result = await processor.process("Patient transcript text...")
    # or synchronously:
    result = processor.process_sync("Patient transcript text...")
    # or with timestamped segments:
    result = await processor.process(text, segments=[
        {"text": "I feel terrible", "start": 0.0, "end": 2.5},
        {"text": "everything is wrong", "start": 2.5, "end": 5.0},
    ])
"""
from app.modules.nlp.processor import NLPProcessor

__all__ = ["NLPProcessor"]
