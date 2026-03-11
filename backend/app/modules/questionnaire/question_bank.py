"""
DSM-5 Level 1 Cross-Cutting Symptom Measure — Question Bank (Adult).

Contains the 23 standardised questions, domain mapping, and threshold rules.
No diagnosis logic — only data structure and threshold classification.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ── Response Scale ───────────────────────────────────────────
RESPONSE_OPTIONS = [
    {"value": 0, "label": "None", "description": "Not at all"},
    {"value": 1, "label": "Slight", "description": "Rare, less than a day or two"},
    {"value": 2, "label": "Mild", "description": "Several days"},
    {"value": 3, "label": "Moderate", "description": "More than half the days"},
    {"value": 4, "label": "Severe", "description": "Nearly every day"},
]


# ── Threshold Types ──────────────────────────────────────────
THRESHOLD_MILD = "mild"       # score >= 2 to flag
THRESHOLD_SLIGHT = "slight"   # score >= 1 to flag

THRESHOLD_VALUES = {
    THRESHOLD_MILD: 2,
    THRESHOLD_SLIGHT: 1,
}


# ── Question Dataclass ───────────────────────────────────────
@dataclass
class Question:
    """A single DSM-5 Level 1 cross-cutting question."""
    id: str
    domain: str
    text: str
    threshold_type: str  # "mild" or "slight"

    @property
    def threshold_value(self) -> int:
        """Minimum score to exceed threshold for this question's domain."""
        return THRESHOLD_VALUES[self.threshold_type]


# ── Domain Metadata ──────────────────────────────────────────
DOMAIN_INFO = {
    "depression":              {"label": "Depression",              "dsm5_section": "I",    "level2": True},
    "anger":                   {"label": "Anger",                   "dsm5_section": "II",   "level2": True},
    "mania":                   {"label": "Mania",                   "dsm5_section": "III",  "level2": True},
    "anxiety":                 {"label": "Anxiety",                 "dsm5_section": "IV",   "level2": True},
    "somatic_symptoms":        {"label": "Somatic Symptoms",        "dsm5_section": "V",    "level2": True},
    "suicidal_ideation":       {"label": "Suicidal Ideation",       "dsm5_section": "VI",   "level2": False},
    "psychosis":               {"label": "Psychosis",               "dsm5_section": "VII",  "level2": True},
    "sleep_problems":          {"label": "Sleep Problems",          "dsm5_section": "VIII", "level2": True},
    "memory":                  {"label": "Memory",                  "dsm5_section": "IX",   "level2": True},
    "repetitive_thoughts":     {"label": "Repetitive Thoughts & Behaviors", "dsm5_section": "X", "level2": True},
    "dissociation":            {"label": "Dissociation",            "dsm5_section": "XI",   "level2": True},
    "personality_functioning": {"label": "Personality Functioning",  "dsm5_section": "XII",  "level2": True},
    "substance_use":           {"label": "Substance Use",           "dsm5_section": "XIII", "level2": True},
}


# ── The 23 Questions ─────────────────────────────────────────
_QUESTIONS = [
    # Domain I: Depression (Q1–Q2)
    Question("dsm5_cc_01", "depression",   "Little interest or pleasure in doing things?", THRESHOLD_MILD),
    Question("dsm5_cc_02", "depression",   "Feeling down, depressed, or hopeless?", THRESHOLD_MILD),

    # Domain II: Anger (Q3)
    Question("dsm5_cc_03", "anger",        "Feeling more irritated, grouchy, or angry than usual?", THRESHOLD_MILD),

    # Domain III: Mania (Q4–Q5)
    Question("dsm5_cc_04", "mania",        "Sleeping less than usual, but still have a lot of energy?", THRESHOLD_MILD),
    Question("dsm5_cc_05", "mania",        "Starting lots more projects than usual or doing more risky things than usual?", THRESHOLD_MILD),

    # Domain IV: Anxiety (Q6–Q8)
    Question("dsm5_cc_06", "anxiety",      "Feeling nervous, anxious, frightened, worried, or on edge?", THRESHOLD_MILD),
    Question("dsm5_cc_07", "anxiety",      "Feeling panic or being frightened?", THRESHOLD_MILD),
    Question("dsm5_cc_08", "anxiety",      "Avoiding situations that make you anxious?", THRESHOLD_MILD),

    # Domain V: Somatic Symptoms (Q9–Q10)
    Question("dsm5_cc_09", "somatic_symptoms", "Unexplained aches and pains?", THRESHOLD_MILD),
    Question("dsm5_cc_10", "somatic_symptoms", "Feeling that your illnesses are not being taken seriously enough?", THRESHOLD_MILD),

    # Domain VI: Suicidal Ideation (Q11) — SLIGHT threshold
    Question("dsm5_cc_11", "suicidal_ideation", "Thoughts of actually hurting yourself?", THRESHOLD_SLIGHT),

    # Domain VII: Psychosis (Q12–Q13) — SLIGHT threshold
    Question("dsm5_cc_12", "psychosis",    "Hearing things other people couldn't hear?", THRESHOLD_SLIGHT),
    Question("dsm5_cc_13", "psychosis",    "Feeling that someone could hear your thoughts?", THRESHOLD_SLIGHT),

    # Domain VIII: Sleep Problems (Q14)
    Question("dsm5_cc_14", "sleep_problems", "Problems with sleep that affected your sleep quality overall?", THRESHOLD_MILD),

    # Domain IX: Memory (Q15)
    Question("dsm5_cc_15", "memory",       "Problems with memory or learning new information?", THRESHOLD_MILD),

    # Domain X: Repetitive Thoughts & Behaviors (Q16–Q17)
    Question("dsm5_cc_16", "repetitive_thoughts", "Unpleasant thoughts, urges, or images that repeatedly enter your mind?", THRESHOLD_MILD),
    Question("dsm5_cc_17", "repetitive_thoughts", "Feeling driven to perform certain behaviors over and over again?", THRESHOLD_MILD),

    # Domain XI: Dissociation (Q18–Q19)
    Question("dsm5_cc_18", "dissociation", "Feeling detached or distant from yourself or your surroundings?", THRESHOLD_MILD),
    Question("dsm5_cc_19", "dissociation", "Not knowing who you really are or what you want out of life?", THRESHOLD_MILD),

    # Domain XII: Personality Functioning (Q20)
    Question("dsm5_cc_20", "personality_functioning", "Not feeling close to other people?", THRESHOLD_MILD),

    # Domain XIII: Substance Use (Q21–Q23) — SLIGHT threshold
    Question("dsm5_cc_21", "substance_use", "Drinking at least 4 drinks of alcohol in a single day?", THRESHOLD_SLIGHT),
    Question("dsm5_cc_22", "substance_use", "Smoking any tobacco products?", THRESHOLD_SLIGHT),
    Question("dsm5_cc_23", "substance_use", "Using medications or drugs in greater amounts than prescribed?", THRESHOLD_SLIGHT),
]


# ── QuestionBank Class ───────────────────────────────────────
class QuestionBank:
    """
    Provides access to the 23 DSM-5 Level 1 Cross-Cutting questions,
    domain metadata, and threshold rules.
    """

    def __init__(self):
        self.questions: List[Question] = list(_QUESTIONS)
        self._by_id = {q.id: q for q in self.questions}
        self._by_domain: dict[str, List[Question]] = {}
        for q in self.questions:
            self._by_domain.setdefault(q.domain, []).append(q)

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def domains(self) -> list[str]:
        """Ordered list of unique domains."""
        seen = []
        for q in self.questions:
            if q.domain not in seen:
                seen.append(q.domain)
        return seen

    def get_by_id(self, question_id: str) -> Optional[Question]:
        return self._by_id.get(question_id)

    def get_by_domain(self, domain: str) -> List[Question]:
        return self._by_domain.get(domain, [])

    def get_domain_info(self, domain: str) -> dict:
        return DOMAIN_INFO.get(domain, {})

    def get_threshold_value(self, question_id: str) -> int:
        q = self.get_by_id(question_id)
        return q.threshold_value if q else 2

    def get_question_at_index(self, index: int) -> Optional[Question]:
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None


# Singleton
question_bank = QuestionBank()
