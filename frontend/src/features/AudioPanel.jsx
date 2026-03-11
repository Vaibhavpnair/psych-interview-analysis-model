import React, { useState, useEffect, useCallback } from 'react';
import { Mic, Upload, Clock, BarChart3, Pause, Gauge, Volume2, Square, AlertTriangle, Zap, Timer, Hash, ShieldCheck, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';

// Barrel imports
import { Card, SkeletonMetricGrid, CollapsibleSection, RiskBand, getRiskLevel, SectionGroup, ErrorAlert } from '../components/UI';
import { AnimatedBar, AnimatedNumber } from '../components/UI';
import { Section, SectionDivider } from '../components/Layout';

// Centralized API service
import { analyzeAudio } from '../services/api';

// Live mic hook
import useMicCapture from '../hooks/useMicCapture';

/* ───────────────────── Helpers ───────────────────── */

function formatTimer(seconds) {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

/** Classify a value into low / moderate / high for a given threshold set */
function classifyLevel(value, { low, moderate }) {
    if (value <= low) return 'low';
    if (value <= moderate) return 'moderate';
    return 'high';
}

const LEVEL_STYLES = {
    low: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', label: 'Low' },
    moderate: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', label: 'Moderate' },
    high: { bg: 'bg-rose-50', text: 'text-rose-700', dot: 'bg-rose-500', label: 'High' },
    normal: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', label: 'Normal' },
};

/* ───────────────────── EnhancedMetricCard ─────────── */

function EnhancedMetricCard({ icon: Icon, label, value, unit, color = 'text-primary', hint, level, barPercent, barColor }) {
    const ls = level ? LEVEL_STYLES[level] : null;
    return (
        <div className="metric-card animate-slide-up" role="group" aria-label={`${label}: ${value} ${unit || ''}`}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Icon size={14} className={color} aria-hidden="true" />
                    <span className="text-xs font-medium text-clinical-muted uppercase tracking-wide">{label}</span>
                </div>
                {ls && (
                    <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full ${ls.bg} ${ls.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${ls.dot}`} />
                        {ls.label}
                    </span>
                )}
            </div>
            <div className="flex items-baseline gap-1">
                <AnimatedNumber value={value} className="text-2xl font-semibold text-clinical-text" />
                {unit && <span className="text-xs text-clinical-muted">{unit}</span>}
            </div>
            {typeof barPercent === 'number' && (
                <AnimatedBar
                    percentage={Math.max(2, Math.min(100, barPercent))}
                    color={barColor || 'bg-primary'}
                    height="h-1.5"
                    className="mt-2"
                    label={label}
                />
            )}
            {hint && <p className="text-[10px] text-clinical-muted mt-1.5 leading-relaxed">{hint}</p>}
        </div>
    );
}

/* ───────────────────── ResponseHistoryItem ─────────── */

function ResponseHistoryItem({ response, index }) {
    const [expanded, setExpanded] = useState(false);
    const f = response.features;

    return (
        <div className="card-clinical p-4">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between text-left"
            >
                <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary-50 text-primary text-xs font-semibold flex items-center justify-center">
                        {index + 1}
                    </span>
                    <div>
                        <span className="text-sm font-medium text-clinical-text">
                            Response #{index + 1}
                        </span>
                        <span className="text-[10px] text-clinical-muted ml-2">
                            {f.word_count} words · {f.speech_rate_wpm?.toFixed(0)} WPM · {response.processing_time?.toFixed(1)}s
                        </span>
                    </div>
                </div>
                {expanded ? <ChevronUp size={14} className="text-clinical-muted" /> : <ChevronDown size={14} className="text-clinical-muted" />}
            </button>

            {expanded && (
                <div className="grid grid-cols-3 gap-3 mt-3 pt-3 border-t border-clinical-border">
                    <div className="text-center">
                        <span className="text-[10px] text-clinical-muted uppercase">Speech Rate</span>
                        <p className="text-sm font-semibold text-clinical-text">{f.speech_rate_wpm?.toFixed(0)} WPM</p>
                    </div>
                    <div className="text-center">
                        <span className="text-[10px] text-clinical-muted uppercase">Pauses</span>
                        <p className="text-sm font-semibold text-clinical-text">{f.pause_count}</p>
                    </div>
                    <div className="text-center">
                        <span className="text-[10px] text-clinical-muted uppercase">Tension</span>
                        <p className="text-sm font-semibold text-clinical-text">{f.tension_index?.toFixed(2)}</p>
                    </div>
                    <div className="text-center">
                        <span className="text-[10px] text-clinical-muted uppercase">Hesitations</span>
                        <p className="text-sm font-semibold text-clinical-text">{f.hesitation_markers}</p>
                    </div>
                    <div className="text-center">
                        <span className="text-[10px] text-clinical-muted uppercase">Confidence</span>
                        <p className="text-sm font-semibold text-clinical-text">{(f.confidence_level * 100)?.toFixed(0)}%</p>
                    </div>
                    <div className="text-center">
                        <span className="text-[10px] text-clinical-muted uppercase">Delay</span>
                        <p className="text-sm font-semibold text-clinical-text">{f.response_delay?.toFixed(1)}s</p>
                    </div>
                </div>
            )}
        </div>
    );
}

/* ───────────────────── AudioPanel ─────────────────── */

export default function AudioPanel() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [fileName, setFileName] = useState('');
    const [responseHistory, setResponseHistory] = useState([]);
    const [responseCount, setResponseCount] = useState(0);

    const {
        startRecording, stopRecording, isRecording,
        audioBlob, error: micError, elapsed
    } = useMicCapture();

    // Surface mic errors
    useEffect(() => {
        if (micError) setError(micError);
    }, [micError]);

    // Handle successful result — push to history
    const handleResult = useCallback((data) => {
        setResult(data);
        setResponseHistory(prev => [data, ...prev]);
        setResponseCount(prev => prev + 1);
    }, []);

    // When audio blob is ready, send to backend
    useEffect(() => {
        if (!audioBlob) return;
        const sendBlob = async () => {
            setLoading(true);
            setError(null);
            setResult(null);
            setFileName('');

            try {
                const file = new File([audioBlob], `mic_${Date.now()}.webm`, { type: audioBlob.type });
                const data = await analyzeAudio(file);
                handleResult(data);
            } catch (err) {
                setError(err.message + ': ' + (err.response?.data?.detail || 'Backend unavailable'));
            } finally {
                setLoading(false);
            }
        };
        sendBlob();
    }, [audioBlob, handleResult]);

    const handleUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        setFileName(file.name);
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const data = await analyzeAudio(file);
            handleResult(data);
        } catch (err) {
            setError(err.message + ': ' + (err.response?.data?.detail || 'Backend unavailable'));
        } finally {
            setLoading(false);
        }
    };

    const handleStartRecording = async () => {
        setResult(null);
        setError(null);
        setFileName('');
        await startRecording();
    };

    const handleNewResponse = () => {
        setResult(null);
        setError(null);
        setFileName('');
    };

    // Derived levels
    const f = result?.features;
    const silenceRisk = f ? getRiskLevel(f.silence_ratio, { low: 0.2, moderate: 0.4, high: 0.6 }) : null;
    const speechRateLevel = f ? classifyLevel(Math.abs(f.speech_rate_wpm - 135), { low: 30, moderate: 60 }) : null;
    const pauseLevel = f ? classifyLevel(f.pause_rate, { low: 5, moderate: 12 }) : null;
    const tensionLevel = f ? classifyLevel(f.tension_index, { low: 2.5, moderate: 5 }) : null;
    const hesitationLevel = f ? classifyLevel(f.hesitation_markers, { low: 2, moderate: 5 }) : null;

    const isDisabled = loading || isRecording;

    return (
        <div className="animate-fade-in -mx-8 -mt-10" role="region" aria-label="Speech Prosody Analysis">

            {/* ─── SECTION 1: Header + Upload + Live Mic ─── */}
            <Section bg="cream" gradient>
                <div className="flex items-center justify-between mb-1">
                    <h2 className="text-xl font-semibold text-clinical-text">Speech Prosody Analysis</h2>
                    {responseCount > 0 && (
                        <span className="text-[10px] font-mono text-clinical-muted bg-white px-2 py-0.5 rounded-full border border-clinical-border">
                            {responseCount} response{responseCount !== 1 ? 's' : ''} analyzed
                        </span>
                    )}
                </div>
                <p className="text-sm text-clinical-muted mt-1 mb-6">
                    Analyze pitch, speech rate, pause patterns, and hesitation markers per patient response.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* File upload zone */}
                    <label
                        className={`upload-zone block ${isDisabled ? 'opacity-50 pointer-events-none' : ''}`}
                        role="button" tabIndex={0} aria-label="Upload audio file"
                    >
                        <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mb-2">
                            <Mic size={24} className="text-primary" aria-hidden="true" />
                        </div>
                        <p className="text-sm font-medium text-clinical-text">
                            {fileName || 'Drop audio file here or click to browse'}
                        </p>
                        <p className="text-xs text-clinical-muted">Supports .wav, .mp3, .m4a — max 50MB</p>
                        <input
                            type="file"
                            className="hidden"
                            accept="audio/*"
                            onChange={handleUpload}
                            disabled={isDisabled}
                            aria-label="Select audio file"
                        />
                        {!fileName && (
                            <span className="mt-3 btn-secondary text-xs px-4 py-1.5 rounded-md inline-flex items-center gap-1.5">
                                <Upload size={12} aria-hidden="true" />
                                Select File
                            </span>
                        )}
                    </label>

                    {/* Live recording zone */}
                    <div className="upload-zone bg-white flex flex-col items-center justify-center relative"
                        style={{ minHeight: '200px' }}>

                        {!isRecording && (
                            <>
                                <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mb-2">
                                    <Mic size={24} className="text-primary" aria-hidden="true" />
                                </div>
                                <p className="text-sm font-medium text-clinical-text">Live Microphone</p>
                                <p className="text-xs text-clinical-muted">Record a patient response for analysis</p>
                                <button
                                    onClick={handleStartRecording}
                                    disabled={loading}
                                    className="mt-3 btn-primary text-xs px-5 py-2 rounded-lg inline-flex items-center gap-1.5"
                                    id="start-recording"
                                >
                                    <Mic size={12} />
                                    Start Recording
                                </button>
                            </>
                        )}

                        {isRecording && (
                            <div className="flex flex-col items-center gap-3">
                                <div className="relative">
                                    <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center">
                                        <Mic size={28} className="text-red-500" />
                                    </div>
                                    <span className="absolute inset-0 rounded-full border-2 border-red-400 animate-ping opacity-30" />
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                                    <span className="text-xs font-mono font-medium text-clinical-text">
                                        REC {formatTimer(elapsed)}
                                    </span>
                                </div>
                                <button
                                    onClick={stopRecording}
                                    className="bg-red-500 hover:bg-red-600 text-white text-xs px-5 py-2 rounded-lg inline-flex items-center gap-1.5 shadow-float transition-all duration-150"
                                    id="stop-recording"
                                >
                                    <Square size={12} fill="currentColor" />
                                    Stop &amp; Analyze
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </Section>

            {/* Error */}
            {error && (
                <Section bg="white">
                    <ErrorAlert message={error} onDismiss={() => setError(null)} />
                </Section>
            )}

            {/* Loading skeleton */}
            {loading && (
                <Section bg="white" aria-live="polite">
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 pb-3">
                            <div className="w-4 h-4 rounded bg-clinical-border/50 animate-pulse" />
                            <div className="h-3 w-28 rounded bg-clinical-border/60 animate-pulse" />
                        </div>
                        <SkeletonMetricGrid count={6} />
                    </div>
                </Section>
            )}

            {/* ─── RESULTS: Current Response ─── */}
            {result && (
                <>
                    {/* Header bar for current result */}
                    <Section bg="white">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <span className="w-7 h-7 rounded-full bg-primary text-white text-xs font-semibold flex items-center justify-center">
                                    {responseCount}
                                </span>
                                <div>
                                    <h3 className="text-sm font-semibold text-clinical-text">Response #{responseCount}</h3>
                                    <span className="text-[10px] text-clinical-muted font-mono">
                                        Processed in {result.processing_time?.toFixed(2)}s
                                    </span>
                                </div>
                            </div>
                            <button
                                onClick={handleNewResponse}
                                className="btn-secondary text-xs px-3 py-1.5 rounded-lg inline-flex items-center gap-1.5"
                            >
                                <RotateCcw size={12} />
                                Next Response
                            </button>
                        </div>

                        {/* Risk band */}
                        <div className="space-y-5 animate-slide-up">
                            {silenceRisk && (
                                <RiskBand
                                    level={silenceRisk}
                                    label={`Speech Pattern: ${silenceRisk === 'low' ? 'Normal Range' : silenceRisk === 'moderate' ? 'Elevated Silence' : 'High Silence Ratio'}`}
                                />
                            )}

                            {/* Key metrics with level indicators + mini bars */}
                            <SectionGroup label="Core Speech Metrics">
                                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                                    <EnhancedMetricCard
                                        icon={Volume2} label="Speech Rate"
                                        value={f.speech_rate_wpm?.toFixed(0)} unit="WPM"
                                        color="text-accent"
                                        level={speechRateLevel}
                                        barPercent={(f.speech_rate_wpm / 200) * 100}
                                        barColor="bg-accent"
                                        hint="120–150 WPM typical conversational range"
                                    />
                                    <EnhancedMetricCard
                                        icon={Gauge} label="Mean Pitch"
                                        value={f.pitch_mean?.toFixed(1)} unit="Hz"
                                        color="text-primary"
                                        barPercent={Math.min(100, (f.pitch_mean / 300) * 100)}
                                        barColor="bg-primary"
                                        hint="Fundamental frequency of voice"
                                    />
                                    <EnhancedMetricCard
                                        icon={BarChart3} label="Pitch Variance"
                                        value={f.pitch_std?.toFixed(1)} unit="Hz σ"
                                        color="text-secondary"
                                        barPercent={Math.min(100, (f.pitch_std / 80) * 100)}
                                        barColor="bg-secondary"
                                        hint="Low variability may indicate flat affect"
                                    />
                                    <EnhancedMetricCard
                                        icon={Pause} label="Pause Rate"
                                        value={f.pause_rate?.toFixed(1)} unit="/min"
                                        color="text-violet-500"
                                        level={pauseLevel}
                                        barPercent={(f.pause_rate / 20) * 100}
                                        barColor="bg-violet-400"
                                        hint="Pauses per minute of speech"
                                    />
                                    <EnhancedMetricCard
                                        icon={Clock} label="Silence Ratio"
                                        value={(f.silence_ratio * 100)?.toFixed(1)} unit="%"
                                        color="text-risk-moderate"
                                        level={silenceRisk}
                                        barPercent={f.silence_ratio * 100}
                                        barColor={silenceRisk === 'high' ? 'bg-rose-400' : silenceRisk === 'moderate' ? 'bg-amber-400' : 'bg-emerald-400'}
                                        hint="Above 40% may indicate withdrawal"
                                    />
                                    <EnhancedMetricCard
                                        icon={Hash} label="Word Count"
                                        value={f.word_count ?? 0} unit="words"
                                        color="text-primary"
                                        hint="Total words detected in recording"
                                    />
                                </div>
                            </SectionGroup>
                        </div>
                    </Section>

                    <SectionDivider variant="fade" />

                    {/* ─── Behavioral Indicators ─── */}
                    <Section bg="sage">
                        <SectionGroup label="Behavioral Indicators">
                            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                                <EnhancedMetricCard
                                    icon={AlertTriangle} label="Hesitation Markers"
                                    value={f.hesitation_markers ?? 0} unit="fillers"
                                    color="text-amber-500"
                                    level={hesitationLevel}
                                    barPercent={Math.min(100, (f.hesitation_markers / 10) * 100)}
                                    barColor="bg-amber-400"
                                    hint="Filler words (um, uh, like…)"
                                />
                                <EnhancedMetricCard
                                    icon={Zap} label="Tension Index"
                                    value={f.tension_index?.toFixed(2)}
                                    color="text-rose-500"
                                    level={tensionLevel}
                                    barPercent={Math.min(100, (f.tension_index / 8) * 100)}
                                    barColor={tensionLevel === 'high' ? 'bg-rose-400' : tensionLevel === 'moderate' ? 'bg-amber-400' : 'bg-emerald-400'}
                                    hint="Pitch + variability composite — higher = more tension"
                                />
                                <EnhancedMetricCard
                                    icon={ShieldCheck} label="Confidence"
                                    value={(f.confidence_level * 100)?.toFixed(1)} unit="%"
                                    color="text-emerald-600"
                                    barPercent={f.confidence_level * 100}
                                    barColor="bg-emerald-400"
                                    hint="Average transcription confidence"
                                />
                                <EnhancedMetricCard
                                    icon={Timer} label="Response Delay"
                                    value={f.response_delay?.toFixed(2)} unit="sec"
                                    color="text-sky-500"
                                    barPercent={Math.min(100, (f.response_delay / 5) * 100)}
                                    barColor="bg-sky-400"
                                    hint="Time to first speech onset"
                                />
                            </div>
                        </SectionGroup>
                    </Section>

                    {/* ─── Transcript Segments ─── */}
                    {result.segments && result.segments.length > 0 && (
                        <>
                            <SectionDivider variant="fade" />
                            <Section bg="teal">
                                <CollapsibleSection
                                    title="Transcript Segments"
                                    subtitle={`${result.segments.length} segments detected`}
                                    icon={Mic}
                                >
                                    <div className="space-y-3 max-h-64 overflow-y-auto mt-3">
                                        {result.segments.map((seg, i) => (
                                            <div key={i} className="flex gap-3 text-sm p-3 bg-white rounded-lg">
                                                <span className="text-[10px] font-mono text-clinical-muted whitespace-nowrap mt-1">
                                                    {seg.start_time?.toFixed(1)}s
                                                </span>
                                                <p className="text-clinical-text leading-relaxed">{seg.transcript}</p>
                                            </div>
                                        ))}
                                    </div>
                                </CollapsibleSection>
                            </Section>
                        </>
                    )}
                </>
            )}

            {/* ─── Response History ─── */}
            {responseHistory.length > 1 && (
                <>
                    <SectionDivider variant="fade" />
                    <Section bg="stone">
                        <CollapsibleSection
                            title="Response History"
                            subtitle={`${responseHistory.length} responses recorded this session`}
                            icon={Clock}
                        >
                            <div className="space-y-2 mt-3 max-h-72 overflow-y-auto">
                                {responseHistory.map((resp, i) => (
                                    <ResponseHistoryItem
                                        key={`resp-${i}`}
                                        response={resp}
                                        index={responseHistory.length - 1 - i}
                                    />
                                ))}
                            </div>
                        </CollapsibleSection>
                    </Section>
                </>
            )}
        </div>
    );
}
