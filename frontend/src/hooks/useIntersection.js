import { useEffect, useRef, useState } from 'react';

/**
 * useIntersection — fires once when element enters viewport.
 * Replaces inline IntersectionObserver in AnimatedPrimitives.
 *
 * @param {{ threshold?: number }} options
 * @returns {[React.RefObject, boolean]}
 *
 * Usage:
 *   const [ref, isVisible] = useIntersection({ threshold: 0.3 });
 *   return <div ref={ref} className={isVisible ? 'animate-fade-in' : 'opacity-0'} />;
 */
export default function useIntersection({ threshold = 0.3 } = {}) {
    const ref = useRef(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;

        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setVisible(true);
                    observer.disconnect(); // fire-once
                }
            },
            { threshold }
        );

        observer.observe(el);
        return () => observer.disconnect();
    }, [threshold]);

    return [ref, visible];
}
