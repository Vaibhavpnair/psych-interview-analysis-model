import React, { useEffect, useRef, useState } from 'react';

/**
 * AnimatedProgress — progress bar with smooth fill animation.
 * Used for confidence bars, polarity meters, and gauge fills.
 *
 * Animates from 0 → target width using CSS `progress-fill` keyframe.
 * Triggers animation only when element enters viewport (IntersectionObserver).
 *
 * ── Framer Motion alternative ──
 * <motion.div
 *   initial={{ width: 0 }}
 *   animate={{ width: `${percentage}%` }}
 *   transition={{ duration: 0.7, ease: [0.33, 1, 0.68, 1] }}
 * />
 */
export function AnimatedBar({
    percentage = 0,
    color = 'bg-primary',
    height = 'h-2',
    className = '',
    label,
}) {
    const ref = useRef(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const observer = new IntersectionObserver(
            ([entry]) => { if (entry.isIntersecting) setVisible(true); },
            { threshold: 0.3 }
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    return (
        <div
            ref={ref}
            className={`w-full ${height} bg-surface rounded-full overflow-hidden ${className}`}
            role="progressbar"
            aria-valuenow={Math.round(percentage)}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={label}
        >
            <div
                className={`${height} ${color} rounded-full
                           ${visible ? 'animate-progress-fill' : 'w-0'}`}
                style={{ '--progress-width': `${Math.max(1, percentage)}%`, width: visible ? `${percentage}%` : '0%' }}
            />
        </div>
    );
}

/**
 * AnimatedNumber — counter that ticks up with a subtle animation.
 * Uses CSS class `animate-number-tick` for the entrance.
 */
export function AnimatedNumber({
    value,
    suffix = '',
    className = 'text-2xl font-semibold text-clinical-text',
}) {
    const [displayed, setDisplayed] = useState(null);

    useEffect(() => {
        setDisplayed(null);
        // Brief delay then show with tick animation
        const timer = setTimeout(() => setDisplayed(value), 50);
        return () => clearTimeout(timer);
    }, [value]);

    if (displayed === null) return <span className={className}>—</span>;

    return (
        <span className={`${className} inline-block animate-number-tick`} key={value}>
            {value}{suffix}
        </span>
    );
}

/**
 * ChartReveal — wrapper that clips content and reveals with a left-to-right wipe.
 * Use around chart/graph containers for smooth load-in.
 */
export function ChartReveal({ children, delay = 0, className = '' }) {
    const ref = useRef(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const observer = new IntersectionObserver(
            ([entry]) => { if (entry.isIntersecting) setVisible(true); },
            { threshold: 0.2 }
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    return (
        <div
            ref={ref}
            className={`${visible ? 'animate-chart-reveal' : 'opacity-0'} ${className}`}
            style={{ animationDelay: `${delay}ms` }}
        >
            {children}
        </div>
    );
}
