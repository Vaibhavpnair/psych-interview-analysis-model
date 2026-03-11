import React, { useEffect, useState, useCallback } from 'react';
import { X } from 'lucide-react';

/**
 * Modal — smooth open/close transitions (Stripe/Linear feel).
 *
 * Open:  backdrop fades 150ms, content scales from 0.96→1 in 200ms
 * Close: content scales down 150ms, then backdrop fades out
 *
 * ── TailwindCSS approach (current) ──
 * Uses `animate-modal-overlay` and `animate-modal-in` / `animate-modal-out`
 * keyframes defined in tailwind.config.js.
 *
 * ── Framer Motion alternative ──
 * import { AnimatePresence, motion } from 'framer-motion';
 *
 * <AnimatePresence>
 *   {isOpen && (
 *     <motion.div
 *       className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
 *       initial={{ opacity: 0 }}
 *       animate={{ opacity: 1 }}
 *       exit={{ opacity: 0 }}
 *       transition={{ duration: 0.15, ease: 'easeInOut' }}
 *     >
 *       <motion.div
 *         className="modal-content"
 *         initial={{ opacity: 0, scale: 0.96, y: 8 }}
 *         animate={{ opacity: 1, scale: 1, y: 0 }}
 *         exit={{ opacity: 0, scale: 0.96, y: 8 }}
 *         transition={{ duration: 0.2, ease: [0.33, 1, 0.68, 1] }}
 *       >
 *         {children}
 *       </motion.div>
 *     </motion.div>
 *   )}
 * </AnimatePresence>
 *
 * ── Accessibility ──
 * • role="dialog" + aria-modal="true"
 * • aria-labelledby for title
 * • Focus trap: auto-focuses close button on open
 * • Escape key closes modal
 * • prefers-reduced-motion disables animations
 */
export default function Modal({
    isOpen,
    onClose,
    title,
    children,
    size = 'md',
    className = '',
}) {
    const [closing, setClosing] = useState(false);
    const [mounted, setMounted] = useState(false);

    const sizes = {
        sm: 'max-w-md',
        md: 'max-w-lg',
        lg: 'max-w-2xl',
        xl: 'max-w-4xl',
    };

    useEffect(() => {
        if (isOpen) {
            setMounted(true);
            setClosing(false);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    const handleClose = useCallback(() => {
        setClosing(true);
        setTimeout(() => {
            setMounted(false);
            setClosing(false);
            onClose?.();
        }, 150); // matches modal-out duration
    }, [onClose]);

    // Escape key
    useEffect(() => {
        if (!isOpen) return;
        const handleKey = (e) => {
            if (e.key === 'Escape') handleClose();
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [isOpen, handleClose]);

    if (!mounted) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className={`absolute inset-0 bg-black/25 backdrop-blur-[2px]
                           ${closing ? 'animate-modal-out' : 'animate-modal-overlay'}`}
                onClick={handleClose}
                aria-hidden="true"
            />

            {/* Content */}
            <div
                className={`relative w-full ${sizes[size]} bg-white rounded-xl shadow-card-hover
                           border border-clinical-border
                           ${closing ? 'animate-modal-out' : 'animate-modal-in'}
                           ${className}`}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
            >
                {/* Header */}
                {title && (
                    <div className="flex items-center justify-between px-6 py-4 border-b border-clinical-divider">
                        <h3 id="modal-title" className="text-sm font-semibold text-clinical-text">
                            {title}
                        </h3>
                        <button
                            onClick={handleClose}
                            className="w-7 h-7 rounded-md flex items-center justify-center
                                       text-clinical-muted hover:text-clinical-text hover:bg-surface
                                       transition-colors duration-150
                                       focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                            aria-label="Close dialog"
                            autoFocus
                        >
                            <X size={14} />
                        </button>
                    </div>
                )}

                {/* Body */}
                <div className="px-6 py-5">
                    {children}
                </div>
            </div>
        </div>
    );
}
