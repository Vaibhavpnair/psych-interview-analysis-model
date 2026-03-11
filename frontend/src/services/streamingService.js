/**
 * StreamingService — WebSocket client for real-time audio + video streaming.
 *
 * Protocol:
 *   Send binary:  0x01 + PCM float32 bytes (audio)
 *                 0x02 + JPEG bytes (video)
 *   Receive JSON: { type, data }
 */

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

const HEADER_AUDIO = 0x01;
const HEADER_VIDEO = 0x02;

export class StreamingService {
    constructor() {
        this._ws = null;
        this._listeners = new Map();
        this._audioContext = null;
        this._audioStream = null;
        this._videoStream = null;
        this._videoInterval = null;
        this._videoCanvas = null;
        this._videoCtx = null;
        this._reconnectTimer = null;
        this._sessionId = null;
        this._isConnected = false;
    }

    // ── Connection ──────────────────────────────────────────

    connect(sessionId) {
        return new Promise((resolve, reject) => {
            this._sessionId = sessionId;
            const url = `${WS_BASE}/ws/stream/${sessionId}`;

            this._ws = new WebSocket(url);
            this._ws.binaryType = 'arraybuffer';

            this._ws.onopen = () => {
                this._isConnected = true;
                this._emit('connection', { connected: true });
                resolve();
            };

            this._ws.onerror = (e) => {
                console.error('[StreamingService] WS error:', e);
                this._emit('error', { message: 'WebSocket connection error' });
                reject(e);
            };

            this._ws.onclose = () => {
                this._isConnected = false;
                this._emit('connection', { connected: false });
            };

            this._ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    this._emit(msg.type, msg.data);
                } catch (e) {
                    console.error('[StreamingService] Parse error:', e);
                }
            };
        });
    }

    disconnect() {
        this.stopAudio();
        this.stopVideo();
        if (this._ws) {
            this._ws.close();
            this._ws = null;
        }
        this._isConnected = false;
    }

    get isConnected() {
        return this._isConnected;
    }

    // ── Event Emitter ───────────────────────────────────────

    on(type, callback) {
        if (!this._listeners.has(type)) {
            this._listeners.set(type, []);
        }
        this._listeners.get(type).push(callback);
        return () => {
            const arr = this._listeners.get(type);
            if (arr) {
                const idx = arr.indexOf(callback);
                if (idx !== -1) arr.splice(idx, 1);
            }
        };
    }

    _emit(type, data) {
        const cbs = this._listeners.get(type) || [];
        cbs.forEach(cb => cb(data));
    }

    // ── Audio Streaming ─────────────────────────────────────

    async startAudio() {
        if (!this._isConnected) throw new Error('Not connected');

        this._audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
            },
        });

        this._audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: 16000,
        });

        const source = this._audioContext.createMediaStreamSource(this._audioStream);

        // ScriptProcessorNode — widely supported fallback
        // Buffer size 4096 at 16kHz ≈ 256ms per chunk
        const processor = this._audioContext.createScriptProcessor(4096, 1, 1);

        processor.onaudioprocess = (e) => {
            if (!this._isConnected || !this._ws) return;

            const input = e.inputBuffer.getChannelData(0);
            const pcmBytes = new Float32Array(input).buffer;

            // Prepend header byte
            const msg = new Uint8Array(1 + pcmBytes.byteLength);
            msg[0] = HEADER_AUDIO;
            msg.set(new Uint8Array(pcmBytes), 1);

            if (this._ws.readyState === WebSocket.OPEN) {
                this._ws.send(msg.buffer);
            }
        };

        source.connect(processor);
        processor.connect(this._audioContext.destination);
        this._audioProcessor = processor;
        this._audioSource = source;
    }

    stopAudio() {
        if (this._audioProcessor) {
            this._audioProcessor.disconnect();
            this._audioProcessor = null;
        }
        if (this._audioSource) {
            this._audioSource.disconnect();
            this._audioSource = null;
        }
        if (this._audioContext) {
            this._audioContext.close();
            this._audioContext = null;
        }
        if (this._audioStream) {
            this._audioStream.getTracks().forEach(t => t.stop());
            this._audioStream = null;
        }
    }

    // ── Video Streaming ─────────────────────────────────────

    async startVideo(videoElement) {
        if (!this._isConnected) throw new Error('Not connected');
        if (!videoElement) throw new Error('Video element is required');

        this._videoStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 320 },
                height: { ideal: 240 },
                frameRate: { ideal: 5, max: 10 },
            },
        });

        videoElement.srcObject = this._videoStream;
        this._videoElement = videoElement;

        // Wait for the video element to actually start playing
        await new Promise((resolve) => {
            const onPlaying = () => {
                videoElement.removeEventListener('playing', onPlaying);
                resolve();
            };
            // Already playing (e.g. autoPlay worked immediately)
            if (!videoElement.paused && videoElement.readyState >= 2) {
                resolve();
            } else {
                videoElement.addEventListener('playing', onPlaying);
                videoElement.play().catch(() => { });
            }
        });

        // Size canvas to actual video track dimensions
        const settings = this._videoStream.getVideoTracks()[0].getSettings();
        const cw = settings.width || 320;
        const ch = settings.height || 240;

        this._videoCanvas = document.createElement('canvas');
        this._videoCanvas.width = cw;
        this._videoCanvas.height = ch;
        this._videoCtx = this._videoCanvas.getContext('2d');

        console.log(`[StreamingService] Video capture started: ${cw}x${ch}`);

        // Capture at 5fps — draw from the live video element
        this._videoInterval = setInterval(() => {
            if (!this._isConnected || !this._ws || !this._videoStream) return;

            const track = this._videoStream.getVideoTracks()[0];
            if (!track || track.readyState !== 'live') return;

            // Draw current frame from the playing video element
            this._videoCtx.drawImage(this._videoElement, 0, 0, cw, ch);

            // Encode as JPEG and send
            this._videoCanvas.toBlob(
                (blob) => {
                    if (!blob || !this._ws || this._ws.readyState !== WebSocket.OPEN) return;
                    blob.arrayBuffer().then((buf) => {
                        const msg = new Uint8Array(1 + buf.byteLength);
                        msg[0] = HEADER_VIDEO;
                        msg.set(new Uint8Array(buf), 1);
                        this._ws.send(msg.buffer);
                    });
                },
                'image/jpeg',
                0.7
            );
        }, 200); // 5fps
    }

    stopVideo() {
        if (this._videoInterval) {
            clearInterval(this._videoInterval);
            this._videoInterval = null;
        }
        if (this._videoStream) {
            this._videoStream.getTracks().forEach(t => t.stop());
            this._videoStream = null;
        }
        this._videoCanvas = null;
        this._videoCtx = null;
        this._videoElement = null;
    }
}

// Singleton
export const streamingService = new StreamingService();
