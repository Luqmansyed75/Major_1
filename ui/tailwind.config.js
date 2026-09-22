/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7', // Primary Stitch Brand Sky Blue
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        surface: {
          canvas: '#f8fafc',
          tint: '#f0f9ff',
          card: '#ffffff',
          dim: '#f1f5f9',
          elevated: 'rgba(255, 255, 255, 0.90)',
        },
        ink: {
          title: '#0f172a',
          body: '#334155',
          muted: '#64748b',
          faint: '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      boxShadow: {
        'stitch-card': '0 1px 3px rgba(15, 23, 42, 0.03), 0 4px 20px rgba(2, 132, 199, 0.05)',
        'stitch-hover': '0 6px 24px rgba(2, 132, 199, 0.09), 0 1px 2px rgba(15, 23, 42, 0.04)',
        'stitch-frosted': '0 12px 36px rgba(2, 132, 199, 0.12), 0 2px 6px rgba(15, 23, 42, 0.04)',
      },
      borderRadius: {
        'stitch': '12px',
        'stitch-lg': '18px',
      }
    },
  },
  plugins: [],
}
