/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
        "./src/index.css",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                // Clinical color palette (Indigo)
                primary: {
                    50: '#eef2ff',
                    100: '#e0e7ff',
                    200: '#c7d2fe',
                    300: '#a5b4fc',
                    400: '#818cf8',
                    500: '#6366f1',
                    600: '#4f46e5',
                    700: '#4338ca',
                    800: '#3730a3',
                    900: '#312e81',
                    950: '#1e1b4b',
                },
                // Risk-based colors
                risk: {
                    low: '#22c55e',
                    moderate: '#f59e0b',
                    high: '#ef4444',
                    critical: '#dc2626',
                },
                // Neutrals (Slate)
                surface: {
                    50: '#f8fafc',
                    100: '#f1f5f9',
                    200: '#e2e8f0',
                    300: '#cbd5e1',
                    400: '#94a3b8',
                    500: '#64748b',
                    600: '#475569',
                    700: '#334155',
                    800: '#1e293b',
                    900: '#0f172a',
                    950: '#020617',
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            boxShadow: {
                'floating': '0 8px 32px rgba(0, 0, 0, 0.3)',
            },
        },
    },
    safelist: [
        {
            pattern: /(bg|text|border|shadow|from|to)-(primary|surface|risk)-(50|100|200|300|400|500|600|700|800|900|950|low|moderate|high|critical)/,
            variants: ['hover', 'focus', 'active', 'group-hover'],
        },
    ],
    plugins: [],
};
