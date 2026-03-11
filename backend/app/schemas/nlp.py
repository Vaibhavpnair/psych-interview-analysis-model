from pydantic import BaseModel
from typing import List, Dict, Optional

class SentimentData(BaseModel):
    polarity: float  # -1.0 to 1.0
    label: str       # "positive", "negative", "neutral"
    confidence: float # 0.0 to 1.0

class LinguisticFeatures(BaseModel):
    absolutist_count: int
    absolutist_words: List[str]
    first_person_pronouns: int
    avoidance_words: List[str]
    sentence_complexity: float

class NLPAnalysisResult(BaseModel):
    session_id: str
    segment_id: int
    transcript: str
    sentiment: SentimentData
    features: LinguisticFeatures
    processing_time: float
