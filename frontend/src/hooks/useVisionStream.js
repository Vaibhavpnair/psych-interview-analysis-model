/**
 * useVisionStream — React hook for real-time vision-only streaming.
 *
 * Opens a WebSocket to /ws/vision/{session_id}, captures webcam frames
 * as JPEG at 5fps, and receives face_data events from the backend.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export default function useVisionStream() {
    const [isStreaming, setIsStreaming] = useState(false);
    const [faceData, setFaceData] = useState(null);
    const [frameCount, setFrameCount] = useState(0);
    const [error, setError] = useState(null);
    const [elapsed, setElapsed] = useState(0);

    const videoRef = useRef(null);
    const wsRef = useRef(null);
    const streamRef = useRef(null);
    const intervalRef = useRef(null);
    const canvasRef = useRef(null);
    const ctxRef = useRef(null);
    const timerRef = useRef(null);

    const cleanup = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
        canvasRef.current = null;
        ctxRef.current = null;
    }, []);

    const startStream = useCallback(async (videoElement) => {
        setError(null);
        setFaceData(null);
        setFrameCount(0);
        setElapsed(0);

        if (!videoElement) {
            setError('Video element is required');
            return;
        }

        try {
            // 1. Connect WebSocket
            const sessionId = `vision-${Date.now()}`;
            const ws = new WebSocket(`${WS_BASE}/ws/vision/${sessionId}`);
            ws.binaryType = 'arraybuffer';
            wsRef.current = ws;

            await new Promise((resolve, reject) => {
                ws.onopen = resolve;
                ws.onerror = (e) => reject(new Error('WebSocket connection failed'));
                // Timeout after 5s
                setTimeout(() => reject(new Error('WebSocket connection timeout')), 5000);
            });

            // 2. Listen for face_data events
            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === 'face_data') {
                        setFaceData(msg.data);
                        setFrameCount(prev => prev + 1);
                    }
                } catch (e) {
                    console.error('[useVisionStream] Parse error:', e);
                }
            };

            ws.onclose = () => {
                setIsStreaming(false);
            };

            // 3. Get webcam stream (video only)
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 320 },
                    height: { ideal: 240 },
                    frameRate: { ideal: 5, max: 10 },
                },
                audio: false,
            });
            streamRef.current = stream;
            videoElement.srcObject = stream;

            // 4. Wait for video to actually start playing
            await new Promise((resolve) => {
                const onPlaying = () => {
                    videoElement.removeEventListener('playing', onPlaying);
                    resolve();
                };
                if (!videoElement.paused && videoElement.readyState >= 2) {
                    resolve();
                } else {
                    videoElement.addEventListener('playing', onPlaying);
                    videoElement.play().catch(() => { });
                }
            });

            // 5. Setup canvas for JPEG encoding
            const settings = stream.getVideoTracks()[0].getSettings();
            const cw = settings.width || 320;
            const ch = settings.height || 240;

            const canvas = document.createElement('canvas');
            canvas.width = cw;
            canvas.height = ch;
            canvasRef.current = canvas;
            ctxRef.current = canvas.getContext('2d');

            console.log(`[useVisionStream] Capture started: ${cw}x${ch}`);

            // 6. Capture at 5fps
            intervalRef.current = setInterval(() => {
                if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                if (!streamRef.current) return;

                const track = streamRef.current.getVideoTracks()[0];
                if (!track || track.readyState !== 'live') return;

                ctxRef.current.drawImage(videoElement, 0, 0, cw, ch);

                canvasRef.current.toBlob(
                    (blob) => {
                        if (!blob || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
                        blob.arrayBuffer().then((buf) => {
                            wsRef.current.send(buf);
                        });
                    },
                    'image/jpeg',
                    0.7
                );
            }, 200);

            // 7. Elapsed timer
            const t0 = Date.now();
            timerRef.current = setInterval(() => {
                setElapsed(Math.floor((Date.now() - t0) / 1000));
            }, 1000);

            setIsStreaming(true);

        } catch (err) {
            cleanup();
            setError(err.message || 'Failed to start vision stream');
        }
    }, [cleanup]);

    const stopStream = useCallback(() => {
        cleanup();
        setIsStreaming(false);
    }, [cleanup]);

    // Cleanup on unmount
    useEffect(() => cleanup, [cleanup]);

    return {
        startStream,
        stopStream,
        isStreaming,
        faceData,
        frameCount,
        error,
        elapsed,
        videoRef,
    };
}
