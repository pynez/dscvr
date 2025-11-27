/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#050816",
          light: "#f3f4f6",
        },
        accent: "#8b5cf6",
      },
    },
  },
  darkMode: ["class", '[data-theme="dark"]'],
  plugins: [],
}