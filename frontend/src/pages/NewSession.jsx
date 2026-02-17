import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    createSession,
    uploadAudio,
    uploadVideo,
    processText,
    getSessionResults,
    getPatients
} from '../services/api';
import RiskBadge from '../components/RiskBadge';

export default function NewSession() {
    const navigate = useNavigate();
    const [patients, setPatients] = useState([]);
    const [selectedPatient, setSelectedPatient] = useState('');
    const [sessionId, setSessionId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    // Modality states
    const [textInput, setTextInput] = useState('');
    const [audioFile, setAudioFile] = useState(null);
    const [videoFile, setVideoFile] = useState(null);

    // Processing states
    const [status, setStatus] = useState({
        text: 'idle', // idle, processing, success, error
        audio: 'idle',
        video: 'idle',
        fusion: 'idle'
    });

    const [progress, setProgress] = useState({
        audio: 0,
        video: 0
    });

    const [results, setResults] = useState(null);

    useEffect(() => {
        const fetchPatients = async () => {
            try {
                const res = await getPatients();
                setPatients(res.data);
                if (res.data.length > 0) setSelectedPatient(res.data[0].id);
            } catch (err) {
                console.error("Failed to fetch patients", err);
            }
        };
        fetchPatients();
    }, []);

    const handleCreateSession = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await createSession({
                patient_id: selectedPatient,
                interviewer_id: "Clinical Staff"
            });
            setSessionId(res.data.id);
            setSuccess("Session initialized successfully.");
        } catch (err) {
            setError("Failed to create session. Please ensure backend is running.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpload = async (type) => {
        if (!sessionId) return;

        setStatus(prev => ({ ...prev, [type]: 'processing', fusion: 'processing' }));
        if (type !== 'text') setProgress(prev => ({ ...prev, [type]: 0 }));

        try {
            let res;
            if (type === 'text') {
                res = await processText(sessionId, textInput);
            } else if (type === 'audio') {
                res = await uploadAudio(sessionId, audioFile, (p) => {
                    setProgress(prev => ({ ...prev, audio: p }));
                });
            } else if (type === 'video') {
                res = await uploadVideo(sessionId, videoFile, (p) => {
                    setProgress(prev => ({ ...prev, video: p }));
                });
            }

            setStatus(prev => ({ ...prev, [type]: 'success' }));

            // Fetch updated fusion results
            const resultRes = await getSessionResults(sessionId);
            setResults(resultRes.data);
            setStatus(prev => ({ ...prev, fusion: 'success' }));

        } catch (err) {
            console.error(`${type} upload failed`, err);
            setStatus(prev => ({ ...prev, [type]: 'error' }));
        }
    };

    const resetModality = (type) => {
        setStatus(prev => ({ ...prev, [type]: 'idle' }));
        if (type === 'audio') { setAudioFile(null); setProgress(p => ({ ...p, audio: 0 })); }
        if (type === 'video') { setVideoFile(null); setProgress(p => ({ ...p, video: 0 })); }
        if (type === 'text') setTextInput('');
    };

    return (
        <div className="max-w-4xl mx-auto space-y-12 animate-in pb-20">
            {/* Header */}
            <div className="text-center pt-4">
                <h1 className="text-4xl font-bold mb-3 tracking-tight">
                    Clinical <span className="text-primary-400">Session Intake</span>
                </h1>
                <p className="text-surface-400 max-w-xl mx-auto text-lg">
                    Multimodal behavioral analysis for decision support.
                </p>
            </div>

            {error && (
                <div className="p-4 bg-risk-high/10 border border-risk-high/20 rounded-xl text-risk-high text-sm flex items-center justify-between">
                    <span>⚠️ {error}</span>
                    <button onClick={() => setError(null)} className="text-xs hover:underline">Dismiss</button>
                </div>
            )}

            {!sessionId ? (
                /* Step 1: Session Initialization */
                <div className="card-floating bg-surface-900/60 p-10 border border-surface-800 shadow-2xl max-w-2xl mx-auto">
                    <h2 className="text-2xl font-semibold mb-8 flex items-center gap-3">
                        <span className="w-10 h-10 bg-primary-500/10 text-primary-400 rounded-xl flex items-center justify-center font-bold">1</span>
                        Session Setup
                    </h2>

                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-surface-300 mb-3">Target Patient Record</label>
                            {patients.length > 0 ? (
                                <select
                                    value={selectedPatient}
                                    onChange={(e) => setSelectedPatient(e.target.value)}
                                    className="w-full bg-surface-800 border border-surface-700 rounded-xl px-5 py-3.5 focus:ring-2 focus:ring-primary-500 outline-none transition-all appearance-none cursor-pointer"
                                >
                                    {patients.map(p => (
                                        <option key={p.id} value={p.id}>{p.anonymous_id} — {p.gender || 'N/A'}, {p.age_range || 'N/A'}</option>
                                    ))}
                                </select>
                            ) : (
                                <div className="p-4 bg-surface-800/50 border border-surface-700 rounded-xl text-surface-400 text-sm italic">
                                    No patient records found. Please seed the database.
                                </div>
                            )}
                        </div>

                        <button
                            onClick={handleCreateSession}
                            disabled={isLoading || patients.length === 0}
                            className="w-full py-4 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-bold transition-all shadow-xl shadow-primary-500/20 text-lg"
                        >
                            {isLoading ? "Starting Environment..." : "Initialize Session"}
                        </button>
                    </div>
                </div>
            ) : (
                /* Step 2: Multimodal Input */
                <div className="space-y-10">
                    <div className="flex items-center justify-between px-2">
                        <div className="flex items-center gap-4">
                            <div className="px-4 py-1.5 bg-surface-800/80 border border-surface-700/50 rounded-full text-xs font-mono text-primary-400">
                                SESSION_ID: {sessionId.slice(0, 12).toUpperCase()}
                            </div>
                            <div className="w-2 h-2 bg-risk-low rounded-full animate-pulse"></div>
                            <span className="text-xs text-surface-500 font-medium">Session Active</span>
                        </div>
                        <button
                            onClick={() => navigate(`/session/${sessionId}`)}
                            className="group flex items-center gap-2 text-sm text-surface-400 hover:text-primary-400 transition-colors"
                        >
                            View Analysis Dashboard
                            <span className="group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Text Input Panel */}
                        <div className={`card-floating transition-all duration-500 ${status.text === 'success' ? 'border-risk-low/40 bg-risk-low/5' : ''}`}>
                            <div className="flex items-center justify-between mb-5">
                                <h3 className="font-bold text-lg flex items-center gap-3">
                                    <span className="text-2xl">📝</span>
                                    Lexical Snippets
                                </h3>
                                <StatusIndicator status={status.text} />
                            </div>
                            <textarea
                                value={textInput}
                                onChange={(e) => setTextInput(e.target.value)}
                                disabled={status.text === 'processing' || status.text === 'success'}
                                placeholder="Paste interview transcript or clinical notes for sentiment and risk analysis..."
                                className="w-full h-40 bg-surface-800/40 border border-surface-700/50 rounded-xl p-4 text-sm focus:ring-2 focus:ring-primary-500/30 outline-none resize-none transition-all placeholder:text-surface-600"
                            />
                            <div className="mt-4 flex gap-3">
                                {status.text === 'idle' || status.text === 'processing' ? (
                                    <button
                                        onClick={() => handleUpload('text')}
                                        disabled={!textInput || status.text === 'processing'}
                                        className="flex-1 py-3 bg-primary-600/10 hover:bg-primary-600/20 text-primary-400 border border-primary-500/20 rounded-xl text-sm font-bold transition-all disabled:opacity-30"
                                    >
                                        {status.text === 'processing' ? 'Analyzing...' : 'Run Text AI'}
                                    </button>
                                ) : (
                                    <button
                                        onClick={() => resetModality('text')}
                                        className="flex-1 py-3 bg-surface-800 hover:bg-surface-700 text-surface-300 rounded-xl text-sm font-bold transition-all"
                                    >
                                        Clear & New Input
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Audio/Video Upload Panel */}
                        <div className="space-y-6">
                            {/* Audio Card */}
                            <div className={`card-floating transition-all duration-500 ${status.audio === 'success' ? 'border-risk-low/40 bg-risk-low/5' : ''}`}>
                                <div className="flex items-center justify-between mb-5">
                                    <h3 className="font-bold text-lg flex items-center gap-3">
                                        <span className="text-2xl">🎙️</span>
                                        Vocal Prosody
                                    </h3>
                                    <StatusIndicator status={status.audio} progress={progress.audio} />
                                </div>

                                {status.audio === 'idle' || status.audio === 'error' ? (
                                    <div className="space-y-4">
                                        <div className="relative group">
                                            <input
                                                type="file"
                                                accept=".wav,.mp3,.m4a"
                                                onChange={(e) => setAudioFile(e.target.files[0])}
                                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                            />
                                            <div className="border-2 border-dashed border-surface-700/50 group-hover:border-primary-500/30 rounded-xl p-6 text-center transition-colors">
                                                <p className="text-sm text-surface-400 font-medium">
                                                    {audioFile ? audioFile.name : "Drag audio file or click to browse"}
                                                </p>
                                                <p className="text-[10px] text-surface-600 mt-1">Recommended: .wav or .mp3</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleUpload('audio')}
                                            disabled={!audioFile || status.audio === 'processing'}
                                            className="w-full py-3 bg-primary-600/10 hover:bg-primary-600/20 text-primary-400 border border-primary-500/20 rounded-xl text-sm font-bold transition-all disabled:opacity-30"
                                        >
                                            Upload & Process
                                        </button>
                                    </div>
                                ) : (
                                    <div className="py-4 text-center space-y-4">
                                        {status.audio === 'processing' ? (
                                            <div className="w-full bg-surface-800 rounded-full h-2 overflow-hidden">
                                                <div
                                                    className="bg-primary-500 h-full transition-all duration-300 ease-out"
                                                    style={{ width: `${progress.audio}%` }}
                                                ></div>
                                            </div>
                                        ) : (
                                            <button
                                                onClick={() => resetModality('audio')}
                                                className="w-full py-3 bg-surface-800 hover:bg-surface-700 text-surface-300 rounded-xl text-sm font-bold transition-all"
                                            >
                                                Replace Audio File
                                            </button>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Video Card */}
                            <div className={`card-floating transition-all duration-500 ${status.video === 'success' ? 'border-risk-low/40 bg-risk-low/5' : ''}`}>
                                <div className="flex items-center justify-between mb-5">
                                    <h3 className="font-bold text-lg flex items-center gap-3">
                                        <span className="text-2xl">🎥</span>
                                        Facial Affect
                                    </h3>
                                    <StatusIndicator status={status.video} progress={progress.video} />
                                </div>

                                {status.video === 'idle' || status.video === 'error' ? (
                                    <div className="space-y-4">
                                        <div className="relative group">
                                            <input
                                                type="file"
                                                accept=".mp4,.webm"
                                                onChange={(e) => setVideoFile(e.target.files[0])}
                                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                            />
                                            <div className="border-2 border-dashed border-surface-700/50 group-hover:border-primary-500/30 rounded-xl p-6 text-center transition-colors">
                                                <p className="text-sm text-surface-400 font-medium">
                                                    {videoFile ? videoFile.name : "Select video recording for face mesh AI"}
                                                </p>
                                                <p className="text-[10px] text-surface-600 mt-1">Accepts: .mp4, .webm</p>
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => handleUpload('video')}
                                            disabled={!videoFile || status.video === 'processing'}
                                            className="w-full py-3 bg-primary-600/10 hover:bg-primary-600/20 text-primary-400 border border-primary-500/20 rounded-xl text-sm font-bold transition-all disabled:opacity-30"
                                        >
                                            Run Vision Analysis
                                        </button>
                                    </div>
                                ) : (
                                    <div className="py-4 text-center space-y-4">
                                        {status.video === 'processing' ? (
                                            <div className="w-full bg-surface-800 rounded-full h-2 overflow-hidden">
                                                <div
                                                    className="bg-primary-500 h-full transition-all duration-300 ease-out"
                                                    style={{ width: `${progress.video}%` }}
                                                ></div>
                                            </div>
                                        ) : (
                                            <button
                                                onClick={() => resetModality('video')}
                                                className="w-full py-3 bg-surface-800 hover:bg-surface-700 text-surface-300 rounded-xl text-sm font-bold transition-all"
                                            >
                                                Use Different Video
                                            </button>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Dynamic Results Preview */}
                    {results && (
                        <div className="card-floating relative overflow-hidden animate-in border-surface-700/40 bg-surface-900/40">
                            <div className="absolute top-0 right-0 p-6">
                                <RiskBadge band={results.risk_band} score={results.risk_score} />
                            </div>

                            <div className="mb-8">
                                <h3 className="text-2xl font-bold mb-2">Multimodal <span className="text-primary-400">Fusion Report</span></h3>
                                <p className="text-xs text-surface-500 font-mono tracking-widest">REAL-TIME CLINICAL INDICATORS</p>
                            </div>

                            <div className="space-y-8">
                                <div className="p-6 bg-surface-800/20 rounded-2xl border border-surface-700/30 ring-1 ring-white/5">
                                    <p className="text-[10px] text-primary-400 uppercase tracking-widest font-bold mb-3 flex items-center gap-2">
                                        <span className="w-2 h-2 bg-primary-400 rounded-full"></span>
                                        Behavioral Summary
                                    </p>
                                    <p className="text-surface-100 text-lg leading-relaxed font-medium italic">
                                        "{results.summary}"
                                    </p>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="p-5 bg-surface-800/40 rounded-2xl border border-surface-700/50">
                                        <p className="text-[10px] text-surface-500 uppercase tracking-widest font-bold mb-4">Underlying Factors</p>
                                        <ul className="space-y-2.5">
                                            {results.fusion_result?.explainability?.decision_factors?.map((f, i) => (
                                                <li key={i} className="text-xs flex items-start gap-3 text-surface-200">
                                                    <span className="mt-1 w-1.5 h-1.5 bg-primary-500 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.6)]"></span>
                                                    {f}
                                                </li>
                                            ))}
                                            {(!results.fusion_result?.explainability?.decision_factors || results.fusion_result?.explainability?.decision_factors.length === 0) && (
                                                <li className="text-xs text-surface-500 italic">No significant factors identified yet.</li>
                                            )}
                                        </ul>
                                    </div>
                                    <div className="p-5 bg-surface-800/40 rounded-2xl border border-surface-700/50 flex flex-col justify-between">
                                        <div>
                                            <p className="text-[10px] text-surface-500 uppercase tracking-widest font-bold mb-4">Analysis Confidence</p>
                                            <div className="flex items-end gap-3 mb-2">
                                                <span className="text-4xl font-black text-white tracking-tighter">{(results.fusion_result?.confidence?.score * 100).toFixed(0)}%</span>
                                                <div className="mb-1.5 flex flex-col">
                                                    <span className="text-[10px] text-primary-400 font-bold uppercase tracking-tighter">Reliability index</span>
                                                    <span className="text-[9px] text-surface-500">Based on {results.fusion_result?.confidence?.modalities_available?.length || 0} channels</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex gap-1 mt-4">
                                            {['Audio', 'Vision', 'NLP'].map(m => (
                                                <div
                                                    key={m}
                                                    className={`h-1 flex-1 rounded-full transition-colors duration-500 ${results.fusion_result?.confidence?.modalities_available?.includes(m) ? 'bg-primary-500' : 'bg-surface-700'}`}
                                                ></div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-10 pt-6 border-t border-surface-800/80">
                                <div className="flex items-start gap-3">
                                    <span className="text-risk-high text-xs">⚠️</span>
                                    <p className="text-[10px] text-surface-500 leading-normal italic font-medium">
                                        {results.fusion_result?.explainability?.disclaimer}
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function StatusIndicator({ status, progress }) {
    if (status === 'processing') {
        return (
            <div className="flex flex-col items-end gap-1.5">
                <span className="text-[10px] font-bold uppercase tracking-widest text-primary-400 animate-pulse">Analyzing...</span>
                {progress !== undefined && progress > 0 && progress < 100 && (
                    <span className="text-[9px] text-surface-500 font-mono">{progress}% uploaded</span>
                )}
            </div>
        );
    }
    if (status === 'success') {
        return (
            <div className="flex items-center gap-2 bg-risk-low/10 px-2.5 py-1 rounded-full border border-risk-low/20 animate-in">
                <span className="text-[10px] font-bold uppercase tracking-widest text-risk-low">Success</span>
                <span className="text-xs">✓</span>
            </div>
        );
    }
    if (status === 'error') {
        return (
            <div className="flex items-center gap-2 bg-risk-high/10 px-2.5 py-1 rounded-full border border-risk-high/20 animate-in">
                <span className="text-[10px] font-bold uppercase tracking-widest text-risk-high">Error</span>
                <span className="text-xs">✕</span>
            </div>
        );
    }
    return <span className="text-[10px] font-bold uppercase tracking-widest text-surface-600">Idle</span>;
}
