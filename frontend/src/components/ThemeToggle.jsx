// frontend/src/components/ThemeToggle.jsx
export function ThemeToggle({ theme, onToggle }) {
  const isDark = theme === "dark";

  const baseClasses = `
    inline-flex items-center gap-1.5
    rounded-full px-3 py-1
    text-[11px] font-semibold uppercase tracking-[0.16em]
    transition-colors duration-200
    focus:outline-none focus:ring-2 focus:ring-accent/60 focus:ring-offset-2 focus:ring-offset-[var(--app-bg)]
  `;

  const stateClasses = isDark
    ? `
      bg-[rgba(255,255,255,0.06)]
      border border-[rgba(255,255,255,0.18)]
      text-app-fg
      shadow-[0_8px_24px_rgba(0,0,0,0.25)]
      hover:border-[rgba(255,255,255,0.35)]
      hover:bg-[rgba(255,255,255,0.10)]
    `
    : `
      bg-[rgba(0,0,0,0.09)]
      border border-[rgba(0,0,0,0.12)]
      text-app-fg
      hover:border-[rgba(0,0,0,0.25)]
      hover:bg-[rgba(0,0,0,0.10)]
    `;

  return (
    <button
      type="button"
      onClick={onToggle}
      className={`${baseClasses} ${stateClasses}`}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      <span className="text-sm" aria-hidden="true">
        {isDark ? "🌙" : "☀️"}
      </span>
      <span>{isDark ? "Dark" : "Light"}</span>
    </button>
  );
}
