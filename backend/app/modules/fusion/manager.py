"""
Fusion Manager — Multimodal orchestration logic.

Coordinates between the database, session models, and the FusionEngine
to generate consolidated behavioral risk reports.
"""
import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.session import InterviewSession
from app.modules.fusion.engine import FusionEngine

logger = logging.getLogger(__name__)

class FusionManager:
    """
    Orchestrates the multimodal fusion process for interview sessions.
    
    Responsibilities:
        - Fetching session data from DB
        - Invoking FusionEngine with available modality features
        - Updating session status and result records
        - Ensuring explainability and ethical constraints
    """

    def __init__(self, engine: FusionEngine = None):
        self.engine = engine or FusionEngine()

    async def run_fusion(self, session_id: UUID, db: Session) -> InterviewSession:
        """
        Run the multimodal fusion pipeline for a specific session.
        Calculates risk score, confidence, contradictions, and escalation.
        """
        logger.info(f"Running multimodal fusion for session: {session_id}")
        
        # 1. Fetch session
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            logger.error(f"Fusion failed: Session {session_id} not found")
            return None

        # 2. Execute Fusion
        try:
            report = self.engine.fuse(
                audio=session.speech_features or {},
                nlp=session.nlp_features or {},
                vision=session.vision_features or {}
            )

            # 3. Update Session Record
            session.fusion_result = report
            
            # Update high-level dashboard fields
            risk_assessment = report.get("risk_assessment", {})
            session.risk_band = risk_assessment.get("risk_band", "Low Concern")
            session.risk_score = risk_assessment.get("raw_score", 0.0)
            
            explainability = report.get("explainability", {})
            session.summary = explainability.get("summary", "")
            
            # Update status if all completed or significant results found
            if session.status == "processing":
                 # Heuristic: If we have at least one significant result, we can mark as preliminary completed
                 # or wait for explicit completion. For now, we update on every fusion run.
                 session.completed_at = datetime.now(timezone.utc)
                 session.status = "completed"

            db.commit()
            db.refresh(session)
            
            logger.info(f"Fusion complete for {session_id}. Risk: {session.risk_band} ({session.risk_score})")
            return session

        except Exception as e:
            logger.error(f"Fusion Error for session {session_id}: {e}", exc_info=True)
            db.rollback()
            return session
