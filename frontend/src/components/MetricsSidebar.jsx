/**
 * MetricsSidebar — Zone D of the dashboard.
 * Speech metrics radar chart, sentiment bar chart, engagement stats.
 */
import {
    RadarChart, PolarGrid, PolarAngleAxis, Radar,
    BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer,
} from 'recharts';

export default function MetricsSidebar({ features, contradictions = [] }) {
    const speechMetrics = features?.speech || {};
    const nlpMetrics = features?.nlp || {};

    // Radar chart data: Actual vs Clinical Norms (shadow area)
    const radarData = [
        { metric: 'WPM', actual: Math.min((speechMetrics.speech_rate_wpm || 0) / 180, 1) * 100, norm: 70 },
        { metric: 'Stability', actual: 100 - ((speechMetrics.pitch_std_dev || 0) / 50 * 100), norm: 80 },
        { metric: 'Fluent', actual: 100 - (Math.min((speechMetrics.filler_word_rate || 0) / 15, 1) * 100), norm: 90 },
        { metric: 'Latency', actual: 100 - (Math.min((speechMetrics.response_latency_ms || 0) / 4000, 1) * 100), norm: 75 },
        { metric: 'Flow', actual: (1 - (speechMetrics.silence_ratio || 0)) * 100, norm: 85 },
    ];

    return (
        <div className="space-y-6 animate-in" style={{ animationDelay: '0.2s' }}>
            {/* Speech Analysis Radar */}
            <div className="card-floating bg-primary-900/10 border-primary-500/20">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-primary-400 mb-6">
                    Clinical Speech Radar
                </h3>
                <div className="h-64 -mx-4">
                    <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={radarData}>
                            <PolarGrid stroke="#334155" />
                            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: '#94a3b8', fontWeight: 600 }} />
                            {/* Norm Shadow */}
                            <Radar
                                name="Normal Range"
                                dataKey="norm"
                                stroke="transparent"
                                fill="#475569"
                                fillOpacity={0.15}
                            />
                            {/* Patient Actual */}
                            <Radar
                                name="Patient"
                                dataKey="actual"
                                stroke="#6366f1"
                                strokeWidth={2}
                                fill="#6366f1"
                                fillOpacity={0.4}
                            />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Linguistic Markers */}
            <div className="card-floating">
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-surface-400 mb-6">
                    Linguistic Markers
                </h3>
                <div className="grid grid-cols-2 gap-4">
                    <MarkerBox
                        label="Self-Focus"
                        value={`${((nlpMetrics.pronouns?.first_person_ratio || 0) * 100).toFixed(1)}%`}
                        desc="Rumination index"
                    />
                    <MarkerBox
                        label="Absolutist"
                        value={nlpMetrics.lexical?.absolutist_count || 0}
                        desc="Cognitive rigidity"
                    />
                    <MarkerBox
                        label="Avoidance"
                        value={nlpMetrics.lexical?.avoidance_count || 0}
                        desc="Defensive markers"
                    />
                    <MarkerBox
                        label="Filler Rate"
                        value={`${(speechMetrics.filler_word_rate || 0).toFixed(1)}/m`}
                        desc="Processing load"
                    />
                </div>
            </div>

            {/* Cross-Modal Contradictions */}
            <div className={`card-floating border-l-4 transition-all duration-500 ${contradictions.length > 0 ? 'border-l-risk-moderate bg-risk-moderate/5' : 'border-l-surface-800'
                }`}>
                <h3 className="text-[10px] font-bold uppercase tracking-widest text-surface-400 mb-6">
                    Contradiction Summary
                </h3>
                {contradictions.length > 0 ? (
                    <div className="space-y-4">
                        {contradictions.map((c, i) => (
                            <div key={i} className="group cursor-help">
                                <div className="flex items-start gap-3">
                                    <span className="text-risk-moderate text-sm">⚠️</span>
                                    <div>
                                        <p className="text-xs font-bold text-white mb-1 group-hover:text-risk-moderate transition-colors">
                                            {c.rule.replace(/_/g, ' ')}
                                        </p>
                                        <p className="text-[10px] text-surface-400 leading-normal">
                                            {c.note}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-4">
                        <span className="text-xs text-surface-500 italic">No cross-modal mismatches found</span>
                    </div>
                )}
            </div>
        </div>
    );
}

function MarkerBox({ label, value, desc }) {
    return (
        <div className="bg-surface-800/50 p-3 rounded-lg border border-surface-700/50 hover:border-surface-600 transition-colors">
            <p className="text-[10px] font-bold text-surface-400 uppercase tracking-tighter mb-1">{label}</p>
            <p className="text-lg font-mono font-bold text-white mb-1">{value}</p>
            <p className="text-[9px] text-surface-200/40 leading-tight">{desc}</p>
        </div>
    );
}
