"""
WebSocket endpoint for structured question-driven assessment.

/ws/assessment/{session_id}

Protocol:
  Client → Server:
    Binary: 0x01 + PCM float32  →  audio chunk
    Binary: 0x02 + JPEG bytes   →  video frame
    Text JSON:
      {"type": "submit_answer", "score": 0-4}
      {"type": "pause"}
      {"type": "resume"}
      {"type": "override_score", "question_id": "...", "score": 2}
      {"type": "skip_question"}

  Server → Client:
    JSON: {type: "question", data: {...}}
    JSON: {type: "face_data", data: {...}}
    JSON: {type: "transcript", data: {...}}
    JSON: {type: "audio_features", data: {...}}
    JSON: {type: "question_metrics", data: {...}}     — per-question snapshot
    JSON: {type: "assessment_complete", data: {...}}  — final report
    JSON: {type: "paused"|"resumed", data: {...}}
    JSON: {type: "status"|"error", data: {...}}
"""

import asyncio
import json
import logging
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import (
    WS_HEADER_AUDIO,
    WS_HEADER_VIDEO,
    AUDIO_BUFFER_SECONDS,
)
from app.core.session import session_manager
from app.modules.audio.streaming import StreamingAudioProcessor
from app.modules.vision.streaming import StreamingVisionProcessor
from app.modules.nlp.streaming import StreamingNLPProcessor
from app.modules.questionnaire.question_engine import question_engine
from app.modules.questionnaire.question_bank import RESPONSE_OPTIONS, DOMAIN_INFO, question_bank
from app.modules.questionnaire.report_generator import ReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter()

# Reuse preloaded processor instances
audio_processor = StreamingAudioProcessor()
vision_processor = StreamingVisionProcessor()
nlp_processor = StreamingNLPProcessor()
report_generator = ReportGenerator()


def _question_to_dict(q, index: int, total: int) -> dict:
    """Convert a Question object to a JSON-serializable dict."""
    domain_info = DOMAIN_INFO.get(q.domain, {})
    return {
        "id": q.id,
        "domain": q.domain,
        "domain_label": domain_info.get("label", q.domain),
        "text": q.text,
        "question_number": index + 1,
        "total_questions": total,
        "response_options": RESPONSE_OPTIONS,
    }


def _response_to_metrics(resp) -> dict:
    """Convert a QuestionResponse to a compact metrics dict for the frontend."""
    return {
        "question_id": resp.question_id,
        "domain": resp.domain,
        "self_report_score": resp.self_report_score,
        "duration_seconds": resp.duration_seconds,
        "confidence_proxy": resp.confidence_proxy,
        "hesitation_count": resp.hesitation_count,
        "hesitation_ratio": resp.hesitation_ratio,
        "facial_stability": resp.facial_stability,
        "emotional_intensity": resp.emotional_intensity,
        "blink_rate": resp.blink_rate,
        "avg_speech_rate": resp.avg_speech_rate,
        "avg_valence": resp.avg_valence,
        "avg_arousal": resp.avg_arousal,
        "total_words": resp.total_words,
        "total_pauses": resp.total_pauses,
        "pitch_variance": resp.pitch_variance,
    }


@router.websocket("/ws/assessment/{session_id}")
async def assessment_session(websocket: WebSocket, session_id: str):
    await websocket.accept()
    logger.info(f"[assessment] WebSocket connected: {session_id}")

    # Create streaming session for audio/video queues
    try:
        stream_session = session_manager.create_session(session_id, websocket)
    except RuntimeError as e:
        await websocket.send_json({"type": "error", "data": {"message": str(e)}})
        await websocket.close()
        return

    # Start assessment
    assess_id, first_question = question_engine.start_assessment()
    stream_session.is_recording = True

    # Send first question
    await _send(websocket, "status", {
        "state": "assessment_active",
        "session_id": session_id,
        "assessment_id": assess_id,
    })
    await _send(websocket, "question", _question_to_dict(
        first_question, 0, question_bank.total_questions
    ))

    # Launch background workers
    audio_task = asyncio.create_task(_assessment_audio_worker(stream_session, assess_id))
    vision_task = asyncio.create_task(_assessment_vision_worker(stream_session, assess_id))

    try:
        while True:
            message = await websocket.receive()

            # Binary: audio or video frame
            if "bytes" in message:
                data = message["bytes"]
                if len(data) < 2:
                    continue
                header = data[0]
                payload = data[1:]

                if header == WS_HEADER_AUDIO:
                    stream_session.append_audio(payload)
                    if stream_session.audio_buffer_duration >= AUDIO_BUFFER_SECONDS:
                        chunk = stream_session.flush_audio_buffer()
                        try:
                            stream_session.audio_queue.put_nowait(chunk)
                        except asyncio.QueueFull:
                            pass

                elif header == WS_HEADER_VIDEO:
                    try:
                        stream_session.video_queue.put_nowait(payload)
                    except asyncio.QueueFull:
                        pass

            # Text JSON: commands
            elif "text" in message:
                try:
                    msg = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")

                if msg_type == "submit_answer":
                    score = int(msg.get("score", 0))
                    score = max(0, min(4, score))

                    try:
                        next_q, completed = question_engine.complete_question(assess_id, score)
                    except ValueError as e:
                        await _send(websocket, "error", {"message": str(e)})
                        continue

                    # Send per-question metrics snapshot
                    responses = question_engine.get_responses(assess_id)
                    if responses:
                        latest = responses[-1]
                        await _send(websocket, "question_metrics", _response_to_metrics(latest))

                    if completed:
                        # Generate full report
                        report = report_generator.generate(question_engine, assess_id)
                        await _send(websocket, "assessment_complete", report.to_dict())
                        break
                    else:
                        q_index = question_engine.get_session(assess_id).current_index
                        await _send(websocket, "question", _question_to_dict(
                            next_q, q_index, question_bank.total_questions
                        ))

                elif msg_type == "pause":
                    question_engine.pause(assess_id)
                    await _send(websocket, "paused", {"session_id": session_id})

                elif msg_type == "resume":
                    question_engine.resume(assess_id)
                    await _send(websocket, "resumed", {"session_id": session_id})

                elif msg_type == "skip_question":
                    try:
                        next_q, completed = question_engine.skip_question(assess_id)
                    except ValueError as e:
                        await _send(websocket, "error", {"message": str(e)})
                        continue

                    responses = question_engine.get_responses(assess_id)
                    if responses:
                        await _send(websocket, "question_metrics", _response_to_metrics(responses[-1]))

                    if completed:
                        report = report_generator.generate(question_engine, assess_id)
                        await _send(websocket, "assessment_complete", report.to_dict())
                        break
                    else:
                        q_index = question_engine.get_session(assess_id).current_index
                        await _send(websocket, "question", _question_to_dict(
                            next_q, q_index, question_bank.total_questions
                        ))

                elif msg_type == "override_score":
                    q_id = msg.get("question_id")
                    new_score = int(msg.get("score", 0))
                    try:
                        question_engine.override_answer(assess_id, q_id, new_score)
                        await _send(websocket, "status", {
                            "state": "score_overridden",
                            "question_id": q_id,
                            "new_score": new_score,
                        })
                    except ValueError as e:
                        await _send(websocket, "error", {"message": str(e)})

    except WebSocketDisconnect:
        logger.info(f"[assessment] WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"[assessment] Error: {e}")
        await _send(websocket, "error", {"message": str(e)})
    finally:
        stream_session.is_recording = False
        for task in [audio_task, vision_task]:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        session_manager.remove_session(session_id)
        question_engine.remove_session(assess_id)
        logger.info(f"[assessment] Cleaned up: {session_id}")


# ── Background Workers ───────────────────────────────────────

async def _assessment_audio_worker(session, assess_id: str):
    """Process audio chunks and feed results to the QuestionEngine."""
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

        result = await loop.run_in_executor(
            None, audio_processor.process_chunk, pcm_bytes, segment_id
        )
        if result is None:
            continue

        # Send live transcript
        await _send(session.websocket, "transcript", result.transcript.model_dump())

        # Send live audio features
        await _send(session.websocket, "audio_features", result.features.model_dump())

        # Feed into QuestionEngine accumulators
        question_engine.accumulate_audio(assess_id, result.features.model_dump())
        question_engine.accumulate_transcript(assess_id, result.transcript.text)

        # NLP on transcript
        nlp_result = nlp_processor.process_segment(
            result.transcript.text, session.session_id, segment_id
        )
        if nlp_result:
            await _send(session.websocket, "nlp_result", nlp_result.model_dump())
            question_engine.accumulate_nlp(assess_id, nlp_result.model_dump())


async def _assessment_vision_worker(session, assess_id: str):
    """Process video frames and feed results to the QuestionEngine."""
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
        face_dict = face_data.model_dump()

        # Send live face data
        await _send(session.websocket, "face_data", face_dict)

        # Feed into QuestionEngine accumulators
        question_engine.accumulate_vision(assess_id, face_dict)


# ── Helper ───────────────────────────────────────────────────

async def _send(websocket: WebSocket, event_type: str, data: dict):
    try:
        await websocket.send_json({"type": event_type, "data": data})
    except Exception as e:
        logger.error(f"[assessment] Failed to send '{event_type}': {e}")
