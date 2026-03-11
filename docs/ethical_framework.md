# Ethical Framework

## Core Principles
1. **Non-Maleficence**: The system must never harm the patient
2. **Human Authority**: AI is a "Second Opinion," never the "First Opinion"
3. **Privacy by Design**: Patient data is treated as sensitive — minimize storage, maximize redaction

## Safety Constraints
- **No Diagnosis Rule**: API never returns ICD-10/DSM-V codes
- **Emergency Protocol**: CRITICAL ALERT for explicit suicidal intent, requires clinician acknowledgment
- **No Auto-Police**: System only notifies the doctor, never calls emergency services

## Explainability (XAI)
- Feature Attribution: "Risk Score is 80/100 because Speech Rate < 80wpm AND Absolutist Count > 5"
- Contextual Linking: Click risk flag → jump to exact video frame and transcript line
- Confidence Bars: Wide intervals = "AI is uncertain, please verify"

## Bias Mitigation
- Per-Subject Baseline: Compare patient to themselves (not population norms)
- Accent-Agnostic VAD: Diverse training data for voice activity detection

## Data Privacy
- PII Redaction: Automatic bleeping of names/addresses via NER
- Face Blurring: Default for secondary reviewers, unlockable by assigned psychiatrist
- Immutable Audit Logs: Every AI score override is hashed and logged
