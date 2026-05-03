/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#01696f', hover: '#0c4e54', light: '#cedcd8', dark: '#4f98a3' },
        surface: { DEFAULT: '#f9f8f5', 2: '#fbfbf9', off: '#edeae5', dark: '#1c1b19', 'dark-2': '#201f1d', 'dark-off': '#22211f' },
        border: { DEFAULT: '#d4d1ca', dark: '#393836' },
        success: { DEFAULT: '#437a22', light: '#d4dfcc', dark: '#6daa45' },
        danger: { DEFAULT: '#a12c7b', light: '#e0ced7', dark: '#d163a7' },
        warning: { DEFAULT: '#964219', light: '#ddcfc6', dark: '#bb653b' },
      },
      fontFamily: {
        body: ['Inter', 'sans-serif'],
        display: ['Syne', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
