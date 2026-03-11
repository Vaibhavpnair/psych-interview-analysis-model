import React, { useRef, useEffect } from 'react';
import { useStreamingSession } from '../hooks/useStreamingSession';
import {
    Radio, Square, RotateCcw,
    Mic, Video, Brain, Activity,
    AlertTriangle, Info
} from 'lucide-react';

// ── Gauge Component ─────────────────────────────────────────
function Gauge({ label, value, min = -1, max = 1, color = '#6366f1' }) {
    const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
    return (
        <div className="space-y-1">
            <div className="flex justify-between text-xs">
                <span className="text-slate-400">{label}</span>
                <span className="font-mono text-white">{typeof value === 'number' ? value.toFixed(3) : '—'}</span>
            </div>
            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                />
            </div>
        </div>
    );
}

// ── Metric Card ─────────────────────────────────────────────
function MetricCard({ title, icon: Icon, children }) {
    return (
        <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2">
                <Icon size={16} className="text-primary" />
                <h3 className="text-sm font-semibold text-white">{title}</h3>
            </div>
            {children}
        </div>
    );
}

// ── Main Panel ──────────────────────────────────────────────
export default function LiveSessionPanel() {
    const {
        isConnected,
        isRecording,
        error,
        transcripts,
        audioFeatures,
        audioUpdate,
        faceData,
        nlpResults,
        fusionSummary,
        startSession,
        stopSession,
        resetData,
    } = useStreamingSession();

    const rolling = audioUpdate?.rolling;
    const cumulative = audioUpdate;

    const videoRef = useRef(null);
    const transcriptEndRef = useRef(null);

    // Auto-scroll transcript
    useEffect(() => {
        transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [transcripts]);

    const handleStart = async () => {
        resetData();
        await startSession(videoRef.current);
    };

    const handleStop = () => {
        stopSession();
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
    };

    const latestNlp = nlpResults.length > 0 ? nlpResults[nlpResults.length - 1] : null;

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3" id="live-session-heading">
                        <div className={`w-3 h-3 rounded-full ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-slate-600'}`} />
                        Live Session
                    </h1>
                    <p className="text-sm text-slate-400 mt-1">
                        Real-time multimodal behavioral analysis
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    {!isRecording ? (
                        <button
                            id="start-session-btn"
                            onClick={handleStart}
                            className="flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary/90
                                       text-white text-sm font-medium rounded-xl transition-all duration-200
                                       shadow-lg shadow-primary/25 hover:shadow-primary/40"
                        >
                            <Radio size={16} />
                            Start Session
                        </button>
                    ) : (
                        <button
                            id="stop-session-btn"
                            onClick={handleStop}
                            className="flex items-center gap-2 px-5 py-2.5 bg-red-500/90 hover:bg-red-500
                                       text-white text-sm font-medium rounded-xl transition-all duration-200
                                       shadow-lg shadow-red-500/25"
                        >
                            <Square size={14} />
                            Stop Session
                        </button>
                    )}
                    <button
                        id="reset-session-btn"
                        onClick={() => { handleStop(); resetData(); }}
                        className="p-2.5 bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white
                                   rounded-xl transition-all duration-200"
                        title="Reset"
                    >
                        <RotateCcw size={16} />
                    </button>
                </div>
            </div>

            {/* Disclaimer Banner */}
            <div className="flex items-start gap-3 px-4 py-3 bg-amber-500/5 border border-amber-500/10 rounded-xl">
                <Info size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-amber-200/80 leading-relaxed">
                    This tool provides observational data to support clinical assessment.
                    It does not diagnose any condition. All metrics are behavioral indicators only.
                </p>
            </div>

            {/* Error */}
            {error && (
                <div className="flex items-center gap-3 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <AlertTriangle size={16} className="text-red-400" />
                    <p className="text-sm text-red-300">{error}</p>
                </div>
            )}

            {/* Connection Status */}
            <div className="flex items-center gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-slate-600'}`} />
                    {isConnected ? 'Connected' : 'Disconnected'}
                </span>
                {isRecording && (
                    <>
                        <span>Segments: {transcripts.length}</span>
                        <span>Frames: {faceData?.frame_index ?? 0}</span>
                    </>
                )}
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

                {/* ── Column 1: Video + Audio ──────────── */}
                <div className="space-y-5">

                    {/* Webcam Preview */}
                    <MetricCard title="Video Feed" icon={Video}>
                        <div className="relative aspect-[4/3] bg-black/50 rounded-lg overflow-hidden">
                            <video
                                ref={videoRef}
                                autoPlay
                                muted
                                playsInline
                                className="w-full h-full object-cover"
                                style={{ transform: 'scaleX(-1)' }}
                            />
                            {!isRecording && (
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <p className="text-slate-500 text-sm">Camera preview</p>
                                </div>
                            )}
                        </div>
                    </MetricCard>

                    {/* Face Metrics */}
                    <MetricCard title="Facial Metrics" icon={Video}>
                        <Gauge label="Valence" value={faceData?.valence ?? 0} color="#818cf8" />
                        <Gauge label="Arousal" value={faceData?.arousal ?? 0} min={0} color="#f472b6" />
                        <Gauge label="Smile" value={faceData?.smile_score ?? 0} min={0} color="#34d399" />
                        <Gauge label="Brow Furrow" value={faceData?.brow_furrow_score ?? 0} min={0} color="#fb923c" />
                        <div className="text-[10px] text-slate-600 pt-1">
                            {faceData?.face_detected ? '✓ Face detected' : '✗ No face detected'}
                        </div>
                    </MetricCard>
                </div>

                {/* ── Column 2: Audio + NLP ────────────── */}
                <div className="space-y-5">

                    {/* Audio Metrics */}
                    <MetricCard title="Speech Metrics" icon={Mic}>
                        <Gauge label="Pitch (Hz)" value={audioFeatures?.pitch_mean ?? 0} min={0} max={500} color="#818cf8" />
                        <Gauge label="Pitch Variability" value={audioFeatures?.pitch_std ?? 0} min={0} max={100} color="#a78bfa" />
                        <Gauge label="Energy (RMS)" value={audioFeatures?.energy_rms ?? 0} min={0} max={0.5} color="#f59e0b" />
                        <Gauge label="Energy (dB)" value={audioFeatures?.energy_db ?? -60} min={-60} max={0} color="#eab308" />
                        <Gauge label="Speech Rate (WPM)" value={audioFeatures?.speech_rate_wpm ?? 0} min={0} max={250} color="#34d399" />
                        <Gauge label="Silence Ratio" value={audioFeatures?.silence_ratio ?? 0} min={0} color="#fb923c" />
                        <div className="flex items-center justify-between text-[10px] text-slate-600 pt-1">
                            <span>Pauses: {audioFeatures?.pause_count ?? 0}</span>
                            <span>Words: {audioFeatures?.word_count ?? 0}</span>
                            <span>Chunk: {audioFeatures?.chunk_duration ?? 0}s</span>
                        </div>
                    </MetricCard>

                    {/* Rolling Window Stats */}
                    <MetricCard title="Rolling Window (~10s)" icon={Activity}>
                        {rolling ? (
                            <div className="space-y-2">
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <span className="text-slate-500">Avg Pitch</span>
                                        <p className="text-white font-mono mt-0.5">{rolling.avg_pitch_mean} Hz</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <span className="text-slate-500">Avg Energy</span>
                                        <p className="text-white font-mono mt-0.5">{rolling.avg_energy_db} dB</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <span className="text-slate-500">Avg Rate</span>
                                        <p className="text-white font-mono mt-0.5">{rolling.avg_speech_rate_wpm} WPM</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <span className="text-slate-500">Pauses</span>
                                        <p className="text-white font-mono mt-0.5">{rolling.total_pauses_in_window}</p>
                                    </div>
                                </div>
                                <div className="text-[10px] text-slate-600 border-t border-white/5 pt-1.5">
                                    Window: {rolling.window_duration}s ({rolling.window_chunks} chunks) |
                                    Total: {cumulative?.cumulative_words ?? 0} words, {cumulative?.cumulative_pauses ?? 0} pauses, {cumulative?.cumulative_duration ?? 0}s
                                </div>
                            </div>
                        ) : (
                            <p className="text-xs text-slate-600">Stats appear after first audio chunk...</p>
                        )}
                    </MetricCard>

                    {/* NLP / Sentiment */}
                    <MetricCard title="Linguistic Analysis" icon={Brain}>
                        {latestNlp ? (
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="text-xs text-slate-400">Sentiment</span>
                                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${latestNlp.sentiment.label === 'positive' ? 'bg-emerald-500/20 text-emerald-300' :
                                        latestNlp.sentiment.label === 'negative' ? 'bg-red-500/20 text-red-300' :
                                            'bg-slate-500/20 text-slate-300'
                                        }`}>
                                        {latestNlp.sentiment.label}
                                    </span>
                                </div>
                                <Gauge label="Polarity" value={latestNlp.sentiment.polarity} color="#818cf8" />
                                <div className="grid grid-cols-2 gap-3 text-xs">
                                    <div className="bg-white/5 rounded-lg p-2.5">
                                        <span className="text-slate-500">Absolutist</span>
                                        <p className="text-white font-mono mt-0.5">{latestNlp.features.absolutist_count}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2.5">
                                        <span className="text-slate-500">1st Person</span>
                                        <p className="text-white font-mono mt-0.5">{latestNlp.features.first_person_pronouns}</p>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-xs text-slate-600">Awaiting speech...</p>
                        )}
                    </MetricCard>
                </div>

                {/* ── Column 3: Transcript + Fusion ────── */}
                <div className="space-y-5">

                    {/* Live Transcript */}
                    <MetricCard title="Live Transcript" icon={Mic}>
                        <div className="max-h-[200px] overflow-y-auto space-y-2 scrollbar-thin pr-1">
                            {transcripts.length === 0 ? (
                                <p className="text-xs text-slate-600">Speak into your microphone...</p>
                            ) : (
                                transcripts.map((t, i) => (
                                    <div key={i} className="text-xs text-slate-300 bg-white/5 rounded-lg px-3 py-2">
                                        <span className="text-slate-600 text-[10px] mr-2">#{t.segment_id}</span>
                                        {t.text}
                                    </div>
                                ))
                            )}
                            <div ref={transcriptEndRef} />
                        </div>
                    </MetricCard>

                    {/* Behavioral Summary (Fusion) */}
                    <MetricCard title="Behavioral Summary" icon={Activity}>
                        {fusionSummary ? (
                            <div className="space-y-3">
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="bg-white/5 rounded-lg p-2.5">
                                        <span className="text-slate-500">Valence</span>
                                        <p className="text-white font-mono mt-0.5">{fusionSummary.overall_valence}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2.5">
                                        <span className="text-slate-500">Arousal</span>
                                        <p className="text-white font-mono mt-0.5">{fusionSummary.overall_arousal}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2.5">
                                        <span className="text-slate-500">Sentiment</span>
                                        <p className="text-white font-mono mt-0.5">{fusionSummary.overall_sentiment_polarity}</p>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2.5">
                                        <span className="text-slate-500">Speech Rate</span>
                                        <p className="text-white font-mono mt-0.5">{fusionSummary.avg_speech_rate_wpm} WPM</p>
                                    </div>
                                </div>

                                {/* Observations */}
                                <div className="space-y-1.5">
                                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">Observations</span>
                                    {fusionSummary.observations.map((obs, i) => (
                                        <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                                            <span className="text-primary mt-0.5">•</span>
                                            <span>{obs}</span>
                                        </div>
                                    ))}
                                </div>

                                <div className="text-[10px] text-slate-600 border-t border-white/5 pt-2">
                                    Samples: {fusionSummary.sample_count} | Absolutist: {fusionSummary.total_absolutist_words} | 1st-person: {fusionSummary.total_first_person_pronouns}
                                </div>
                            </div>
                        ) : (
                            <p className="text-xs text-slate-600">Summary appears after analysis begins...</p>
                        )}
                    </MetricCard>
                </div>
            </div>
        </div>
    );
}
