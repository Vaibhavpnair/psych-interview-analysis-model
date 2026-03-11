/**
 * BehavioralTimeline — Zone B of the dashboard.
 * Multi-track synchronized timeline: Audio waveform, Emotion curve, Event flags.
 */
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function BehavioralTimeline({ data = [] }) {
    if (data.length === 0) {
        return (
            <div className="card-floating animate-in">
                <h3 className="text-sm font-bold uppercase tracking-widest text-surface-200/50 mb-6">
                    Behavioral Timeline
                </h3>
                <div className="h-64 flex flex-col items-center justify-center text-surface-400 gap-3 border-2 border-dashed border-surface-800 rounded-xl">
                    <span className="text-3xl opacity-20">📊</span>
                    <p className="text-sm font-medium">Timeline synchronization pending analysis</p>
                </div>
            </div>
        );
    }

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-surface-900 border border-surface-700 p-3 rounded-lg shadow-2xl backdrop-blur-md">
                    <p className="text-[10px] font-bold text-primary-400 mb-2 uppercase tracking-tighter">
                        T + {label}s
                    </p>
                    <div className="space-y-1.5">
                        {payload.map((p, i) => (
                            <div key={i} className="flex justify-between gap-4 text-xs">
                                <span className="text-surface-300 capitalize">
                                    {p.name.replace(/_/g, ' ')}:
                                </span>
                                <span className="font-mono text-white font-bold">
                                    {p.value.toFixed(2)}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="card-floating animate-in">
            <div className="flex items-center justify-between mb-8">
                <h3 className="text-sm font-bold uppercase tracking-widest text-surface-200/50">
                    Multimodal Timeline
                </h3>
                <div className="flex gap-4">
                    <LegendItem color="#818cf8" label="Face Valence" />
                    <LegendItem color="#ef4444" label="Sentiment" />
                    <LegendItem color="#fbbf24" label="Arousal" />
                </div>
            </div>

            <div className="space-y-10">
                {/* Track 1: Emotional Valence vs Sentiment */}
                <div className="group">
                    <div className="flex items-center justify-between mb-4">
                        <p className="text-[10px] font-bold text-surface-400 uppercase tracking-widest group-hover:text-primary-400 transition-colors">
                            Affective Range (Valence)
                        </p>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-surface-800 text-surface-400 font-mono">
                            Scale: -1.0 to +1.0
                        </span>
                    </div>
                    <div className="h-32">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <XAxis dataKey="timestamp" hide />
                                <YAxis domain={[-1, 1]} hide />
                                <Tooltip content={<CustomTooltip />} />
                                <ReferenceLine y={0} stroke="#334155" strokeDasharray="3 3" />
                                <Line
                                    name="face_valence"
                                    type="monotone"
                                    dataKey="face_valence"
                                    stroke="#818cf8"
                                    strokeWidth={3}
                                    dot={false}
                                    animationDuration={1500}
                                />
                                <Line
                                    name="sentiment_score"
                                    type="step"
                                    dataKey="sentiment_score"
                                    stroke="#ef4444"
                                    strokeWidth={2}
                                    strokeDasharray="5 5"
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Track 2: Engagement (Arousal) */}
                <div className="group">
                    <p className="text-[10px] font-bold text-surface-400 uppercase tracking-widest mb-4 group-hover:text-amber-400 transition-colors">
                        Psychological Arousal
                    </p>
                    <div className="h-20">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={data}>
                                <XAxis dataKey="timestamp" hide />
                                <YAxis domain={[0, 1]} hide />
                                <Tooltip content={<CustomTooltip />} />
                                <Line
                                    name="arousal"
                                    type="monotone"
                                    dataKey="arousal"
                                    stroke="#fbbf24"
                                    strokeWidth={2}
                                    fillOpacity={0.1}
                                    fill="url(#colorArousal)"
                                    dot={false}
                                />
                                <defs>
                                    <linearGradient id="colorArousal" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.1} />
                                        <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Track 3: Contradiction Flags */}
                <div>
                    <p className="text-[10px] font-bold text-surface-400 uppercase tracking-widest mb-4">
                        Analysis Markers & Contradictions
                    </p>
                    <div className="flex flex-wrap gap-2 min-h-8">
                        {data.filter(d => d.flag).map((d, i) => (
                            <div
                                key={i}
                                className={`text-[10px] px-3 py-1.5 rounded-lg border font-bold flex items-center gap-2 transition-all hover:scale-105 cursor-default
                                    ${d.severity === 'HIGH'
                                        ? 'bg-risk-high/10 text-risk-high border-risk-high/30 shadow-[0_0_15px_-5px] shadow-risk-high/50'
                                        : 'bg-risk-moderate/10 text-risk-moderate border-risk-moderate/30'
                                    }`}
                            >
                                <span className="opacity-60 font-mono">{d.timestamp}s</span>
                                <span className="w-1 h-1 rounded-full bg-current" />
                                <span className="uppercase tracking-tight">{d.flag}</span>
                            </div>
                        ))}
                        {data.filter(d => d.flag).length === 0 && (
                            <span className="text-[10px] text-surface-500 italic mt-2">
                                No significant anomalies detected in timeline
                            </span>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function LegendItem({ color, label }) {
    return (
        <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-[10px] font-bold text-surface-400 uppercase tracking-tight">{label}</span>
        </div>
    );
}
