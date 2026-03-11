import React from 'react';

/**
 * Section — full-width background block with consistent padding.
 * Used to create alternating background rhythm between content areas.
 *
 * Layout structure (within each panel):
 *   <Section bg="cream">  — Header + Upload
 *   <Section bg="white">  — Key Results
 *   <Section bg="teal">   — Advanced Data
 *   <Section bg="stone">  — Raw Data
 *
 * Background system:
 *   cream  → #F9F7F4  (warm off-white)
 *   teal   → #F0F7F8  (cool teal tint)
 *   stone  → #F5F3EF  (warm stone wash)
 *   mist   → #F3F6F9  (cool blue-grey)
 *   sage   → #F2F6F3  (soft sage green)
 *   white  → #FFFFFF  (pure white)
 *
 * Subtle gradient option:
 *   Pass gradient={true} for a very soft top-to-bottom fade
 *   within the section (e.g., cream to slightly lighter).
 */

const bgMap = {
    cream: 'bg-section-cream',
    teal: 'bg-section-teal',
    stone: 'bg-section-stone',
    mist: 'bg-section-mist',
    sage: 'bg-section-sage',
    white: 'bg-section-white',
    surface: 'bg-surface',
};

const gradientMap = {
    cream: 'from-section-cream to-[#FDFCFA]',
    teal: 'from-section-teal to-[#F7FBFC]',
    stone: 'from-section-stone to-[#FAF9F6]',
    mist: 'from-section-mist to-[#F8FAFC]',
    sage: 'from-section-sage to-[#F8FAF8]',
    white: 'from-white to-surface',
};

export default function Section({
    bg = 'white',
    gradient = false,
    children,
    className = '',
    padded = true,
    id,
    ariaLabel,
}) {
    const bgClass = gradient
        ? `bg-gradient-to-b ${gradientMap[bg] || gradientMap.white}`
        : bgMap[bg] || bgMap.white;

    return (
        <section
            className={`
                ${bgClass}
                ${padded ? 'px-8 py-10 sm:px-10 sm:py-12 lg:px-12 lg:py-14' : ''}
                transition-colors duration-300
                ${className}
            `.trim()}
            id={id}
            aria-label={ariaLabel}
        >
            <div className="max-w-5xl">
                {children}
            </div>
        </section>
    );
}

/**
 * SectionDivider — subtle visual separator between sections.
 * Renders a thin line or a fade-gradient strip.
 */
export function SectionDivider({ variant = 'line' }) {
    if (variant === 'fade') {
        return (
            <div className="h-px bg-gradient-to-r from-transparent via-clinical-border to-transparent" />
        );
    }
    return <div className="h-px bg-clinical-divider" />;
}
