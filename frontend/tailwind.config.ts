import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#04060c',
        panel: '#0a0f1c',
        border: '#1c2740',
        blue: '#2d6bff',
        cyan: '#00e8ff',
        steel: '#7c8da6',
        steelDim: '#4a5872',
        text: '#e8f0ff',
        red: '#ff3a55',
        green: '#20e3a2',
      },
      fontFamily: {
        display: ['var(--font-chakra)', 'sans-serif'],
        body: ['var(--font-inter)', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
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
