import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const client = axios.create({
    baseURL: API_URL,
    timeout: 60_000,
    headers: { 'Accept': 'application/json' },
});

/**
 * Audio analysis — upload WAV/MP3/M4A file.
 * @param {File} file
 * @returns {Promise<{ features, segments, processing_time }>}
 */
export async function analyzeAudio(file) {
    const form = new FormData();
    form.append('file', file);
    const { data } = await client.post('/audio/analyze', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
}

/**
 * NLP analysis — send transcript text.
 * @param {string} transcript
 * @returns {Promise<{ sentiment, features, processing_time }>}
 */
export async function analyzeNLP(transcript) {
    const { data } = await client.post('/nlp/analyze', {
        session_id: `session-${Date.now()}`,
        transcript,
    });
    return data;
}

/**
 * Vision analysis — upload MP4/MOV/AVI file.
 * @param {File} file
 * @returns {Promise<{ average_valence, average_arousal, frames, processing_time }>}
 */
export async function analyzeVision(file) {
    const form = new FormData();
    form.append('file', file);
    const { data } = await client.post('/vision/analyze', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
}
