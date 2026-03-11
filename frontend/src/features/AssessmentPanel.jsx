import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
    Stethoscope, ArrowRight, RotateCcw, CheckCircle2, AlertTriangle,
    ChevronRight, Brain, Mic, Video, Eye, Activity, Smile, Target,
    MessageSquare, ChevronDown, ChevronUp, Pause, Play, SkipForward,
    Shield, TrendingUp, Gauge, AlertCircle, Info, Zap, Clock,
} from 'lucide-react';
import Section, { SectionDivider } from '../components/Layout/Section';
import ErrorAlert from '../components/UI/ErrorAlert';
import useAssessmentSession from '../hooks/useAssessmentSession';

/* ─── Severity Button Styles ─────────────────────────── */
const SEV = [
    { bg: 'bg-emerald-50 hover:bg-emerald-100 border-emerald-200', text: 'text-emerald-700', ring: 'ring-emerald-300' },
    { bg: 'bg-sky-50 hover:bg-sky-100 border-sky-200', text: 'text-sky-700', ring: 'ring-sky-300' },
    { bg: 'bg-amber-50 hover:bg-amber-100 border-amber-200', text: 'text-amber-700', ring: 'ring-amber-300' },
    { bg: 'bg-orange-50 hover:bg-orange-100 border-orange-200', text: 'text-orange-700', ring: 'ring-orange-300' },
    { bg: 'bg-rose-50 hover:bg-rose-100 border-rose-200', text: 'text-rose-700', ring: 'ring-rose-300' },
];

/* ─── Risk Band Styles ─────────────────────────────── */
const RISK = {
    Low: { bg: 'bg-emerald-100', text: 'text-emerald-700', border: 'border-emerald-300', icon: Shield },
    Moderate: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300', icon: AlertTriangle },
    High: { bg: 'bg-rose-100', text: 'text-rose-700', border: 'border-rose-300', icon: AlertCircle },
};

/* ─── Mini Metric Chip ─────────────────────────────── */
function MetricChip({ icon: Icon, label, value, unit = '', color = 'text-primary' }) {
    return (
        <div className="flex items-center gap-1.5 bg-white/80 backdrop-blur-sm border border-clinical-border
                        rounded-lg px-2.5 py-1.5 text-[10px]">
            <Icon size={11} className={color} />
            <span className="text-clinical-muted font-medium">{label}</span>
            <span className="font-bold text-clinical-text">
                {typeof value === 'number' ? value.toFixed(2) : '—'}{unit}
            </span>
        </div>
    );
}

/* ─── Transition Screen (between questions) ──────── */
function TransitionMetrics({ metrics, onContinue }) {
    useEffect(() => {
        const timer = setTimeout(onContinue, 2500);
        return () => clearTimeout(timer);
    }, [onContinue]);

    if (!metrics) return null;
    return (
        <div className="max-w-md mx-auto text-center py-8 animate-fade-in space-y-5">
            <div className="flex items-center justify-center gap-2">
                <Gauge size={18} className="text-primary" />
                <span className="text-sm font-semibold text-clinical-text">Response Captured</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
                <div className="card-clinical p-3">
                    <p className="text-[10px] text-clinical-muted uppercase tracking-wide mb-1">Confidence</p>
                    <p className="text-xl font-bold text-primary">
                        {(metrics.confidence_proxy * 100).toFixed(0)}%
                    </p>
                </div>
                <div className="card-clinical p-3">
                    <p className="text-[10px] text-clinical-muted uppercase tracking-wide mb-1">Hesitations</p>
                    <p className="text-xl font-bold text-amber-600">{metrics.hesitation_count}</p>
                </div>
                <div className="card-clinical p-3">
                    <p className="text-[10px] text-clinical-muted uppercase tracking-wide mb-1">Facial Stability</p>
                    <p className="text-xl font-bold text-indigo-600">
                        {(metrics.facial_stability * 100).toFixed(0)}%
                    </p>
                </div>
                <div className="card-clinical p-3">
                    <p className="text-[10px] text-clinical-muted uppercase tracking-wide mb-1">Intensity</p>
                    <p className="text-xl font-bold text-rose-500">
                        {(metrics.emotional_intensity * 100).toFixed(0)}%
                    </p>
                </div>
            </div>
            <div className="flex justify-center gap-4 text-[10px] text-clinical-muted">
                <span>Words: <strong>{metrics.total_words}</strong></span>
                <span>Rate: <strong>{metrics.avg_speech_rate?.toFixed(0)}</strong> wpm</span>
                <span>Blink: <strong>{metrics.blink_rate?.toFixed(0)}</strong>/min</span>
            </div>
            <p className="text-[10px] text-clinical-muted animate-pulse">Loading next question…</p>
        </div>
    );
}

/* ─── Domain Result Card ─────────────────────────────── */
function DomainCard({ domain, expanded, onToggle }) {
    const exceeded = domain.threshold_exceeded;
    return (
        <div className={`card-clinical border-l-4 overflow-hidden transition-all duration-200
            ${exceeded ? 'border-l-rose-400 bg-rose-50/30' : 'border-l-emerald-400 bg-emerald-50/20'}`}>
            <button onClick={onToggle} className="w-full p-4 flex items-center justify-between text-left">
                <div className="flex items-center gap-2">
                    {exceeded
                        ? <AlertTriangle size={14} className="text-rose-500" />
                        : <CheckCircle2 size={14} className="text-emerald-500" />}
                    <span className="text-sm font-semibold text-clinical-text">{domain.domain_label}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${exceeded
                        ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                        {exceeded ? 'Threshold Exceeded' : 'Below Threshold'}
                    </span>
                </div>
                <div className="flex items-center gap-3 text-xs text-clinical-muted">
                    <span>Score: <strong>{domain.highest_score}</strong>/4</span>
                    <span>BII: <strong>{domain.behavioral_intensity_index?.toFixed(2)}</strong></span>
                    {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>
            </button>
            {expanded && (
                <div className="px-4 pb-4 space-y-3 animate-slide-down">
                    {/* Domain behavioral metrics */}
                    <div className="grid grid-cols-4 gap-2 text-[10px]">
                        <div className="bg-white rounded-lg p-2 text-center border border-clinical-border">
                            <p className="text-clinical-muted">Confidence</p>
                            <p className="font-bold text-primary">{(domain.avg_confidence_proxy * 100).toFixed(0)}%</p>
                        </div>
                        <div className="bg-white rounded-lg p-2 text-center border border-clinical-border">
                            <p className="text-clinical-muted">Val</p>
                            <p className="font-bold">{domain.avg_valence?.toFixed(2)}</p>
                        </div>
                        <div className="bg-white rounded-lg p-2 text-center border border-clinical-border">
                            <p className="text-clinical-muted">Stability</p>
                            <p className="font-bold">{(domain.avg_facial_stability * 100).toFixed(0)}%</p>
                        </div>
                        <div className="bg-white rounded-lg p-2 text-center border border-clinical-border">
                            <p className="text-clinical-muted">Hes Ratio</p>
                            <p className="font-bold">{(domain.avg_hesitation_ratio * 100).toFixed(1)}%</p>
                        </div>
                    </div>
                    <p className="text-xs italic text-clinical-muted">{domain.recommendation}</p>
                    {domain.questions?.map((q) => (
                        <div key={q.question_id} className="bg-white rounded-lg p-3 border border-clinical-border text-xs">
                            <p className="font-medium text-clinical-text mb-2">"{q.text}"</p>
                            <div className="grid grid-cols-3 gap-2 text-clinical-muted">
                                <span>Score: <strong className="text-clinical-text">{q.self_report_score}</strong>/4</span>
                                <span>Conf: <strong className="text-clinical-text">{(q.confidence_proxy * 100).toFixed(0)}%</strong></span>
                                <span>Words: <strong className="text-clinical-text">{q.audio?.total_words ?? 0}</strong></span>
                                <span>Hes: <strong className="text-clinical-text">{q.audio?.hesitation_count ?? 0}</strong></span>
                                <span>Stability: <strong className="text-clinical-text">{((q.vision?.facial_stability ?? 0) * 100).toFixed(0)}%</strong></span>
                                <span>Intensity: <strong className="text-clinical-text">{((q.vision?.emotional_intensity ?? 0) * 100).toFixed(0)}%</strong></span>
                            </div>
                            {q.transcript && (
                                <p className="mt-2 text-[10px] text-clinical-muted italic truncate">"{q.transcript}"</p>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

/* ─── Main Assessment Panel ──────────────────────────── */
export default function AssessmentPanel() {
    const {
        startAssessment, submitAnswer, pauseSession, resumeSession,
        skipQuestion, stopAssessment,
        isConnected, isPaused, currentQuestion, questionMetrics, results,
        faceData, audioFeatures, transcripts,
        error, submitting, mediaStream,
    } = useAssessmentSession();

    /* ── Callback ref: attach media stream to <video> whenever it mounts ── */
    const mediaStreamRef = useRef(mediaStream);
    mediaStreamRef.current = mediaStream;

    const videoRefCallback = useCallback((el) => {
        if (el && mediaStreamRef.current) {
            el.srcObject = mediaStreamRef.current;
            el.play().catch(() => { });
        }
    }, []);

    /* Re-attach stream when mediaStream changes and video is already mounted */
    const videoElRef = useRef(null);
    const combinedVideoRef = useCallback((el) => {
        videoElRef.current = el;
        videoRefCallback(el);
    }, [videoRefCallback]);

    useEffect(() => {
        if (videoElRef.current && mediaStream) {
            videoElRef.current.srcObject = mediaStream;
            videoElRef.current.play().catch(() => { });
        }
    }, [mediaStream]);

    const [expandedDomain, setExpandedDomain] = useState(null);
    const [showTransition, setShowTransition] = useState(false);
    const [lastMetrics, setLastMetrics] = useState(null);

    // When question_metrics arrives → show transition screen briefly
    useEffect(() => {
        if (questionMetrics && !results) {
            setLastMetrics(questionMetrics);
            setShowTransition(true);
        }
    }, [questionMetrics, results]);

    const handleTransitionDone = useCallback(() => {
        setShowTransition(false);
        setLastMetrics(null);
    }, []);

    const handleStart = useCallback(async () => {
        await startAssessment();
    }, [startAssessment]);

    const handleRestart = useCallback(() => {
        stopAssessment();
        setExpandedDomain(null);
        setShowTransition(false);
        setLastMetrics(null);
    }, [stopAssessment]);

    const progress = currentQuestion
        ? ((currentQuestion.question_number - 1) / currentQuestion.total_questions) * 100
        : results ? 100 : 0;

    const isActive = isConnected && currentQuestion && !results && !showTransition;

    return (
        <div className="animate-fade-in -mx-8 -mt-10" role="region" aria-label="Structured Assessment">

            {/* ── Header ── */}
            <Section bg="sage" gradient>
                <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                            <Stethoscope size={20} className="text-primary" />
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold text-clinical-text">
                                Structured Assessment
                            </h2>
                            <p className="text-xs text-clinical-muted mt-0.5">
                                DSM-5 Cross-Cutting · 23 questions · Live audio + facial capture
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {isActive && !isPaused && (
                            <button onClick={pauseSession}
                                className="btn-secondary text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                                id="pause-assess">
                                <Pause size={12} /> Pause
                            </button>
                        )}
                        {isActive && isPaused && (
                            <button onClick={resumeSession}
                                className="btn-primary text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                                id="resume-assess">
                                <Play size={12} /> Resume
                            </button>
                        )}
                        {isActive && (
                            <button onClick={skipQuestion}
                                className="btn-secondary text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                                id="skip-assess">
                                <SkipForward size={12} /> Skip
                            </button>
                        )}
                        {(isConnected || results) && (
                            <button onClick={handleRestart}
                                className="btn-secondary text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                                id="restart-assess">
                                <RotateCcw size={12} /> Restart
                            </button>
                        )}
                    </div>
                </div>
                {(isConnected || results) && (
                    <div className="mt-4">
                        <div className="flex justify-between text-[10px] text-clinical-muted mb-1.5">
                            <span>Progress {isPaused && '(Paused)'}</span>
                            <span>{currentQuestion
                                ? `${currentQuestion.question_number} / ${currentQuestion.total_questions}`
                                : 'Complete'}</span>
                        </div>
                        <div className="h-2 bg-white/80 rounded-full overflow-hidden border border-clinical-border">
                            <div className={`h-full rounded-full transition-all duration-500 ease-out
                                ${isPaused ? 'bg-amber-400' : 'bg-primary'}`}
                                style={{ width: `${progress}%` }} />
                        </div>
                    </div>
                )}
            </Section>

            {
                error && (
                    <Section bg="white" padded>
                        <ErrorAlert message={error} onDismiss={() => { }} />
                    </Section>
                )
            }

            {/* ── Welcome Screen ── */}
            {
                !isConnected && !results && (
                    <Section bg="white">
                        <div className="max-w-lg mx-auto text-center py-12 space-y-6">
                            <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto">
                                <Stethoscope size={28} className="text-primary" />
                            </div>
                            <h3 className="text-lg font-semibold text-clinical-text">
                                Multimodal Structured Assessment
                            </h3>
                            <p className="text-sm text-clinical-muted leading-relaxed">
                                Each of the 23 questions will be presented one at a time. While the patient
                                responds, <strong>live audio and facial expression capture</strong> will run
                                simultaneously. After the response, select the severity rating to advance.
                            </p>
                            <div className="flex justify-center gap-3 text-[10px] text-clinical-muted">
                                <span className="flex items-center gap-1"><Mic size={12} /> Speech capture</span>
                                <span className="flex items-center gap-1"><Video size={12} /> Facial analysis</span>
                                <span className="flex items-center gap-1"><Brain size={12} /> NLP processing</span>
                            </div>
                            <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-left">
                                <p className="text-xs text-amber-700 leading-relaxed">
                                    <strong>Note:</strong> Camera and microphone access are required.
                                    This is a decision-support tool only — it does not generate diagnoses.
                                </p>
                            </div>
                            <button onClick={handleStart}
                                className="btn-primary px-8 py-3 rounded-xl inline-flex items-center gap-2 text-sm font-semibold shadow-float"
                                id="start-assessment">
                                Start Assessment <ArrowRight size={16} />
                            </button>
                        </div>
                    </Section>
                )
            }

            {/* ── Transition Screen (between questions) ── */}
            {
                showTransition && !results && (
                    <Section bg="white">
                        <TransitionMetrics metrics={lastMetrics} onContinue={handleTransitionDone} />
                    </Section>
                )
            }

            {/* ── Active Question (split layout) ── */}
            {
                isActive && (
                    <Section bg="white">
                        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 py-4">

                            {/* Left: Question + Buttons (3 cols) */}
                            <div className="lg:col-span-3 space-y-5">
                                <div className="flex items-center gap-2">
                                    <Brain size={14} className="text-primary" />
                                    <span className="text-[10px] font-semibold text-primary uppercase tracking-wide">
                                        {currentQuestion.domain_label}
                                    </span>
                                    <span className="text-[10px] text-clinical-muted">
                                        — Q{currentQuestion.question_number} of {currentQuestion.total_questions}
                                    </span>
                                </div>

                                <div className="card-clinical p-5 bg-white">
                                    <p className="text-xs text-clinical-muted mb-2">
                                        During the past <strong>TWO (2) WEEKS</strong>, how much have you been bothered by:
                                    </p>
                                    <p className="text-base font-semibold text-clinical-text leading-relaxed">
                                        "{currentQuestion.text}"
                                    </p>
                                </div>

                                {isPaused && (
                                    <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-center gap-2">
                                        <Pause size={14} className="text-amber-600" />
                                        <span className="text-xs text-amber-700 font-medium">
                                            Session paused — audio/video capture suspended
                                        </span>
                                    </div>
                                )}

                                {transcripts.length > 0 && (
                                    <div className="bg-slate-50 rounded-xl p-3 border border-clinical-border">
                                        <div className="flex items-center gap-1.5 mb-1.5">
                                            <MessageSquare size={11} className="text-primary" />
                                            <span className="text-[10px] font-semibold text-clinical-muted">Live Transcript</span>
                                        </div>
                                        <p className="text-xs text-clinical-text leading-relaxed">
                                            {transcripts.join(' ')}
                                        </p>
                                    </div>
                                )}

                                <div className="space-y-2">
                                    <p className="text-[10px] font-semibold text-clinical-muted uppercase tracking-widest">
                                        Rate severity
                                    </p>
                                    {(currentQuestion.response_options || []).map((opt) => {
                                        const s = SEV[opt.value] || SEV[0];
                                        return (
                                            <button key={opt.value}
                                                onClick={() => submitAnswer(opt.value)}
                                                disabled={submitting || isPaused}
                                                className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border
                                                transition-all duration-150 ${s.bg} ${s.text}
                                                focus:outline-none focus:ring-2 ${s.ring}
                                                disabled:opacity-50 disabled:pointer-events-none`}
                                                id={`assess-response-${opt.value}`}>
                                                <div className="flex items-center gap-3">
                                                    <span className="w-6 h-6 rounded-lg bg-white/80 flex items-center justify-center
                                                    text-xs font-bold shadow-sm border border-black/5">{opt.value}</span>
                                                    <span className="text-sm font-semibold">{opt.label}</span>
                                                </div>
                                                <ChevronRight size={14} className="opacity-40" />
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Right: Live webcam + metrics (2 cols) */}
                            <div className="lg:col-span-2 space-y-4">
                                <div className="relative rounded-xl overflow-hidden bg-slate-900 aspect-video">
                                    <video ref={combinedVideoRef} autoPlay muted playsInline
                                        className="w-full h-full object-cover"
                                        style={{ transform: 'scaleX(-1)' }} />
                                    <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/50
                                    backdrop-blur-sm px-2 py-1 rounded-full">
                                        <span className={`w-2 h-2 rounded-full ${isPaused
                                            ? 'bg-amber-400' : 'bg-red-500 animate-pulse'}`} />
                                        <span className="text-[9px] font-mono text-white">
                                            {isPaused ? 'PAUSED' : 'LIVE'}
                                        </span>
                                    </div>
                                    <div className="absolute bottom-2 left-2 right-2">
                                        <span className={`text-[9px] font-semibold px-2 py-0.5 rounded-full ${faceData?.face_detected
                                            ? 'bg-emerald-500/80 text-white'
                                            : 'bg-red-500/80 text-white'
                                            }`}>
                                            {faceData?.face_detected ? '✓ Face' : '✗ No Face'}
                                        </span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-2">
                                    <MetricChip icon={Smile} label="Val" value={faceData?.valence} color="text-indigo-500" />
                                    <MetricChip icon={Activity} label="Aro" value={faceData?.arousal} color="text-amber-500" />
                                    <MetricChip icon={Eye} label="Smile" value={faceData?.smile_score} color="text-emerald-500" />
                                    <MetricChip icon={Target} label="Brow" value={faceData?.brow_furrow_score} color="text-rose-400" />
                                </div>

                                {audioFeatures && (
                                    <div className="grid grid-cols-2 gap-2">
                                        <MetricChip icon={Mic} label="Rate"
                                            value={audioFeatures.speech_rate_wpm} color="text-blue-500" />
                                        <MetricChip icon={Zap} label="Hes"
                                            value={audioFeatures.hesitation_count} color="text-orange-500" />
                                    </div>
                                )}
                            </div>
                        </div>
                    </Section>
                )
            }

            {/* ── Results with Report ── */}
            {
                results && (
                    <>
                        <Section bg="white">
                            <div className="max-w-2xl mx-auto space-y-5">
                                <div className="text-center space-y-2">
                                    <CheckCircle2 size={32} className="text-emerald-500 mx-auto" />
                                    <h3 className="text-lg font-semibold text-clinical-text">Assessment Complete</h3>
                                    <p className="text-sm text-clinical-muted">
                                        {results.total_answered} of {results.total_questions} questions ·
                                        {' '}{Math.round(results.duration_seconds)}s total
                                    </p>
                                </div>

                                {/* Risk Band + Confidence */}
                                <div className="grid grid-cols-2 gap-4">
                                    {(() => {
                                        const r = RISK[results.risk_band] || RISK.Low;
                                        const RIcon = r.icon;
                                        return (
                                            <div className={`rounded-xl px-4 py-4 border ${r.bg} ${r.border} text-center`}>
                                                <RIcon size={22} className={`${r.text} mx-auto mb-1`} />
                                                <p className="text-[10px] text-clinical-muted uppercase tracking-wide">Risk Band</p>
                                                <p className={`text-xl font-bold ${r.text}`}>{results.risk_band}</p>
                                            </div>
                                        );
                                    })()}
                                    <div className="rounded-xl px-4 py-4 border bg-blue-50 border-blue-200 text-center">
                                        <Gauge size={22} className="text-blue-600 mx-auto mb-1" />
                                        <p className="text-[10px] text-clinical-muted uppercase tracking-wide">Confidence</p>
                                        <p className="text-xl font-bold text-blue-700">
                                            {(results.confidence_score * 100).toFixed(0)}%
                                        </p>
                                    </div>
                                </div>

                                {/* Escalation */}
                                {results.escalation && (
                                    <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
                                        <div className="flex items-center gap-2 mb-1">
                                            <AlertCircle size={14} className="text-rose-600" />
                                            <span className="text-sm font-bold text-rose-700">Escalation</span>
                                        </div>
                                        <p className="text-xs text-rose-600">{results.escalation}</p>
                                    </div>
                                )}

                                {/* Flagged domains */}
                                {results.flagged_domains?.length > 0 ? (
                                    <div className="bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
                                        <div className="flex items-center gap-2 mb-1">
                                            <AlertTriangle size={14} className="text-rose-500" />
                                            <span className="text-sm font-semibold text-rose-700">
                                                {results.flagged_domains.length} domain{results.flagged_domains.length !== 1 ? 's' : ''} exceeded threshold
                                            </span>
                                        </div>
                                        <p className="text-xs text-rose-600">
                                            {results.flagged_domains.join(', ')}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <CheckCircle2 size={14} className="text-emerald-500" />
                                            <span className="text-sm font-semibold text-emerald-700">
                                                No domains exceeded threshold
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Behavioral Summary */}
                                {results.behavioral_summary?.length > 0 && (
                                    <div className="bg-slate-50 border border-clinical-border rounded-xl px-4 py-3">
                                        <div className="flex items-center gap-2 mb-2">
                                            <TrendingUp size={14} className="text-primary" />
                                            <span className="text-sm font-semibold text-clinical-text">
                                                Behavioral Observations
                                            </span>
                                        </div>
                                        <ul className="space-y-1">
                                            {results.behavioral_summary.map((obs, i) => (
                                                <li key={i} className="text-xs text-clinical-muted flex items-start gap-1.5">
                                                    <span className="mt-1 w-1 h-1 rounded-full bg-primary shrink-0" />
                                                    {obs}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Explainability */}
                                <div className="flex items-start gap-2 text-[10px] text-clinical-muted bg-blue-50 border border-blue-100 rounded-xl px-3 py-2">
                                    <Info size={12} className="text-blue-400 shrink-0 mt-0.5" />
                                    <p>{results.explainability_note}</p>
                                </div>
                            </div>
                        </Section>

                        <SectionDivider variant="fade" />

                        <Section bg="sage">
                            <div className="max-w-2xl mx-auto space-y-3">
                                <p className="text-[10px] font-semibold text-clinical-muted uppercase tracking-widest mb-2">
                                    Domain Results — click to expand
                                </p>
                                {results.domains?.map((d) => (
                                    <DomainCard key={d.domain} domain={d}
                                        expanded={expandedDomain === d.domain}
                                        onToggle={() => setExpandedDomain(
                                            expandedDomain === d.domain ? null : d.domain
                                        )} />
                                ))}
                            </div>
                        </Section>
                    </>
                )
            }
        </div >
    );
}
