/**
 * RiskBadge — Color-coded risk band indicator.
 * Displays Low/Moderate/High/Critical concern levels.
 */

const BAND_CONFIG = {
    'Low Concern': {
        container: 'bg-risk-low/10 text-risk-low border-risk-low/20',
        ring: 'text-risk-low',
        icon: '✓',
    },
    'Moderate Concern': {
        container: 'bg-risk-moderate/10 text-risk-moderate border-risk-moderate/20',
        ring: 'text-risk-moderate',
        icon: '⚠',
    },
    'High Concern': {
        container: 'bg-risk-high/10 text-risk-high border-risk-high/20',
        ring: 'text-risk-high',
        icon: '⚡',
    },
    'Critical': {
        container: 'bg-risk-critical/10 text-risk-critical border-risk-critical/20 animate-pulse',
        ring: 'text-risk-critical',
        icon: '🚨',
    },
};

export default function RiskBadge({ band = 'Low Concern', score, confidence = 0.85 }) {
    const config = BAND_CONFIG[band] || BAND_CONFIG['Low Concern'];

    return (
        <div className="flex flex-col items-end gap-2">
            {/* Risk Band Badge */}
            <div className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold border ${config.container} backdrop-blur-sm shadow-sm transition-all duration-300`}>
                <span className="mr-2 text-sm">{config.icon}</span>
                <span className="tracking-wide uppercase font-black">{band}</span>
                {score !== undefined && (
                    <span className="ml-2 border-l border-current/20 pl-2 opacity-80">
                        {(score * 100).toFixed(0)}%
                    </span>
                )}
            </div>

            {/* Confidence Indicator */}
            <div className="flex items-center gap-2 group cursor-help" title="AI Confidence Score">
                <div className="h-1.5 w-24 bg-surface-800 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${config.ring} bg-current transition-all duration-1000 ease-out`}
                        style={{ width: `${confidence * 100}%` }}
                    />
                </div>
                <span className="text-[10px] font-bold text-surface-200/50 uppercase tracking-tighter">
                    {Math.round(confidence * 100)}% Confidence
                </span>
            </div>
        </div>
    );
}
