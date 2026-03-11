/**
 * SessionView Page — Full session analysis (4-zone layout).
 * Zone A: Session Header (Risk Badge + Summary)
 * Zone B: Behavioral Timeline (Audio, Emotion, Flags)
 * Zone C: Smart Transcript
 * Zone D: Metrics Sidebar
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import SessionHeader from '../components/SessionHeader';
import BehavioralTimeline from '../components/BehavioralTimeline';
import SmartTranscript from '../components/SmartTranscript';
import MetricsSidebar from '../components/MetricsSidebar';

const mockData = {
    id: '7708c9e5',
    risk_band: 'Moderate Concern',
    risk_score: 0.58,
    summary: "Patient demonstrates high vocal energy and negative facial valence spikes (AU4/AU15), contrasting with positive verbal sentiment. This profile suggests potential emotional masking or social desirability bias. Recommended for priority clinical review for underlying distress indicators.",
    duration_seconds: 450,
    word_count: 842,
    timeline: Array.from({ length: 30 }, (_, i) => ({
        timestamp: i * 15,
        face_valence: i > 10 && i < 20 ? -0.4 - Math.random() * 0.3 : 0.1 + Math.random() * 0.2,
        sentiment_score: 0.3 + Math.random() * 0.4,
        arousal: i > 10 && i < 20 ? 0.7 + Math.random() * 0.2 : 0.3 + Math.random() * 0.2,
        flag: i === 15 ? 'Affective Mismatch' : null,
        severity: i === 15 ? 'HIGH' : null
    })),
    transcript: [
        { timestamp_start: 0, speaker: 'psychiatrist', text: "How have you been feeling since our last session?" },
        { timestamp_start: 4, speaker: 'patient', text: "Honestly, I've been doing completely fine. Everything is just... perfect.", flag: "Abstolutist Language" },
        { timestamp_start: 12, speaker: 'psychiatrist', text: "Perfect is a strong word. Any moments of hesitation?" },
        { timestamp_start: 18, speaker: 'patient', text: "No, never. I always manage to stay on top of things. I must be doing okay, right?", flag: "Masking Pattern" }
    ],
    metrics: {
        speech: {
            speech_rate_wpm: 132,
            pitch_std_dev: 24.5,
            filler_word_rate: 4.2,
            response_latency_ms: 850,
            silence_ratio: 0.18
        },
        nlp: {
            pronouns: { first_person_ratio: 0.12 },
            lexical: { absolutist_count: 8, avoidance_count: 2 }
        }
    },
    contradictions: [
        {
            rule: 'MASKING_DETECTED',
            severity: 'HIGH',
            note: 'Positive sentiment ("completely fine") aligns with high facial tension and negative valence spikes at 15m 12s.'
        },
        {
            rule: 'TEXT_VS_FACE',
            severity: 'MODERATE',
            note: 'Verbal claim of calm state contradicts elevated physiological arousal (AU6/AU12 mismatch).'
        }
    ]
};

export default function SessionView() {
    const { id } = useParams();
    const [session, setSession] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [transcript, setTranscript] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Mocking sophisticated multimodal data for development
        const timer = setTimeout(() => {
            const data = {
                ...mockData,
                id: id
            };
            setSession(data);
            setTimeline(data.timeline);
            setTranscript(data.transcript);
            setLoading(false);
        }, 800);
        return () => clearTimeout(timer);
    }, [id]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
                <div className="animate-spin w-10 h-10 border-4 border-primary-500 border-t-transparent rounded-full shadow-lg shadow-primary-500/20" />
                <p className="text-sm font-bold uppercase tracking-widest text-surface-400 animate-pulse">
                    Synthesizing Multimodal Report...
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in">
            {/* Breadcrumbs */}
            <nav className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-surface-500 mb-2">
                <Link to="/" className="hover:text-primary-400 transition-colors">Dashboard</Link>
                <span>/</span>
                <span className="text-surface-200">Session {id.slice(0, 8)}</span>
            </nav>

            {/* Zone A: Session Overview */}
            <SessionHeader session={session} />

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* Zones B & C: Analysis & Narrative (Column Span 8) */}
                <div className="lg:col-span-8 space-y-6">
                    {/* Zone B: Behavioral Timeline */}
                    <BehavioralTimeline data={timeline} />

                    {/* Zone C: Annotated Transcript */}
                    <SmartTranscript segments={transcript} />
                </div>

                {/* Zone D: Detailed Metrics Sidebar (Column Span 4) */}
                <div className="lg:col-span-4 sticky top-24">
                    <MetricsSidebar
                        features={session.metrics}
                        contradictions={session.contradictions}
                    />
                </div>
            </div>
        </div>
    );
}
