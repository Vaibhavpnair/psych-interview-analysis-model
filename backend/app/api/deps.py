"""
Dependency injection for database sessions and common utilities.
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

from app.modules.audio.processor import AudioProcessor
from app.modules.nlp.processor import NLPProcessor
from app.modules.vision.processor import VisionProcessor
from app.modules.fusion.engine import FusionEngine
from app.modules.fusion.manager import FusionManager

# ── SQLAlchemy Engine ────────────────────────────────
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── AI Processors (Singletons) ────────────────────────
# These are initialized lazily on first use by get_* dependencies.
_audio_processor = AudioProcessor(whisper_model_size=settings.WHISPER_MODEL_SIZE)
_nlp_processor = NLPProcessor()
_vision_processor = VisionProcessor()
_fusion_engine = FusionEngine()
_fusion_manager = FusionManager(engine=_fusion_engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Automatically closes the session after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_audio_processor() -> AudioProcessor:
    """Dependency that returns the singleton AudioProcessor."""
    return _audio_processor


def get_nlp_processor() -> NLPProcessor:
    """Dependency that returns the singleton NLPProcessor."""
    return _nlp_processor


def get_vision_processor() -> VisionProcessor:
    """Dependency that returns the singleton VisionProcessor."""
    return _vision_processor


def get_fusion_engine() -> FusionEngine:
    """Dependency that returns the singleton FusionEngine."""
    return _fusion_engine


def get_fusion_manager() -> FusionManager:
    """Dependency that returns the singleton FusionManager."""
    return _fusion_manager
