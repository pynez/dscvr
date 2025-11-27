import { ThemeToggle } from "./ThemeToggle";

export function Layout({ children, theme, onToggleTheme }) {
  return (
    <div
      className="
        min-h-screen w-full
        bg-app-bg text-app-fg
        px-4 py-6 sm:px-6 lg:px-8
      "
    >
      <div className="w-full max-w-3xl mx-auto flex flex-col gap-6">
        <header className="flex flex-col items-center text-center gap-3">
          <h1 className="text-3xl font-semibold tracking-tight">dscvr.</h1>

          <p className="text-sm text-app-subtle max-w-md">
            Type a track you love and discover more songs with a similar vibe.
          </p>

          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </header>

        <main className="flex flex-col items-center w-full gap-6">
          {children}
        </main>

        <footer
          className="
            mt-8 pt-4 w-full
            border-t border-app-border
            text-[11px] text-app-subtle
            flex items-center justify-between
          "
        >
          <span>dscvr. · by Victor Pyne Jr</span>
          <span>Last.fm · iTunes · FastAPI · React</span>
        </footer>
      </div>
    </div>
  );
}
