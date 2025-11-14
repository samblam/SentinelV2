/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Tactical color palette
        tactical: {
          bg: '#0a0e1a',
          surface: '#141824',
          border: '#1f2937',
          text: '#e5e7eb',
          textMuted: '#9ca3af',
          primary: '#3b82f6',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#06b6d4',
        },
        // Node status colors
        status: {
          online: '#10b981',
          offline: '#6b7280',
          covert: '#3b82f6',  // Backend uses 'covert' status
        },
        // Confidence colors
        confidence: {
          high: '#ef4444',
          medium: '#f59e0b',
          low: '#fbbf24',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}

