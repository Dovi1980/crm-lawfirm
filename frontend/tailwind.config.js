/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enables class-based dark mode
  theme: {
    extend: {
      colors: {
        legal: {
          navy: {
            deep: '#0A1128',
            medium: '#1C2541',
            light: '#3A506B',
            slate: '#1E293B',
          },
          gold: {
            DEFAULT: '#C5A880',
            dark: '#B08E5B',
            light: '#DFCFB7',
            metallic: '#D4AF37',
          },
          charcoal: {
            DEFAULT: '#1E1E24',
            dark: '#121214',
            medium: '#2A2A35',
            light: '#64748B',
          },
          cream: {
            DEFAULT: '#F8F9FA',
            dark: '#F1F3F5',
            soft: '#FCFBF7',
          }
        }
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'sans-serif'],
        serif: ['"Playfair Display"', 'serif'],
      },
      boxShadow: {
        'premium': '0 4px 20px -2px rgba(10, 17, 40, 0.05), 0 2px 10px -1px rgba(197, 168, 128, 0.05)',
        'premium-lg': '0 10px 30px -5px rgba(10, 17, 40, 0.08), 0 4px 15px -2px rgba(197, 168, 128, 0.08)',
        'gold-glow': '0 0 15px rgba(212, 175, 55, 0.15)',
      }
    },
  },
  plugins: [],
}
