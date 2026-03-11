"""
Session API endpoints.
Handles interview session management, analysis results, and timeline data.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import (
    get_db, 
    get_audio_processor, 
    get_nlp_processor, 
    get_vision_processor, 
    get_fusion_engine,
    get_fusion_manager
)
from app.core.security import get_current_user
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionSummary,
    TimelineResponse,
    TranscriptResponse,
    SessionTextUpdate,
    SessionResultsResponse,
)
from app.modules.nlp.processor import NLPProcessor
from app.modules.audio.processor import AudioProcessor
from app.modules.vision.processor import VisionProcessor
from app.modules.fusion.engine import FusionEngine
from app.modules.fusion.manager import FusionManager

router = APIRouter()


import shutil
import pathlib
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Background Task Logic ─────────────────────────────

async def run_nlp_analysis(session_id: UUID, text: str, db: Session, nlp: NLPProcessor):
    """Background task to run NLP analysis and update session."""
    try:
        result = await nlp.process(text)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session:
            session.nlp_features = result
            db.commit()
    except Exception as e:
        print(f"NLP Background Task Error: {e}")


async def run_audio_analysis(session_id: UUID, file_path: str, db: Session, audio: AudioProcessor):
    """Background task to run Audio analysis and update session."""
    try:
        result = await audio.process(file_path)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session:
            session.speech_features = result.get("speech_features")
            session.transcript_data = result.get("transcript")
            session.duration_seconds = int(result.get("speech_features", {}).get("total_duration_sec", 0))
            db.commit()
    except Exception as e:
        print(f"Audio Background Task Error: {e}")


async def run_vision_analysis(session_id: UUID, file_path: str, db: Session, vision: VisionProcessor):
    """Background task to run Vision analysis and update session."""
    try:
        result = await vision.process(file_path)
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if session:
            session.vision_features = result.get("aggregate")
            session.timeline_data = result.get("per_second")
            db.commit()
    except Exception as e:
        print(f"Vision Background Task Error: {e}")


def save_upload_file(upload_file: UploadFile, session_id: UUID, modality: str) -> str:
    """Helper to save uploaded file to disk."""
    upload_dir = pathlib.Path(settings.UPLOAD_DIR) / str(session_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_ext = pathlib.Path(upload_file.filename).suffix
    dest_path = upload_dir / f"{modality}{file_ext}"
    
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return str(dest_path)


# ── Session CRUD ─────────────────────────────────────

@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all interview sessions for the current user."""
    # TODO: Query from database
    return []


from app.models.session import InterviewSession
from app.models.patient import Patient

@router.post("/", response_model=SessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new interview session.
    Requires a valid patient_id.
    """
    # 1. Verify patient exists
    patient = db.query(Patient).filter(Patient.id == session_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2. Create session record
    new_session = InterviewSession(
        patient_id=session_data.patient_id,
        interviewer_id=session_data.interviewer_id or current_user.get("username", "anonymous"),
        status="pending"
    )

    db.add(new_session)
    try:
        db.commit()
        db.refresh(new_session)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return new_session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific session by ID."""
    # TODO: Query session from database
    raise HTTPException(status_code=404, detail="Session not found")


# ── Analysis Results ─────────────────────────────────

@router.get("/{session_id}/summary", response_model=SessionSummary)
async def get_session_summary(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns high-level metrics, risk band, and summary text.
    This powers Zone A (Session Header) of the dashboard.
    """
    # TODO: Fetch analysis summary from database
    return SessionSummary(
        session_id=session_id,
        risk_band="Low Concern",
        risk_score=0.2,
        summary="No significant behavioral concerns detected in this session.",
        duration_seconds=0,
        word_count=0,
    )


@router.get("/{session_id}/timeline", response_model=TimelineResponse)
async def get_session_timeline(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns time-series data (1s granularity) for the Behavioral Timeline.
    Powers Zone B of the dashboard.
    """
    # TODO: Fetch timeline data from database
    return TimelineResponse(session_id=session_id, interval_sec=1, data=[])


@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
async def get_session_transcript(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns structured transcript with feature highlights.
    Powers Zone C (Smart Transcript) of the dashboard.
    """
    # TODO: Fetch transcript from database
    return TranscriptResponse(session_id=session_id, segments=[])


@router.get("/{session_id}/results", response_model=SessionResultsResponse)
async def get_session_results(
    session_id: UUID,
    db: Session = Depends(get_db),
    fusion_manager: FusionManager = Depends(get_fusion_manager),
    current_user: dict = Depends(get_current_user),
):
    """
    Get aggregated results and final risk assessment for a session.
    Triggers multimodal fusion on-demand using current features.
    """
    # 1. Trigger fusion (this updates session in DB with latest findings)
    session = await fusion_manager.run_fusion(session_id, db)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post("/{session_id}/text")
async def process_session_text(
    session_id: UUID,
    text_data: SessionTextUpdate,
    db: Session = Depends(get_db),
    nlp: NLPProcessor = Depends(get_nlp_processor),
    fusion_manager: FusionManager = Depends(get_fusion_manager),
    current_user: dict = Depends(get_current_user),
):
    """
    Process text input for a session and return analysis.
    Returns sentiment and clinical linguistic markers.
    """
    # 1. Validate session
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Validate input length (redundant due to Pydantic but good for explicit safety)
    if len(text_data.text.strip()) < 1:
        raise HTTPException(status_code=400, detail="Text input cannot be empty")

    try:
        # 3. Process (Non-blocking via thread pool in processor)
        result = await nlp.process(text_data.text)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"NLP processing failed: {result.get('errors')}")

        # 4. Store results in Session for Multimodal Fusion
        session.nlp_features = result
        
        if session.status == "pending":
            session.status = "processing"
        
        db.commit()

        # 5. Trigger Multimodal Fusion (Automatic Update)
        await fusion_manager.run_fusion(session_id, db)

        # 6. Return structured JSON matching clinical dashboard requirements
        return {
            "status": "success",
            "session_id": str(session_id),
            "sentiment": {
                "polarity": result.get("sentiment", {}).get("polarity", {}).get("compound", 0),
                "label": result.get("sentiment", {}).get("label", "neutral"),
                "emotions": result.get("sentiment", {}).get("emotions", {})
            },
            "linguistic_markers": {
                "absolutist_count": result.get("lexical", {}).get("absolutist_words", {}).get("count", 0),
                "first_person_ratio": result.get("lexical", {}).get("pronoun_analysis", {}).get("first_person_ratio", 0),
                "crisis_detected": result.get("meta", {}).get("crisis_detected", False),
                "lexical_summary": result.get("lexical", {})
            }
        }

    except Exception as e:
        logger.error(f"NLP endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── File Upload ──────────────────────────────────────

@router.post("/{session_id}/audio")
async def upload_audio(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    audio_proc: AudioProcessor = Depends(get_audio_processor),
    fusion_manager: FusionManager = Depends(get_fusion_manager),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload and process audio synchronously.
    Returns processed metrics in the response.
    Accepted formats: .wav, .mp3, .m4a
    """
    # 1. Validate session
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Validate file type
    allowed_extensions = {".wav", ".mp3", ".m4a", ".mp4", ".webm"}
    file_ext = pathlib.Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type {file_ext}. Allowed: {allowed_extensions}"
        )

    # 3. Save to temporary location
    temp_path = save_upload_file(file, session_id, f"temp_audio_{uuid.uuid4().hex[:8]}")
    
    try:
        # 4. Process (Non-blocking server-side via thread pool)
        result = await audio_proc.process(temp_path)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"Audio processing failed: {result.get('errors')}")

        # 5. Store results in Session
        session.speech_features = result.get("speech_features")
        session.transcript_data = result.get("transcript")
        session.duration_seconds = int(result.get("speech_features", {}).get("total_duration_sec", 0))
        session.status = "processing" # Still processing if others modules are pending
        
        db.commit()

        # 6. Trigger Multimodal Fusion (Automatic Update)
        await fusion_manager.run_fusion(session_id, db)

        # 7. Return processed metrics
        return {
            "status": "success",
            "session_id": str(session_id),
            "metrics": result.get("speech_features"),
            "transcript_summary": {
                "word_count": result.get("speech_features", {}).get("total_words"),
                "duration": result.get("speech_features", {}).get("total_duration_sec")
            }
        }

    except Exception as e:
        logger.error(f"Audio endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 7. Cleanup temporary file
        try:
            p = pathlib.Path(temp_path)
            if p.exists():
                p.unlink()
        except Exception as cleanup_err:
            logger.error(f"Failed to cleanup temp file {temp_path}: {cleanup_err}")


@router.post("/{session_id}/video")
async def upload_video(
    session_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    vision_proc: VisionProcessor = Depends(get_vision_processor),
    fusion_manager: FusionManager = Depends(get_fusion_manager),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload and process video synchronously.
    Returns facial metrics and stability scores.
    Accepted formats: .mp4, .webm
    """
    # 1. Validate session
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Validate file type
    allowed_extensions = {".mp4", ".webm", ".avi", ".mov"}
    file_ext = pathlib.Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported video type {file_ext}. Allowed: {allowed_extensions}"
        )

    # 3. Save to temporary location
    temp_path = save_upload_file(file, session_id, f"temp_video_{uuid.uuid4().hex[:8]}")
    
    try:
        # 4. Process (Non-blocking via thread pool in processor)
        # Efficient 1 FPS sampling is handled internally by VisionProcessor
        result = await vision_proc.process(temp_path)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"Vision processing failed: {result.get('errors')}")

        # 5. Store results in Session for Multimodal Fusion
        session.vision_features = result.get("aggregate")
        session.timeline_data = result.get("per_second")
        
        if session.status == "pending":
            session.status = "processing"
            
        db.commit()

        # 6. Trigger Multimodal Fusion (Automatic Update)
        await fusion_manager.run_fusion(session_id, db)

        # 7. Return structured metrics for clinical dashboard
        return {
            "status": "success",
            "session_id": str(session_id),
            "video_metadata": {
                "duration_sec": result.get("duration_sec"),
                "frames_analyzed": result.get("frames_analyzed"),
                "face_detection_rate": result.get("face_detection_rate")
            },
            "aggregate_metrics": result.get("aggregate"),
            "stability_scoring": result.get("stability")
        }

    except Exception as e:
        logger.error(f"Video endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # 7. Cleanup temporary file
        try:
            p = pathlib.Path(temp_path)
            if p.exists():
                p.unlink()
        except Exception as cleanup_err:
            logger.error(f"Failed to cleanup temp video file {temp_path}: {cleanup_err}")


# ── Clinician Notes ──────────────────────────────────

@router.post("/{session_id}/notes")
async def add_clinician_note(
    session_id: UUID,
    note: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Save clinician's manual observation/annotation (Audit logged).
    """
    # TODO: Save note to database + audit log
    return {"message": "Note saved", "session_id": str(session_id)}
