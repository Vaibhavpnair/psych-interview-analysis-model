import React from 'react';
import { Shield } from 'lucide-react';

/**
 * Risk-level indicator band — horizontal strip showing clinical risk assessment.
 * Uses muted, clinical-grade colors to avoid aggressive appearance.
 *
 * Levels: low, moderate, high, critical
 */

const riskConfig = {
    low: {
        bar: 'bg-risk-low',
        bg: 'bg-risk-low-bg',
        text: 'text-risk-low',
        label: 'Low Risk',
        width: '25%',
    },
    moderate: {
        bar: 'bg-risk-moderate',
        bg: 'bg-risk-mod-bg',
        text: 'text-risk-moderate',
        label: 'Moderate',
        width: '50%',
    },
    high: {
        bar: 'bg-risk-high',
        bg: 'bg-risk-high-bg',
        text: 'text-risk-high',
        label: 'Elevated Risk',
        width: '75%',
    },
    critical: {
        bar: 'bg-risk-critical',
        bg: 'bg-risk-crit-bg',
        text: 'text-risk-critical',
        label: 'Critical',
        width: '100%',
    },
};

export function getRiskLevel(value, thresholds = { low: 0.3, moderate: 0.5, high: 0.7 }) {
    const abs = Math.abs(value);
    if (abs >= thresholds.high) return 'high';
    if (abs >= thresholds.moderate) return 'moderate';
    return 'low';
}

export default function RiskBand({ level = 'low', label, className = '' }) {
    const config = riskConfig[level] || riskConfig.low;
    const displayLabel = label || config.label;

    return (
        <div
            className={`${config.bg} rounded-lg px-4 py-3 flex items-center gap-3 ${className}`}
            role="status"
            aria-label={`Risk level: ${displayLabel}`}
        >
            <Shield size={16} className={config.text} />
            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1.5">
                    <span className={`text-xs font-semibold ${config.text}`}>
                        {displayLabel}
                    </span>
                    <span className="text-[10px] font-mono text-clinical-muted">
                        Clinical Indicator
                    </span>
                </div>
                <div className="w-full h-1.5 bg-white/60 rounded-full overflow-hidden">
                    <div
                        className={`h-full ${config.bar} rounded-full animate-progress-fill`}
                        style={{ '--progress-width': config.width, width: config.width }}
                    />
                </div>
            </div>
        </div>
    );
}
