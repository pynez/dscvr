// frontend/src/components/ThemeToggle.jsx
export function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={onToggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <span className="theme-toggle-icon" aria-hidden="true">
        {isDark ? "🌙" : "☀️"}
      </span>
      <span className="theme-toggle-label">
        {isDark ? "Dark" : "Light"}
      </span>
    </button>
  );
}
