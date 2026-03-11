/**
 * useAssessmentSession — React hook for question-driven multimodal assessment.
 *
 * Enhanced with:
 *  - Pause/resume session control
 *  - Clinician override of previous answers
 *  - Skip question support
 *  - Per-question metrics snapshots
 *  - Full report reception
 */

import { useState, useCallback, useRef, useEffect } from 'react';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export default function useAssessmentSession() {
    const [isConnected, setIsConnected] = useState(false);
    const [isPaused, setIsPaused] = useState(false);
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [questionMetrics, setQuestionMetrics] = useState(null);
    const [results, setResults] = useState(null);
    const [faceData, setFaceData] = useState(null);
    const [audioFeatures, setAudioFeatures] = useState(null);
    const [transcripts, setTranscripts] = useState([]);
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [mediaStream, setMediaStream] = useState(null);

    const wsRef = useRef(null);
    const streamRef = useRef(null);
    const audioCtxRef = useRef(null);
    const sourceRef = useRef(null);
    const processorRef = useRef(null);
    const videoIntervalRef = useRef(null);
    const canvasRef = useRef(null);
    const offscreenVideoRef = useRef(null);

    const cleanup = useCallback(() => {
        if (videoIntervalRef.current) {
            clearInterval(videoIntervalRef.current);
            videoIntervalRef.current = null;
        }
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }
        if (sourceRef.current) {
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        if (audioCtxRef.current) {
            audioCtxRef.current.close().catch(() => { });
            audioCtxRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }
        if (offscreenVideoRef.current) {
            offscreenVideoRef.current.pause();
            offscreenVideoRef.current.srcObject = null;
            offscreenVideoRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        canvasRef.current = null;
        setMediaStream(null);
    }, []);

    const startAssessment = useCallback(async () => {
        setError(null);
        setCurrentQuestion(null);
        setQuestionMetrics(null);
        setResults(null);
        setFaceData(null);
        setAudioFeatures(null);
        setTranscripts([]);
        setIsPaused(false);
        setMediaStream(null);

        try {
            const sessionId = `assess-${Date.now()}`;
            const ws = new WebSocket(`${WS_BASE}/ws/assessment/${sessionId}`);
            ws.binaryType = 'arraybuffer';
            wsRef.current = ws;

            await new Promise((resolve, reject) => {
                ws.onopen = resolve;
                ws.onerror = () => reject(new Error('WebSocket connection failed'));
                setTimeout(() => reject(new Error('Connection timeout')), 5000);
            });

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    switch (msg.type) {
                        case 'question':
                            setCurrentQuestion(msg.data);
                            setSubmitting(false);
                            setQuestionMetrics(null);
                            setFaceData(null);
                            setAudioFeatures(null);
                            break;
                        case 'question_metrics':
                            setQuestionMetrics(msg.data);
                            break;
                        case 'face_data':
                            setFaceData(msg.data);
                            break;
                        case 'audio_features':
                            setAudioFeatures(msg.data);
                            break;
                        case 'transcript':
                            if (msg.data?.text?.trim()) {
                                setTranscripts(prev => [...prev, msg.data.text]);
                            }
                            break;
                        case 'assessment_complete':
                            setResults(msg.data);
                            setCurrentQuestion(null);
                            setQuestionMetrics(null);
                            break;
                        case 'paused':
                            setIsPaused(true);
                            break;
                        case 'resumed':
                            setIsPaused(false);
                            break;
                        case 'error':
                            setError(msg.data?.message || 'Unknown error');
                            break;
                    }
                } catch (e) {
                    console.error('[Assessment] Parse error:', e);
                }
            };

            ws.onclose = () => setIsConnected(false);

            // Get media stream (audio + video)
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                },
                video: {
                    width: { ideal: 320 },
                    height: { ideal: 240 },
                    frameRate: { ideal: 5, max: 10 },
                },
            });
            streamRef.current = stream;
            setMediaStream(stream);           // expose to component for <video> preview

            // Create an offscreen video element for frame capture
            const offscreenVideo = document.createElement('video');
            offscreenVideo.srcObject = stream;
            offscreenVideo.muted = true;
            offscreenVideo.playsInline = true;
            offscreenVideoRef.current = offscreenVideo;

            await new Promise((resolve) => {
                const onPlaying = () => {
                    offscreenVideo.removeEventListener('playing', onPlaying);
                    resolve();
                };
                if (!offscreenVideo.paused && offscreenVideo.readyState >= 2) {
                    resolve();
                } else {
                    offscreenVideo.addEventListener('playing', onPlaying);
                    offscreenVideo.play().catch(() => { });
                }
            });

            const settings = stream.getVideoTracks()[0].getSettings();
            const cw = settings.width || 320;
            const ch = settings.height || 240;
            const canvas = document.createElement('canvas');
            canvas.width = cw;
            canvas.height = ch;
            canvasRef.current = canvas;
            const ctx = canvas.getContext('2d');

            videoIntervalRef.current = setInterval(() => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                const track = stream.getVideoTracks()[0];
                if (!track || track.readyState !== 'live') return;

                ctx.drawImage(offscreenVideo, 0, 0, cw, ch);
                canvas.toBlob((blob) => {
                    if (!blob || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                    blob.arrayBuffer().then((buf) => {
                        const header = new Uint8Array([0x02]);
                        const payload = new Uint8Array(buf);
                        const frame = new Uint8Array(1 + payload.length);
                        frame.set(header);
                        frame.set(payload, 1);
                        wsRef.current.send(frame.buffer);
                    });
                }, 'image/jpeg', 0.7);
            }, 200);

            // Audio capture
            const audioCtx = new AudioContext({ sampleRate: 16000 });
            audioCtxRef.current = audioCtx;
            const source = audioCtx.createMediaStreamSource(stream);
            sourceRef.current = source;

            const bufferSize = 4096;
            const processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);
            processorRef.current = processor;

            processor.onaudioprocess = (e) => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                const pcm = e.inputBuffer.getChannelData(0);
                const header = new Uint8Array([0x01]);
                const pcmBytes = new Uint8Array(pcm.buffer.slice(0));
                const frame = new Uint8Array(1 + pcmBytes.length);
                frame.set(header);
                frame.set(pcmBytes, 1);
                wsRef.current.send(frame.buffer);
            };

            source.connect(processor);
            processor.connect(audioCtx.destination);

            setIsConnected(true);

        } catch (err) {
            cleanup();
            setError(err.message || 'Failed to start assessment');
        }
    }, [cleanup]);

    const submitAnswer = useCallback((score) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        setSubmitting(true);
        setTranscripts([]);
        wsRef.current.send(JSON.stringify({ type: 'submit_answer', score }));
    }, []);

    const pauseSession = useCallback(() => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        wsRef.current.send(JSON.stringify({ type: 'pause' }));
    }, []);

    const resumeSession = useCallback(() => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        wsRef.current.send(JSON.stringify({ type: 'resume' }));
    }, []);

    const skipQuestion = useCallback(() => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        setSubmitting(true);
        setTranscripts([]);
        wsRef.current.send(JSON.stringify({ type: 'skip_question' }));
    }, []);

    const overrideScore = useCallback((questionId, score) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
        wsRef.current.send(JSON.stringify({
            type: 'override_score',
            question_id: questionId,
            score,
        }));
    }, []);

    const stopAssessment = useCallback(() => {
        cleanup();
        setIsConnected(false);
        setCurrentQuestion(null);
        setIsPaused(false);
        setMediaStream(null);
    }, [cleanup]);

    useEffect(() => cleanup, [cleanup]);

    return {
        startAssessment,
        submitAnswer,
        pauseSession,
        resumeSession,
        skipQuestion,
        overrideScore,
        stopAssessment,
        isConnected,
        isPaused,
        currentQuestion,
        questionMetrics,
        results,
        faceData,
        audioFeatures,
        transcripts,
        error,
        submitting,
        mediaStream,
    };
}
