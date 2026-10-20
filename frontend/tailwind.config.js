/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0D1117',
        surface: '#161B22',
        surfaceHover: '#1c2433',
        border: '#21262D',
        primary: {
          DEFAULT: '#4F8EF7',
          hover: '#3a6fd8',
          light: '#58A6FF',
        },
        success: '#3FB950',
        warning: '#D29922',
        danger: '#F85149',
        muted: '#8B949E',
        text: '#E6EDF3',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
