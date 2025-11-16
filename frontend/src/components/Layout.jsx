// frontend/src/components/Layout.jsx
export function Layout({ children }) {
  return (
    <div className="app-root">
      <header className="app-header">
        <h1 className="app-title">Museek</h1>
        <p className="app-subtitle">
          Type an R&amp;B track you love and discover more songs with a similar vibe.
        </p>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <span>Built with Last.fm, iTunes, FastAPI &amp; React</span>
      </footer>
    </div>
  );
}
