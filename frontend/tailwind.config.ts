import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#05060f',
        panel: '#0c0e1e',
        border: '#20223a',
        blue: '#6d5bff',
        cyan: '#b48cff',
        steel: '#9396b8',
        steelDim: '#5b5f80',
        text: '#f1f0fb',
        red: '#ff5577',
        green: '#2ee6a8',
      },
      fontFamily: {
        display: ['var(--font-chakra)', 'sans-serif'],
        body: ['var(--font-inter)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      boxShadow: {
        glow: '0 8px 40px -8px rgba(109, 91, 255, 0.35)',
      },
      keyframes: {
        riseIn: {
          from: { opacity: '0', transform: 'translateY(14px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.45', transform: 'scale(0.82)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
      },
      animation: {
        riseIn: 'riseIn 0.7s ease forwards',
        pulseDot: 'pulseDot 2.4s ease-in-out infinite',
        blink: 'blink 2s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

export default config;
