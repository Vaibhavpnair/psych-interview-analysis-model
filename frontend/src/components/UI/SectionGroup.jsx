import React from 'react';

/**
 * SectionGroup — visual hierarchy grouping with label and optional description.
 * Used to separate logical groups of content within a panel.
 */
export default function SectionGroup({ label, description, children, className = '' }) {
    return (
        <section className={className} aria-label={label}>
            <div className="flex items-center gap-3 mb-4">
                <div className="h-px flex-1 bg-clinical-divider" />
                <span className="text-[10px] font-semibold text-clinical-muted uppercase tracking-widest flex-shrink-0">
                    {label}
                </span>
                <div className="h-px flex-1 bg-clinical-divider" />
            </div>
            {description && (
                <p className="text-xs text-clinical-muted mb-4 text-center">{description}</p>
            )}
            <div>{children}</div>
        </section>
    );
}
