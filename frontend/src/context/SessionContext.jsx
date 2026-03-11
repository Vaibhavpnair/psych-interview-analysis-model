/**
 * SessionContext — Global state for the current session.
 * Uses Zustand for lightweight state management.
 */
import { create } from 'zustand';

const useSessionStore = create((set) => ({
    // Current session data
    currentSession: null,
    timeline: [],
    transcript: [],

    // Loading states
    isLoading: false,
    error: null,

    // Actions
    setSession: (session) => set({ currentSession: session }),
    setTimeline: (data) => set({ timeline: data }),
    setTranscript: (segments) => set({ transcript: segments }),
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),

    reset: () => set({
        currentSession: null,
        timeline: [],
        transcript: [],
        isLoading: false,
        error: null,
    }),
}));

export default useSessionStore;
