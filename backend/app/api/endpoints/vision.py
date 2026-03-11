import os
import uuid
import asyncio
import tempfile
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.modules.vision.processor import VisionProcessor
from app.schemas.vision import VisionAnalysisResult

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Singleton processor — FaceMesh loaded once, reused across requests ──
vision_processor = VisionProcessor()


def preload():
    """Called at app startup to eagerly load the MediaPipe FaceMesh model."""
    logger.info("Preloading VisionProcessor (MediaPipe)…")
    vision_processor._ensure_face_mesh_loaded()
    logger.info(f"VisionProcessor ready (available={vision_processor.available})")


def _cleanup_file(path: str):
    """Background task: delete temp file after the response is sent."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"Cleaned up temp file: {path}")
    except OSError as e:
        logger.warning(f"Failed to clean temp file {path}: {e}")


@router.post("/analyze", response_model=VisionAnalysisResult)
async def analyze_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    """
    Upload a single patient-response video file.
    Processes it, returns structured metrics, then deletes the temp file.
    """
    response_id = str(uuid.uuid4())
    file_ext = (file.filename or "video.webm").rsplit(".", 1)[-1]

    # 1. Write upload to a temp file
    try:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_ext}", prefix=f"resp_{response_id}_"
        )
        contents = await file.read()
        tmp.write(contents)
        tmp.flush()
        tmp.close()
        file_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # 2. Schedule cleanup after response
    if background_tasks:
        background_tasks.add_task(_cleanup_file, file_path)

    # 3. Process in a thread so we don't block the async event loop
    try:
        result = await asyncio.to_thread(
            vision_processor.process_video, file_path, response_id
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        _cleanup_file(file_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")
