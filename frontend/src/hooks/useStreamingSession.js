/**
 * useStreamingSession — React hook for managing a real-time streaming session.
 *
 * Provides:
 *   - start/stop controls
 *   - real-time state: transcripts, audioFeatures, faceData, nlpResults, fusionSummary
 *   - connection status
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { streamingService } from '../services/streamingService';

export function useStreamingSession() {
    const [isConnected, setIsConnected] = useState(false);
    const [isRecording, setIsRecording] = useState(false);
    const [error, setError] = useState(null);

    // Real-time data
    const [transcripts, setTranscripts] = useState([]);
    const [audioFeatures, setAudioFeatures] = useState(null);
    const [audioUpdate, setAudioUpdate] = useState(null);  // chunk + rolling + cumulative
    const [faceData, setFaceData] = useState(null);
    const [nlpResults, setNlpResults] = useState([]);
    const [fusionSummary, setFusionSummary] = useState(null);

    // Ref for video element (needed by streaming service)
    const videoRef = useRef(null);

    // Cleanup subscriptions
    const unsubsRef = useRef([]);

    const startSession = useCallback(async (videoElement) => {
        setError(null);

        const sessionId = `session-${Date.now()}`;

        try {
            // Connect WebSocket
            await streamingService.connect(sessionId);

            // Subscribe to events
            const unsubs = [
                streamingService.on('connection', (data) => {
                    setIsConnected(data.connected);
                }),
                streamingService.on('transcript', (data) => {
                    setTranscripts(prev => [...prev, data]);
                }),
                streamingService.on('audio_features', (data) => {
                    setAudioFeatures(data);
                }),
                streamingService.on('audio_update', (data) => {
                    setAudioUpdate(data);
                }),
                streamingService.on('face_data', (data) => {
                    setFaceData(data);
                }),
                streamingService.on('nlp_result', (data) => {
                    setNlpResults(prev => [...prev, data]);
                }),
                streamingService.on('fusion_summary', (data) => {
                    setFusionSummary(data);
                }),
                streamingService.on('error', (data) => {
                    setError(data.message);
                }),
            ];
            unsubsRef.current = unsubs;

            // Start streams
            await streamingService.startAudio();
            await streamingService.startVideo(videoElement);

            setIsRecording(true);
            setIsConnected(true);
        } catch (e) {
            console.error('Failed to start session:', e);
            setError(e.message || 'Failed to start session');
            streamingService.disconnect();
        }
    }, []);

    const stopSession = useCallback(() => {
        streamingService.disconnect();
        unsubsRef.current.forEach(unsub => unsub());
        unsubsRef.current = [];
        setIsRecording(false);
        setIsConnected(false);
    }, []);

    const resetData = useCallback(() => {
        setTranscripts([]);
        setAudioFeatures(null);
        setAudioUpdate(null);
        setFaceData(null);
        setNlpResults([]);
        setFusionSummary(null);
        setError(null);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            streamingService.disconnect();
            unsubsRef.current.forEach(unsub => unsub());
        };
    }, []);

    return {
        // State
        isConnected,
        isRecording,
        error,
        transcripts,
        audioFeatures,
        audioUpdate,
        faceData,
        nlpResults,
        fusionSummary,

        // Actions
        startSession,
        stopSession,
        resetData,
        videoRef,
    };
}
