"""
Multimodal Fusion Module.

Usage:
    from app.modules.fusion import FusionEngine

    engine = FusionEngine()
    report = engine.fuse(
        audio=audio_processor_result,
        nlp=nlp_processor_result,
        vision=vision_processor_result,
    )
    print(report["risk_assessment"]["risk_band"])     # "Low Concern"
    print(report["escalation"]["urgency"])            # "ROUTINE"
    print(report["explainability"]["summary"])        # Human-readable summary
"""
from app.modules.fusion.engine import FusionEngine

__all__ = ["FusionEngine"]
