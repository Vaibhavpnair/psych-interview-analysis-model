/**
 * API Service — Axios client for all backend endpoints.
 */
import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// ── Sessions ────────────────────────────────────

export const getSessions = () => api.get('/sessions/');

export const getSession = (id) => api.get(`/sessions/${id}`);

export const createSession = (data) => api.post('/sessions/', data);

export const getSessionSummary = (id) => api.get(`/sessions/${id}/summary`);

export const getSessionTimeline = (id) => api.get(`/sessions/${id}/timeline`);

export const getSessionTranscript = (id) => api.get(`/sessions/${id}/transcript`);

export const getSessionResults = (id) => api.get(`/sessions/${id}/results`);

export const uploadAudio = (sessionId, file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/sessions/${sessionId}/audio`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
            if (onProgress) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percentCompleted);
            }
        }
    });
};

export const uploadVideo = (sessionId, file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/sessions/${sessionId}/video`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
            if (onProgress) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percentCompleted);
            }
        }
    });
};

export const processText = (sessionId, text) =>
    api.post(`/sessions/${sessionId}/text`, { text });

export const addClinicianNote = (sessionId, note) =>
    api.post(`/sessions/${sessionId}/notes`, note);

// ── Patients ────────────────────────────────────

export const getPatients = () => api.get('/patients/');

export const getPatient = (id) => api.get(`/patients/${id}`);

export const getPatientHistory = (id) => api.get(`/patients/${id}/history`);

export default api;
