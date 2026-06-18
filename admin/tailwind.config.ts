import type { Config } from 'tailwindcss'

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#101415',
        surface: '#101415',
        'surface-dim': '#101415',
        'surface-bright': '#363a3b',
        'surface-container-lowest': '#0b0f10',
        'surface-container-low': '#191c1e',
        'surface-container': '#1d2022',
        'surface-container-high': '#272a2c',
        'surface-container-highest': '#323537',
        'on-surface': '#e0e3e5',
        'on-surface-variant': '#c2c6d4',
        outline: '#8c909e',
        'outline-variant': '#424752',
        primary: '#acc7ff',
        'on-primary': '#002f67',
        'primary-container': '#0056b3',
        'on-primary-container': '#bbd0ff',
        secondary: '#4ae176',
        'on-secondary': '#003915',
        tertiary: '#ffb95f',
        error: '#ffb4ab',
      },
      borderRadius: {
        sm: '0.25rem',
        DEFAULT: '0.5rem',
        md: '0.75rem',
        lg: '1rem',
        xl: '1.5rem',
      },
      fontFamily: {
        headline: ['Hanken Grotesk', 'Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      maxWidth: {
        container: '1200px',
      },
      spacing: {
        gutter: '24px',
        'stack-sm': '8px',
        'stack-md': '16px',
        'stack-lg': '32px',
      },
    },
  },
} satisfies Config
