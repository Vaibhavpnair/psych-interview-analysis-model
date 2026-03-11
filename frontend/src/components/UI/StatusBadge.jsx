import React from 'react';

const levelConfig = {
    low: {
        bg: 'bg-risk-low-bg',
        text: 'text-risk-low',
        dot: 'bg-risk-low',
        label: 'Low',
    },
    moderate: {
        bg: 'bg-risk-mod-bg',
        text: 'text-risk-moderate',
        dot: 'bg-risk-moderate',
        label: 'Moderate',
    },
    high: {
        bg: 'bg-risk-high-bg',
        text: 'text-risk-high',
        dot: 'bg-risk-high',
        label: 'High',
    },
    critical: {
        bg: 'bg-risk-crit-bg',
        text: 'text-risk-critical',
        dot: 'bg-risk-critical',
        label: 'Critical',
    },
    neutral: {
        bg: 'bg-surface',
        text: 'text-clinical-muted',
        dot: 'bg-clinical-muted',
        label: 'Neutral',
    },
    positive: {
        bg: 'bg-risk-low-bg',
        text: 'text-risk-low',
        dot: 'bg-accent',
        label: 'Positive',
    },
    negative: {
        bg: 'bg-risk-high-bg',
        text: 'text-risk-high',
        dot: 'bg-risk-high',
        label: 'Negative',
    },
};

export default function StatusBadge({ level, label, pulse = false }) {
    const config = levelConfig[level] || levelConfig.neutral;
    const displayLabel = label || config.label;

    return (
        <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}
            role="status"
            aria-label={`Status: ${displayLabel}`}
        >
            <span className="relative flex h-1.5 w-1.5">
                {pulse && (
                    <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.dot} opacity-75`} />
                )}
                <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${config.dot}`} />
            </span>
            {displayLabel}
        </span>
    );
}
