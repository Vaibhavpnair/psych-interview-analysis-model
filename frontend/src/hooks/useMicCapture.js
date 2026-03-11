import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Custom hook for microphone capture via getUserMedia + MediaRecorder (audio only).
 * Returns controls and state for live audio recording.
 */
export default function useMicCapture() {
    const [isRecording, setIsRecording] = useState(false);
    const [audioBlob, setAudioBlob] = useState(null);
    const [error, setError] = useState(null);
    const [elapsed, setElapsed] = useState(0);

    const streamRef = useRef(null);
    const recorderRef = useRef(null);
    const chunksRef = useRef([]);
    const timerRef = useRef(null);

    // Cleanup helper
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
        recorderRef.current = null;
    }, []);

    // Start microphone + recording
    const startRecording = useCallback(async () => {
        setError(null);
        setAudioBlob(null);
        setElapsed(0);
        chunksRef.current = [];

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: { echoCancellation: true, noiseSuppression: true },
                video: false,
            });
            streamRef.current = stream;

            // Pick best supported audio mime
            const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                ? 'audio/webm;codecs=opus'
                : MediaRecorder.isTypeSupported('audio/webm')
                    ? 'audio/webm'
                    : '';

            const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
            recorderRef.current = recorder;

            recorder.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
            };

            recorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' });
                setAudioBlob(blob);
                // Release mic
                if (streamRef.current) {
                    streamRef.current.getTracks().forEach(t => t.stop());
                    streamRef.current = null;
                }
            };

            recorder.start(500); // collect chunks every 500ms
            setIsRecording(true);

            // Elapsed timer
            const t0 = Date.now();
            timerRef.current = setInterval(() => {
                setElapsed(Math.floor((Date.now() - t0) / 1000));
            }, 1000);

        } catch (err) {
            cleanup();
            setError(err.message || 'Microphone access denied');
        }
    }, [cleanup]);

    // Stop recording (triggers onstop → builds blob)
    const stopRecording = useCallback(() => {
        if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
        }
        if (recorderRef.current && recorderRef.current.state !== 'inactive') {
            recorderRef.current.stop();
        }
        setIsRecording(false);
    }, []);

    // Cleanup on unmount
    useEffect(() => cleanup, [cleanup]);

    return { startRecording, stopRecording, isRecording, audioBlob, error, elapsed };
}
