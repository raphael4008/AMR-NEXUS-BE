/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'SF Pro Text', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      colors: {
        dark: {
          DEFAULT: '#0A0E17',
          bg: '#0A0E17',
          card: '#1A1F2E',
          cardHover: '#1F2538',
          border: '#2A2F3F',
          elevated: '#121724',
        },
        light: {
          DEFAULT: '#F8FAFC',
          bg: '#F8FAFC',
          card: '#FFFFFF',
          cardHover: '#F1F5F9',
          border: '#E2E8F0',
          elevated: '#FFFFFF',
        },
        accent: {
          cyan: '#00F0FF',
          cyanDark: '#00C4D6',
          red: '#FF5A6E',
          redDark: '#E64559',
          green: '#00FF88',
          greenDark: '#00D973',
          gold: '#FFD966',
          goldDark: '#E6C452',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#F1F3F9',
          muted: '#8A94A8',
          disabled: '#5A6478',
        },
      },
      fontSize: {
        'display': ['48px', { lineHeight: '1.2', fontWeight: '700', letterSpacing: '-0.02em' }],
        'display-sm': ['36px', { lineHeight: '1.2', fontWeight: '700', letterSpacing: '-0.02em' }],
        'card-title': ['14px', { lineHeight: '1.4', fontWeight: '600', letterSpacing: '0.01em' }],
        'body': ['13px', { lineHeight: '1.5', fontWeight: '400' }],
        'caption': ['11px', { lineHeight: '1.4', fontWeight: '500', letterSpacing: '0.01em' }],
      },
      borderRadius: {
        'card': '16px',
        'button': '12px',
        'input': '12px',
      },
      boxShadow: {
        'card': '0 8px 20px rgba(0, 0, 0, 0.4)',
        'card-hover': '0 12px 28px rgba(0, 0, 0, 0.5)',
        'glow-cyan': '0 0 12px rgba(0, 240, 255, 0.3)',
        'glow-green': '0 0 12px rgba(0, 255, 136, 0.3)',
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '24px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        glowPulse: {
          '0%, 100%': { opacity: 1, boxShadow: '0 0 4px rgba(0, 240, 255, 0.3)' },
          '50%': { opacity: 0.7, boxShadow: '0 0 12px rgba(0, 240, 255, 0.6)' },
        },
      },
    },
  },
  plugins: [],
}
