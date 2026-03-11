/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: '#1B4D5C',
                    light: '#2A7A8A',
                    dark: '#133A47',
                    50: '#EEF6F8',
                    100: '#D1E8ED',
                },
                secondary: {
                    DEFAULT: '#8B7E74',
                    light: '#A89E95',
                    dark: '#6B6058',
                },
                surface: {
                    DEFAULT: '#F7F6F3',
                    warm: '#FAF9F7',
                },
                // Alternating section backgrounds — calm, clinical rhythm
                section: {
                    cream: '#F9F7F4',     // warm off-white
                    teal: '#F0F7F8',      // cool teal tint
                    stone: '#F5F3EF',     // warm stone wash
                    mist: '#F3F6F9',      // cool blue-grey mist
                    sage: '#F2F6F3',      // soft sage green tint
                    white: '#FFFFFF',     // pure white for contrast
                },
                sidebar: '#1E293B',
                accent: '#5B8A72',
                risk: {
                    low: '#6EBD8A',
                    'low-bg': '#F0F7F2',
                    moderate: '#D4A843',
                    'mod-bg': '#FBF7EE',
                    high: '#D47272',
                    'high-bg': '#FBF0F0',
                    critical: '#B83B3B',
                    'crit-bg': '#F7EDED',
                },
                clinical: {
                    text: '#1A1D23',
                    muted: '#6B7280',
                    border: '#E5E7EB',
                    divider: '#F0EFEC',
                },
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            boxShadow: {
                'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
                'card-hover': '0 4px 12px rgba(0,0,0,0.08)',
                'float': '0 1px 2px rgba(27,77,92,0.08), 0 2px 6px rgba(27,77,92,0.12), 0 4px 12px rgba(27,77,92,0.08)',
                'float-hover': '0 2px 4px rgba(27,77,92,0.10), 0 6px 14px rgba(27,77,92,0.16), 0 10px 24px rgba(27,77,92,0.10)',
                'float-active': '0 1px 2px rgba(27,77,92,0.12), 0 2px 4px rgba(27,77,92,0.08)',
                'inner-glow': 'inset 0 1px 0 rgba(255,255,255,0.05)',
            },
            borderRadius: {
                'card': '12px',
            },
            keyframes: {
                'fade-in': {
                    '0%': { opacity: '0', transform: 'translateY(6px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                'slide-up': {
                    '0%': { opacity: '0', transform: 'translateY(12px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                'pulse-soft': {
                    '0%, 100%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(1.02)' },
                },
                'pulse-ring': {
                    '0%': { transform: 'scale(0.95)', opacity: '1' },
                    '100%': { transform: 'scale(1.8)', opacity: '0' },
                },
                'shimmer': {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' },
                },
                'scale-settle': {
                    '0%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(1.015)' },
                    '100%': { transform: 'scale(1)' },
                },
                // Modal transitions
                'modal-overlay': {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                'modal-scale': {
                    '0%': { opacity: '0', transform: 'scale(0.96) translateY(8px)' },
                    '100%': { opacity: '1', transform: 'scale(1) translateY(0)' },
                },
                'modal-scale-out': {
                    '0%': { opacity: '1', transform: 'scale(1) translateY(0)' },
                    '100%': { opacity: '0', transform: 'scale(0.96) translateY(8px)' },
                },
                // Progress bar fill
                'progress-fill': {
                    '0%': { width: '0%' },
                    '100%': { width: 'var(--progress-width, 100%)' },
                },
                // Chart data reveal (clip-path wipe)
                'chart-reveal': {
                    '0%': { clipPath: 'inset(0 100% 0 0)' },
                    '100%': { clipPath: 'inset(0 0% 0 0)' },
                },
                // Number counter tick
                'number-tick': {
                    '0%': { opacity: '0', transform: 'translateY(4px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
            },
            animation: {
                'fade-in': 'fade-in 0.2s ease-in-out',
                'slide-up': 'slide-up 0.25s ease-in-out',
                'pulse-soft': 'pulse-soft 2s ease-in-out infinite',
                'pulse-ring': 'pulse-ring 1.5s ease-out infinite',
                'shimmer': 'shimmer 2s linear infinite',
                'scale-settle': 'scale-settle 0.2s ease-in-out',
                'modal-overlay': 'modal-overlay 0.15s ease-in-out',
                'modal-in': 'modal-scale 0.2s ease-in-out',
                'modal-out': 'modal-scale-out 0.15s ease-in-out forwards',
                'progress-fill': 'progress-fill 0.7s cubic-bezier(0.33, 1, 0.68, 1)',
                'chart-reveal': 'chart-reveal 0.5s ease-in-out',
                'number-tick': 'number-tick 0.15s ease-out',
            },
        },
    },
    plugins: [],
}
