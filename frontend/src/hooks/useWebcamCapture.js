import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Custom hook for webcam capture via getUserMedia + MediaRecorder.
 * Returns controls and state for live video recording.
 */
export default function useWebcamCapture() {
    const [isCapturing, setIsCapturing] = useState(false);
    const [videoBlob, setVideoBlob] = useState(null);
    const [error, setError] = useState(null);
    const [elapsed, setElapsed] = useState(0);

    const previewRef = useRef(null);
    const streamRef = useRef(null);
    const recorderRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);

    // Cleanup helper — stops all tracks and clears refs
    const cleanup = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        if (recorderRef.current && recorderRef.current.state !== 'inactive') {
            try { recorderRef.current.stop(); } catch (_) { }
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }
        if (previewRef.current) {
            previewRef.current.srcObject = null;
        }
        recorderRef.current = null;
    }, []);

    // Start webcam + recording
    const startCapture = useCallback(async () => {
        setError(null);
        setVideoBlob(null);
        setElapsed(0);
        chunksRef.current = [];

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
                audio: false,
            });
            streamRef.current = stream;

            // Attach live preview
            if (previewRef.current) {
                previewRef.current.srcObject = stream;
                previewRef.current.play().catch(() => { });
            }

            // Determine best supported mime type
            const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
                ? 'video/webm;codecs=vp9'
                : MediaRecorder.isTypeSupported('video/webm')
                    ? 'video/webm'
                    : '';

            const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
            recorderRef.current = recorder;

            recorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
            };

            recorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: mimeType || 'video/webm' });
                setVideoBlob(blob);
                // Stop tracks after recording finishes
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(t => t.stop());
                    streamRef.current = null;
                }
                if (previewRef.current) previewRef.current.srcObject = null;
            };

            recorder.start(500); // collect chunks every 500ms
            setIsCapturing(true);

            // Elapsed timer
            const t0 = Date.now();
            timerRef.current = setInterval(() => {
                setElapsed(Math.floor((Date.now() - t0) / 1000));
            }, 1000);

        } catch (err) {
            cleanup();
            setError(err.message || 'Camera access denied');
        }
    }, [cleanup]);

    // Stop recording (triggers onstop → builds blob)
    const stopCapture = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        if (recorderRef.current && recorderRef.current.state !== 'inactive') {
            recorderRef.current.stop();
        }
        setIsCapturing(false);
    }, []);

    // Cleanup on unmount
    useEffect(() => cleanup, [cleanup]);

    return { startCapture, stopCapture, isCapturing, videoBlob, previewRef, error, elapsed };
}
