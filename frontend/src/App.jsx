// frontend/src/App.jsx
import { useState, useMemo } from "react";
import "./styles/globals.css";
import { Layout } from "./components/Layout";
import { SearchBar } from "./components/SearchBar";
import { TrackCard } from "./components/TrackCard";
import { NowPlayingBar } from "./components/NowPlayingBar";
import { useRecommendations } from "./hooks/useRecommendations";
import { useTheme } from "./hooks/useTheme";

function App() {
  const { theme, toggleTheme } = useTheme();

  const {
    query,
    setQuery, // unused for now but available
    submit,
    matchedTrack,
    recommendations,
    isLoading,
    error,
  } = useRecommendations();

  const [currentIndex, setCurrentIndex] = useState(null);

  useMemo(() => {
    setCurrentIndex(null);
  }, [recommendations]);

  const currentTrack =
    currentIndex !== null && recommendations[currentIndex]
      ? recommendations[currentIndex]
      : null;

  function handlePlayFromCard(index) {
    setCurrentIndex(index);
  }

  function handleNextTrack() {
    if (!recommendations.length || currentIndex === null) return;
    const nextIndex =
      currentIndex + 1 < recommendations.length ? currentIndex + 1 : 0;
    setCurrentIndex(nextIndex);
  }

  function handlePrevTrack() {
    if (!recommendations.length || currentIndex === null) return;
    const prevIndex =
      currentIndex - 1 >= 0 ? currentIndex - 1 : recommendations.length - 1;
    setCurrentIndex(prevIndex);
  }

  const hasPrev = recommendations.length > 1 && currentIndex !== null;
  const hasNext = recommendations.length > 1 && currentIndex !== null;

  return (
    <Layout theme={theme} onToggleTheme={toggleTheme}>
      <SearchBar
        initialQuery={query}
        onSubmit={submit}
        isLoading={isLoading}
      />

      {error && <p className="error-text">{error}</p>}

      {matchedTrack && (
        <section className="matched-section">
          <h2>You asked for:</h2>
          <p className="matched-track">
            <strong>{matchedTrack.title}</strong> — {matchedTrack.artist}
          </p>
        </section>
      )}

      <section className="results-section">
        {isLoading && <p className="dim-text">Crunching vibes…</p>}

        {!isLoading && !recommendations.length && !error && (
          <p className="dim-text">
            Try searching for a track to see recommendations.
          </p>
        )}

        <div className="results-grid">
          {recommendations.map((track, i) => (
            <TrackCard
              key={`${track.row_index}-${track.name}`}
              track={track}
              index={i}
              isActive={i === currentIndex}
              onPlay={handlePlayFromCard}
            />
          ))}
        </div>
      </section>

      <NowPlayingBar
        track={currentTrack}
        hasPrev={hasPrev}
        hasNext={hasNext}
        onPrev={handlePrevTrack}
        onNext={handleNextTrack}
      />
    </Layout>
  );
}

export default App;
