import React from 'react';
import { Loader2 } from 'lucide-react';

const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    ghost: 'btn-ghost',
};

/**
 * Button with floating elevation, layered shadows, and smooth hover transitions.
 *
 * --- TailwindCSS approach (current) ---
 * Uses custom shadow tokens defined in tailwind.config.js
 * with transition-all for smooth interpolation between states.
 *
 * --- Framer Motion alternative ---
 * import { motion } from 'framer-motion';
 * <motion.button
 *   whileHover={{ y: -2, scale: 1.015, boxShadow: '0 6px 14px rgba(27,77,92,0.16), 0 10px 24px rgba(27,77,92,0.10)' }}
 *   whileTap={{ y: 0, scale: 0.98, boxShadow: '0 1px 2px rgba(27,77,92,0.12)' }}
 *   transition={{ type: 'spring', stiffness: 400, damping: 25 }}
 * >
 *
 * --- CSS-only fallback ---
 * .btn-float {
 *   box-shadow: 0 1px 2px rgba(27,77,92,0.08), 0 2px 6px rgba(27,77,92,0.12), 0 4px 12px rgba(27,77,92,0.08);
 *   transition: transform 0.2s cubic-bezier(0.33, 1, 0.68, 1), box-shadow 0.2s cubic-bezier(0.33, 1, 0.68, 1);
 * }
 * .btn-float:hover {
 *   transform: translateY(-2px) scale(1.015);
 *   box-shadow: 0 2px 4px rgba(27,77,92,0.10), 0 6px 14px rgba(27,77,92,0.16), 0 10px 24px rgba(27,77,92,0.10);
 * }
 * .btn-float:active {
 *   transform: translateY(0) scale(0.98);
 *   box-shadow: 0 1px 2px rgba(27,77,92,0.12), 0 2px 4px rgba(27,77,92,0.08);
 * }
 *
 * --- Accessibility ---
 * • Uses minimum 4.5:1 contrast ratio (white text on #1B4D5C = 6.2:1)
 * • Respects prefers-reduced-motion via Tailwind's motion-reduce utilities
 * • Disabled state removes all hover transforms
 * • Focus-visible ring for keyboard navigation
 */
export default function Button({
    children,
    variant = 'primary',
    loading = false,
    disabled = false,
    className = '',
    ...props
}) {
    return (
        <button
            className={`${variants[variant]} inline-flex items-center justify-center gap-2
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2
                motion-reduce:transform-none motion-reduce:transition-none
                ${className}`}
            disabled={disabled || loading}
            {...props}
        >
            {loading && <Loader2 size={16} className="animate-spin" />}
            {children}
        </button>
    );
}
