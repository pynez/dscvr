// frontend/src/components/Layout.jsx
import { ThemeToggle } from "./ThemeToggle";

export function Layout({ children, theme, onToggleTheme }) {
  return (
    <div className="app-root">
      <header className="app-header">
        <div className="app-header-row">
          <div>
            <h1 className="app-title">dscvr</h1>
            <p className="app-subtitle">
              Type an R&amp;B track you love and discover more songs with a similar vibe.
            </p>
          </div>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <span>Built with Last.fm, iTunes, FastAPI &amp; React</span>
      </footer>
    </div>
  );
}
