"""
WebSocket streaming endpoints:
  /ws/stream/{session_id}  — full multimodal (audio + video)
  /ws/audio/{session_id}   — audio-only (lighter, no video processing)

Protocol:
  Client → Server (binary):
    0x01 + PCM float32 bytes  →  audio chunk
    0x02 + JPEG bytes         →  video frame  (only on /ws/stream)

  Server → Client (JSON text):
    { "type": "transcript" | "audio_features" | "audio_update" |
              "face_data" | "nlp_result" | "fusion_summary" |
              "error" | "status",
      "data": { ... } }
"""

import asyncio
import logging
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import (
    WS_HEADER_AUDIO,
    WS_HEADER_VIDEO,
    AUDIO_BUFFER_SECONDS,
    FUSION_EMIT_INTERVAL_SECONDS,
)
from app.core.session import session_manager, SessionState, AudioChunkRecord
from app.modules.audio.streaming import StreamingAudioProcessor
from app.modules.vision.streaming import StreamingVisionProcessor
from app.modules.nlp.streaming import StreamingNLPProcessor
from app.modules.fusion.engine import fusion_engine
from app.schemas.streaming import RollingAudioStats, AudioUpdateEvent

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Shared processor instances (preloaded at startup) ───────
audio_processor = StreamingAudioProcessor()
vision_processor = StreamingVisionProcessor()
nlp_processor = StreamingNLPProcessor()


def preload_models():
    """Called from main.py startup event."""
    audio_processor.preload()
    vision_processor.preload()
    logger.info("All streaming models preloaded.")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 1: Full Multimodal Streaming (audio + video)
# ═══════════════════════════════════════════════════════════

@router.websocket("/ws/stream/{session_id}")
async def stream_session(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"[multimodal] WebSocket connected: session={session_id}")

    try:
        session = session_manager.create_session(session_id, websocket)
    except RuntimeError as e:
        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        await websocket.close()
        return

    session.is_recording = True
    await _send_event(websocket, "status", {"state": "recording", "session_id": session_id})

    # Launch background workers
    audio_task = asyncio.create_task(_audio_worker(session))
    vision_task = asyncio.create_task(_vision_worker(session))
    fusion_task = asyncio.create_task(_fusion_emitter(session))

    try:
        while True:
            data = await websocket.receive_bytes()
            if len(data) < 2:
                continue

            header = data[0]
            payload = data[1:]

            if header == WS_HEADER_AUDIO:
                session.append_audio(payload)
                if session.audio_buffer_duration >= AUDIO_BUFFER_SECONDS:
                    chunk = session.flush_audio_buffer()
                    try:
                        session.audio_queue.put_nowait(chunk)
                    except asyncio.QueueFull:
                        logger.warning(f"[{session_id}] Audio queue full, dropping chunk")

            elif header == WS_HEADER_VIDEO:
                try:
                    session.video_queue.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

    except WebSocketDisconnect:
        logger.info(f"[multimodal] WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"[multimodal] WebSocket error: {e}")
        await _send_event(websocket, "error", {"message": str(e)})
    finally:
        session.is_recording = False
        for task in [audio_task, vision_task, fusion_task]:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        session_manager.remove_session(session_id)
        logger.info(f"[multimodal] Session cleaned up: {session_id}")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 2: Vision-Only Streaming (no audio, lightweight)
# ═══════════════════════════════════════════════════════════

@router.websocket("/ws/vision/{session_id}")
async def vision_stream_session(websocket: WebSocket, session_id: str):
    """
    Dedicated vision-only WebSocket for the Facial Analysis panel.
    Client sends raw JPEG bytes (no header byte needed).
    Server returns JSON: { type: "face_data", data: { ... } }
    """
    await websocket.accept()
    logger.info(f"[vision-only] WebSocket connected: session={session_id}")

    try:
        session = session_manager.create_session(session_id, websocket)
    except RuntimeError as e:
        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        await websocket.close()
        return

    session.is_recording = True
    await _send_event(websocket, "status", {
        "state": "recording",
        "session_id": session_id,
        "mode": "vision_only",
    })

    vision_task = asyncio.create_task(_vision_worker(session))

    try:
        while True:
            jpeg_bytes = await websocket.receive_bytes()
            if len(jpeg_bytes) < 100:  # too small to be a valid JPEG
                continue
            try:
                session.video_queue.put_nowait(jpeg_bytes)
            except asyncio.QueueFull:
                pass  # drop frame if queue full

    except WebSocketDisconnect:
        logger.info(f"[vision-only] WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"[vision-only] WebSocket error: {e}")
        await _send_event(websocket, "error", {"message": str(e)})
    finally:
        session.is_recording = False
        vision_task.cancel()
        try:
            await vision_task
        except asyncio.CancelledError:
            pass
        session_manager.remove_session(session_id)
        logger.info(f"[vision-only] Session cleaned up: {session_id}")


# ═══════════════════════════════════════════════════════════
# ENDPOINT 3: Audio-Only Streaming (no video, lighter)
# ═══════════════════════════════════════════════════════════

@router.websocket("/ws/audio/{session_id}")
async def audio_stream_session(websocket: WebSocket, session_id: str):
    """
    Dedicated audio-only WebSocket.
    Client sends raw PCM float32 bytes (no header byte needed).
    Server returns incremental JSON: transcript, audio_features,
    audio_update (with rolling stats), nlp_result.
    """
    await websocket.accept()
    logger.info(f"[audio-only] WebSocket connected: session={session_id}")

    try:
        session = session_manager.create_session(session_id, websocket)
    except RuntimeError as e:
        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        await websocket.close()
        return

    session.is_recording = True
    await _send_event(websocket, "status", {
        "state": "recording",
        "session_id": session_id,
        "mode": "audio_only",
    })

    audio_task = asyncio.create_task(_audio_worker(session))

    try:
        while True:
            # Audio-only: raw bytes, no header
            pcm_bytes = await websocket.receive_bytes()
            if len(pcm_bytes) < 4:
                continue

            session.append_audio(pcm_bytes)
            if session.audio_buffer_duration >= AUDIO_BUFFER_SECONDS:
                chunk = session.flush_audio_buffer()
                try:
                    session.audio_queue.put_nowait(chunk)
                except asyncio.QueueFull:
                    logger.warning(f"[{session_id}] Audio queue full, dropping chunk")

    except WebSocketDisconnect:
        logger.info(f"[audio-only] WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"[audio-only] WebSocket error: {e}")
        await _send_event(websocket, "error", {"message": str(e)})
    finally:
        session.is_recording = False
        audio_task.cancel()
        try:
            await audio_task
        except asyncio.CancelledError:
            pass
        session_manager.remove_session(session_id)
        logger.info(f"[audio-only] Session cleaned up: {session_id}")


# ═══════════════════════════════════════════════════════════
# BACKGROUND WORKERS
# ═══════════════════════════════════════════════════════════

async def _audio_worker(session: SessionState):
    """
    Pull audio chunks from queue, process in executor, push to
    rolling buffer, send incremental results to client.
    """
    loop = asyncio.get_event_loop()

    while session.is_recording:
        try:
            pcm_bytes = await asyncio.wait_for(
                session.audio_queue.get(), timeout=1.0
            )
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break

        segment_id = session.audio_segment_counter
        session.audio_segment_counter += 1

        # Offload CPU-heavy Whisper + librosa to thread pool
        result = await loop.run_in_executor(
            None, audio_processor.process_chunk, pcm_bytes, segment_id
        )

        if result is None:
            continue

        # ── 1. Send transcript ──────────────────────────────
        await _send_event(
            session.websocket, "transcript",
            result.transcript.model_dump(),
        )

        # ── 2. Push to rolling buffer ───────────────────────
        record = AudioChunkRecord(
            segment_id=segment_id,
            timestamp=time.time(),
            duration=result.features.chunk_duration,
            transcript=result.transcript.text,
            pitch_mean=result.features.pitch_mean,
            pitch_std=result.features.pitch_std,
            energy_rms=result.features.energy_rms,
            energy_db=result.features.energy_db,
            silence_ratio=result.features.silence_ratio,
            speech_rate_wpm=result.features.speech_rate_wpm,
            pause_count=result.features.pause_count,
            pauses=[p.model_dump() for p in result.features.pauses],
            word_count=result.features.word_count,
        )
        session.push_audio_chunk(record)

        # ── 3. Compute rolling stats ────────────────────────
        rolling_dict = session.get_rolling_stats()
        rolling_stats = RollingAudioStats(**rolling_dict)

        # ── 4. Send audio_update (chunk + rolling + cumulative)
        audio_update = AudioUpdateEvent(
            chunk=result.features,
            rolling=rolling_stats,
            cumulative_words=session.total_word_count,
            cumulative_pauses=session.total_pause_count,
            cumulative_duration=round(session.total_audio_duration, 2),
        )
        await _send_event(
            session.websocket, "audio_update",
            audio_update.model_dump(),
        )

        # ── 5. Also send legacy audio_features for backwards compat
        await _send_event(
            session.websocket, "audio_features",
            result.features.model_dump(),
        )

        # ── 6. NLP on the transcript ────────────────────────
        nlp_result = nlp_processor.process_segment(
            result.transcript.text,
            session.session_id,
            segment_id,
        )
        if nlp_result:
            await _send_event(
                session.websocket, "nlp_result",
                nlp_result.model_dump(),
            )
            fusion_engine.update_nlp(session, nlp_result)

        # ── 7. Update fusion ────────────────────────────────
        fusion_engine.update_audio(session, result)
        session.all_transcripts.append(result.transcript.text)


async def _vision_worker(session: SessionState):
    """Pull video frames from queue, process, send results."""
    while session.is_recording:
        try:
            jpeg_bytes = await asyncio.wait_for(
                session.video_queue.get(), timeout=1.0
            )
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            break

        frame_index = session.frame_counter
        session.frame_counter += 1

        face_data = vision_processor.process_frame(jpeg_bytes, frame_index)
        await _send_event(session.websocket, "face_data", face_data.model_dump())
        fusion_engine.update_vision(session, face_data)


async def _fusion_emitter(session: SessionState):
    """Periodically emit a fused behavioral summary."""
    while session.is_recording:
        try:
            await asyncio.sleep(FUSION_EMIT_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            break

        if session.fusion_sample_count == 0:
            continue

        summary = fusion_engine.get_summary(session)
        await _send_event(session.websocket, "fusion_summary", summary.model_dump())


# ── Helpers ──────────────────────────────────────────────────

async def _send_event(websocket: WebSocket, event_type: str, data: dict):
    """Send a typed JSON event to the client."""
    try:
        await websocket.send_json({"type": event_type, "data": data})
    except Exception as e:
        logger.error(f"Failed to send event '{event_type}': {e}")
