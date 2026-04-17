/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg:      "var(--bg)",
          surface: "var(--bg-surface)",
          card:    "var(--bg-card)",
          subtle:  "var(--text-2)",
          border:  "var(--border)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          soft:    "var(--accent-soft)",
        },
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "SF Pro Text", "Helvetica Neue", "Arial", "sans-serif"],
      },
      borderRadius: {
        sm:   "var(--radius-sm)",
        md:   "var(--radius-md)",
        lg:   "var(--radius-lg)",
        xl:   "var(--radius-xl)",
        full: "var(--radius-full)",
      },
    },
  },
  plugins: [],
};
