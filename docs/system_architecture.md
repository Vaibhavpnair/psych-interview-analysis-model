# System Architecture

See the full design documentation in the project's design artifacts:
- Speech Processing Module Design
- NLP Module Design
- Multimodal Fusion Layer Design
- Dashboard & Backend Design
- Ethical & Explainability Architecture
- Evaluation Strategy & Academic Validation
- Technology Stack Selection

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DATA CAPTURE LAYER                    │
│  Video Camera → MP4    |    Microphone → WAV            │
└────────────┬───────────┴────────────┬───────────────────┘
             │                        │
    ┌────────▼────────┐      ┌────────▼────────┐
    │  VISION MODULE  │      │  AUDIO MODULE   │
    │  MediaPipe Mesh │      │  Whisper STT    │
    │  DeepFace       │      │  Librosa/Praat  │
    └────────┬────────┘      └───┬────────┬────┘
             │                   │        │
             │            ┌──────▼──┐  ┌──▼──────────┐
             │            │Transcript│  │Prosody Feat.│
             │            └──┬──────┘  └──┬──────────┘
             │               │            │
    ┌────────▼────────┐  ┌───▼────────────▼───┐
    │  Face Features  │  │    NLP MODULE       │
    │  Valence/Arousal│  │  spaCy + Sentiment  │
    └────────┬────────┘  └───────┬────────────┘
             │                   │
    ┌────────▼───────────────────▼───────────┐
    │          MULTIMODAL FUSION             │
    │  Rule-Based + Anomaly + Contradiction  │
    │  → Behavioral Risk Score (0-100)       │
    └────────────────┬──────────────────────┘
                     │
    ┌────────────────▼──────────────────────┐
    │         PSYCHIATRIST DASHBOARD        │
    │  Timeline | Transcript | Risk Badge   │
    └───────────────────────────────────────┘
```
