// frontend/src/App.jsx
import { useState, useMemo } from "react";
import "./styles/globals.css";
import { Layout } from "./components/Layout";
import { SearchBar } from "./components/SearchBar";
import { TrackCard } from "./components/TrackCard";
import { NowPlayingBar } from "./components/NowPlayingBar";
import { FavoritesPlaylist } from "./components/FavoritesPlaylist";
import { useRecommendations } from "./hooks/useRecommendations";
import { useTheme } from "./hooks/useTheme";
import { useFavorites } from "./hooks/useFavorites";

function App() {
  const { theme, toggleTheme } = useTheme();

  const {
    query,
    setQuery,
    submit,
    matchedTrack,
    recommendations,
    isLoading,
    error,
  } = useRecommendations();

  const { favorites, isFavorite, toggleFavorite } = useFavorites();

  // playContext: which list we're playing from + index within that list
  const [playContext, setPlayContext] = useState({
    type: "recs", // "recs" | "favorites"
    index: null,
  });

  // Reset index when recommendations change (new search)
  useMemo(() => {
    setPlayContext((prev) => ({ ...prev, type: "recs", index: null }));
  }, [recommendations]);

  const currentQueue =
    playContext.type === "favorites" ? favorites : recommendations;

  const currentTrack =
    playContext.index !== null && currentQueue[playContext.index]
      ? currentQueue[playContext.index]
      : null;

  function handlePlayFromCard(index) {
    setPlayContext({ type: "recs", index });
  }

  function handlePlayFromFavorites(index) {
    setPlayContext({ type: "favorites", index });
  }

  function handleNextTrack() {
    if (!currentQueue.length || playContext.index === null) return;
    const nextIndex =
      playContext.index + 1 < currentQueue.length ? playContext.index + 1 : 0;
    setPlayContext((prev) => ({ ...prev, index: nextIndex }));
  }

  function handlePrevTrack() {
    if (!currentQueue.length || playContext.index === null) return;
    const prevIndex =
      playContext.index - 1 >= 0
        ? playContext.index - 1
        : currentQueue.length - 1;
    setPlayContext((prev) => ({ ...prev, index: prevIndex }));
  }

  const hasPrev = currentQueue.length > 1 && playContext.index !== null;
  const hasNext = currentQueue.length > 1 && playContext.index !== null;

  const activeRecsIndex =
    playContext.type === "recs" ? playContext.index : null;
  const activeFavIndex =
    playContext.type === "favorites" ? playContext.index : null;

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
              isActive={i === activeRecsIndex}
              onPlay={handlePlayFromCard}
              isFavorite={isFavorite(track)}
              onToggleFavorite={toggleFavorite}
            />
          ))}
        </div>
      </section>

      <FavoritesPlaylist
        favorites={favorites}
        onPlay={handlePlayFromFavorites}
        isFavorite={isFavorite}
        onToggleFavorite={toggleFavorite}
        activeIndex={activeFavIndex}
      />

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