/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core background layers
        app: {
          bg: "var(--app-bg)",
          fg: "var(--app-fg)",
          subtle: "var(--app-subtle)",
          border: "var(--app-border)"
        },
        accent: {
          DEFAULT: "var(--accent)",
          fg: "var(--accent-fg)",
        },
      },
    },
  },
  plugins: [],
};