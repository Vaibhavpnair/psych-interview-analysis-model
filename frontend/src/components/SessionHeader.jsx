/**
 * SessionHeader — Zone A of the dashboard.
 * Displays patient info, risk band, and AI summary.
 */
import RiskBadge from './RiskBadge';

export default function SessionHeader({ session }) {
    const {
        risk_band = 'Low Concern',
        risk_score = 0,
        confidence = 0.85,
        summary = 'No analysis available yet.',
        duration_seconds = 0,
        word_count = 0,
    } = session || {};

    const formatDuration = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    };

    return (
        <div className="card-floating border-l-4 border-l-primary-500 bg-gradient-to-r from-primary-950/20 to-transparent">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-8">
                <div className="space-y-2">
                    <div className="flex items-center gap-3">
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-primary-500 bg-primary-500/10 px-2 py-1 rounded">
                            Session Analysis
                        </span>
                        <span className="text-[10px] font-bold text-surface-500">
                            ID: {session?.id?.slice(0, 8) || 'PENDING'}
                        </span>
                    </div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">Clinical Behavioral Report</h2>
                    <div className="flex items-center gap-5 text-xs font-medium text-surface-400">
                        <div className="flex items-center gap-2">
                            <span className="opacity-50 text-base">⏱</span>
                            <span>{formatDuration(duration_seconds)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="opacity-50 text-base">💬</span>
                            <span>{word_count} words processed</span>
                        </div>
                    </div>
                </div>
                <RiskBadge band={risk_band} score={risk_score} confidence={confidence} />
            </div>

            <div className="relative">
                <div className="absolute -left-6 top-0 bottom-0 w-1 bg-primary-500/20 rounded-full" />
                <h4 className="text-[10px] font-black uppercase tracking-widest text-surface-500 mb-3">AI Decision Support Summary</h4>
                <p className="text-base text-surface-100 leading-relaxed font-medium max-w-4xl">
                    {summary}
                </p>
            </div>
        </div>
    );
}
