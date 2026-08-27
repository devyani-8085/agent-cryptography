/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#09090b',
          900: '#121214',
          800: '#1a1a1e',
          700: '#252529',
          600: '#3f3f46'
        },
        orange: {
          500: '#ff6b00',
          400: '#ff8c33',
          300: '#ffa666',
        }
      },
      boxShadow: {
        'glow-orange': '0 0 15px rgba(255, 107, 0, 0.25)',
        'glow-orange-lg': '0 0 25px rgba(255, 107, 0, 0.4)',
      }
    },
  },
  plugins: [],
}
