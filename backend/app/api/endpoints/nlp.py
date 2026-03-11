from fastapi import APIRouter, HTTPException, Body
from app.modules.nlp.processor import NLPProcessor
from app.schemas.nlp import NLPAnalysisResult
from pydantic import BaseModel

router = APIRouter()

# Singleton-ish
nlp_processor = NLPProcessor()

class TextRequest(BaseModel):
    session_id: str
    transcript: str
    segment_id: int = 0

@router.post("/analyze", response_model=NLPAnalysisResult)
async def analyze_text(request: TextRequest):
    """
    Analyze text transcript for sentiment and linguistic markers.
    """
    try:
        if not request.transcript.strip():
             raise HTTPException(status_code=400, detail="Transcript is empty")
             
        result = nlp_processor.analyze_text(
            request.transcript, 
            request.session_id, 
            request.segment_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
