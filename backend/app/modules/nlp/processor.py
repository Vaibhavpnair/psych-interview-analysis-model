from app.schemas.nlp import NLPAnalysisResult, SentimentData, LinguisticFeatures
import time

class NLPProcessor:
    def __init__(self):
        self._nlp = None
        self.available = True
        
        # Lexicons for rule-based analysis
        self.positive_terms = {"good", "great", "happy", "excellent", "positive", "wonderful", "amazing", "better", "improve", "well", "fine"}
        self.negative_terms = {"bad", "sad", "angry", "terrible", "negative", "awful", "horrible", "worse", "down", "fail", "pain", "hurt", "tired"}
        
        self.absolutist_terms = {
            "always", "never", "everyone", "nobody", "completely", "totally", 
            "entirely", "absolutely", "constantly", "forever", "everything"
        }
        self.avoidance_terms = {
            "maybe", "perhaps", "guess", "dunno", "pass", "skip"
        }

    def _ensure_models_loaded(self):
        if self._nlp is not None:
            return True
        try:
            import spacy
            # Try to load, if fails, we'll fall back to basic splitting
            self._nlp = spacy.load("en_core_web_sm")
            return True
        except Exception:
            self._nlp = None
            return True

    def analyze_text(self, transcript: str, session_id: str, segment_id: int = 0) -> NLPAnalysisResult:
        self._ensure_models_loaded()
        start_time = time.time()
        
        text = transcript.lower()
        
        # 1. Tokenization
        if self._nlp:
            doc = self._nlp(text)
            tokens = [token.text for token in doc]
            sentences = list(doc.sents)
        else:
            tokens = text.split()
            sentences = [text]
        
        # 2. Extract Features
        absolutist_matches = [t for t in tokens if t in self.absolutist_terms]
        avoidance_matches = [t for t in tokens if t in self.avoidance_terms]
        first_person_count = sum(1 for t in tokens if t in {"i", "me", "my", "mine", "myself"})
        
        sentence_complexity = len(tokens) / len(sentences) if sentences else 0

        # 3. Rule-Based Sentiment Analysis (Fast & Non-blocking)
        pos_count = sum(1 for t in tokens if t in self.positive_terms)
        neg_count = sum(1 for t in tokens if t in self.negative_terms)
        
        if (pos_count + neg_count) > 0:
            polarity = (pos_count - neg_count) / (pos_count + neg_count)
            label = "positive" if polarity > 0.1 else "negative" if polarity < -0.1 else "neutral"
            score = abs(polarity)
        else:
            polarity = 0.0
            label = "neutral"
            score = 1.0

        return NLPAnalysisResult(
            session_id=session_id,
            segment_id=segment_id,
            transcript=transcript,
            sentiment=SentimentData(
                polarity=polarity,
                label=label,
                confidence=score
            ),
            features=LinguisticFeatures(
                absolutist_count=len(absolutist_matches),
                absolutist_words=absolutist_matches,
                first_person_pronouns=first_person_count,
                avoidance_words=avoidance_matches,
                sentence_complexity=sentence_complexity
            ),
            processing_time=time.time() - start_time
        )
