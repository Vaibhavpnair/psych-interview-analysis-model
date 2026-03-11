import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

/**
 * Progressive disclosure section — click to expand/collapse content.
 * Used to hide advanced metrics, detailed data tables, and raw output
 * behind an expandable header to keep the UI clean.
 */
export default function CollapsibleSection({
    title,
    subtitle,
    icon: Icon,
    children,
    defaultOpen = false,
    badge,
    className = '',
}) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className={`card-clinical overflow-hidden ${className}`}>
            {/* Clickable header */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-3 px-5 py-4 text-left
                           hover:bg-surface-warm/50 transition-colors duration-150
                           focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-inset"
                aria-expanded={isOpen}
                aria-controls={`collapsible-${title?.replace(/\s+/g, '-').toLowerCase()}`}
            >
                {Icon && (
                    <div className="w-8 h-8 rounded-lg bg-primary-50 flex items-center justify-center flex-shrink-0">
                        <Icon size={16} className="text-primary" />
                    </div>
                )}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-clinical-text">{title}</span>
                        {badge}
                    </div>
                    {subtitle && (
                        <p className="text-xs text-clinical-muted mt-0.5 truncate">{subtitle}</p>
                    )}
                </div>
                <ChevronDown
                    size={16}
                    className={`text-clinical-muted transition-transform duration-200 flex-shrink-0
                               ${isOpen ? 'rotate-180' : 'rotate-0'}`}
                />
            </button>

            {/* Collapsible content */}
            <div
                id={`collapsible-${title?.replace(/\s+/g, '-').toLowerCase()}`}
                className={`overflow-hidden transition-all duration-300 ease-out
                           ${isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
                role="region"
                aria-label={title}
            >
                <div className="px-5 pb-5 pt-1 border-t border-clinical-divider">
                    {children}
                </div>
            </div>
        </div>
    );
}
