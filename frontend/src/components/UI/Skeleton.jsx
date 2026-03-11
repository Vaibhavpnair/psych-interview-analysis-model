import React from 'react';

/**
 * Skeleton loading placeholder with shimmer animation.
 * Use to show content loading state before data arrives.
 *
 * Variants:
 *  - text: single line of text
 *  - title: wider/taller text line
 *  - card: full card-shaped block
 *  - circle: circular avatar/icon placeholder
 *  - metric: metric card shape (used in result panels)
 */

function SkeletonLine({ className = '', width = 'w-full' }) {
    return (
        <div
            className={`h-3 rounded-md bg-clinical-border/60 animate-pulse ${width} ${className}`}
            role="presentation"
            aria-hidden="true"
        />
    );
}

function SkeletonBlock({ className = '', height = 'h-20' }) {
    return (
        <div
            className={`rounded-card bg-clinical-border/40 animate-pulse ${height} ${className}`}
            role="presentation"
            aria-hidden="true"
        />
    );
}

export function SkeletonMetricGrid({ count = 5 }) {
    return (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4" role="status" aria-label="Loading results">
            {Array.from({ length: count }).map((_, i) => (
                <div
                    key={i}
                    className="card-clinical p-5 space-y-3"
                    style={{ animationDelay: `${i * 80}ms` }}
                >
                    <div className="flex items-center gap-2">
                        <div className="w-4 h-4 rounded bg-clinical-border/50 animate-pulse" />
                        <SkeletonLine width="w-20" />
                    </div>
                    <SkeletonLine width="w-16" className="h-6" />
                </div>
            ))}
            <span className="sr-only">Loading analysis results...</span>
        </div>
    );
}

export function SkeletonTextBlock({ lines = 3 }) {
    return (
        <div className="space-y-2.5" role="status" aria-label="Loading content">
            {Array.from({ length: lines }).map((_, i) => (
                <SkeletonLine
                    key={i}
                    width={i === lines - 1 ? 'w-3/5' : 'w-full'}
                    style={{ animationDelay: `${i * 60}ms` }}
                />
            ))}
            <span className="sr-only">Loading...</span>
        </div>
    );
}

export function SkeletonCard({ height = 'h-32' }) {
    return (
        <div className="card-clinical p-5 space-y-3" role="status" aria-label="Loading">
            <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-clinical-border/50 animate-pulse" />
                <div className="space-y-1.5 flex-1">
                    <SkeletonLine width="w-28" />
                    <SkeletonLine width="w-40" className="h-2" />
                </div>
            </div>
            <SkeletonBlock height={height} />
            <span className="sr-only">Loading...</span>
        </div>
    );
}

export default { SkeletonMetricGrid, SkeletonTextBlock, SkeletonCard };
