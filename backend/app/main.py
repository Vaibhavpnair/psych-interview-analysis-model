import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


# ── Lifespan: startup / shutdown ────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Preloading streaming models...")
    from app.api.endpoints.streaming import preload_models
    preload_models()

    # Preload audio + vision processor models (once, reused across requests)
    from app.api.endpoints.audio import preload as preload_audio
    from app.api.endpoints.vision import preload as preload_vision
    preload_audio()
    preload_vision()

    logger.info("Startup complete.")
    yield
    # --- Shutdown ---
    from app.core.session import session_manager
    for s in session_manager.all_sessions():
        session_manager.remove_session(s.session_id)
    logger.info("All sessions cleaned up. Shutdown complete.")


app = FastAPI(
    title="Psychiatrist Interview Assistant",
    description="Multimodal AI Decision Support System",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "System Operational — Real-Time Streaming Ready"}


@app.get("/health")
def health_check():
    from app.core.session import session_manager
    return {
        "status": "healthy",
        "active_sessions": session_manager.active_count,
    }


# Register Routers — existing REST endpoints
from app.api.endpoints import audio, nlp, vision, questionnaire

app.include_router(audio.router, prefix="/api/audio", tags=["Audio"])
app.include_router(nlp.router, prefix="/api/nlp", tags=["NLP"])
app.include_router(vision.router, prefix="/api/vision", tags=["Vision"])
app.include_router(questionnaire.router, prefix="/api/questionnaire", tags=["Questionnaire"])

# Register Router — real-time streaming
from app.api.endpoints import streaming, assessment

app.include_router(streaming.router, tags=["Streaming"])
app.include_router(assessment.router, tags=["Assessment"])
