// frontend/src/pages/Discover.jsx
// Classic search → recommendations page (preserved from original app)
import { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { SearchBar } from "../components/SearchBar";
import { TrackCard } from "../components/TrackCard";
import { NowPlayingBar } from "../components/NowPlayingBar";
import { FavoritesPlaylist } from "../components/FavoritesPlaylist";
import { useRecommendations } from "../hooks/useRecommendations";
import { useFavorites } from "../hooks/useFavorites";

const ACCENT = "#d49019";

export function Discover() {
  const {
    query,
    submit,
    chooseCandidate,
    matchedTrack,
    recommendations,
    candidates,
    isLoading,
    error,
  } = useRecommendations();

  const { favorites, isFavorite, toggleFavorite } = useFavorites();

  const [playContext, setPlayContext] = useState({ type: "recs", index: null });

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
    setPlayContext((p) => ({
      ...p,
      index: (p.index + 1) % currentQueue.length,
    }));
  }
  function handlePrevTrack() {
    if (!currentQueue.length || playContext.index === null) return;
    setPlayContext((p) => ({
      ...p,
      index: (p.index - 1 + currentQueue.length) % currentQueue.length,
    }));
  }

  const activeRecsIndex = playContext.type === "recs" ? playContext.index : null;
  const activeFavIndex = playContext.type === "favorites" ? playContext.index : null;

  return (
    <div className="discover-page">
      <div className="discover-page__inner">
        <Link to="/#features" className="feature-back">← dscvr.</Link>
        <h1 className="discover-page__title">Discover</h1>
        <p className="discover-page__sub">Find tracks similar to one you love.</p>

        <SearchBar initialQuery={query} onSubmit={submit} isLoading={isLoading} />

        {error && <p className="feature-error">{error}</p>}

        {candidates.length > 0 && (
          <section className="candidate-section">
            <div className="candidate-grid">
              {candidates.map((cand) => (
                <button
                  key={`${cand.row_index}-${cand.track_key}`}
                  className="candidate-card"
                  onClick={() => chooseCandidate(cand)}
                  disabled={isLoading}
                >
                  {cand.artwork_url && (
                    <img className="candidate-art" src={cand.artwork_url} alt="" loading="lazy" />
                  )}
                  <div className="candidate-meta">
                    <span className="candidate-title">{cand.title}</span>
                    <span className="candidate-artist">{cand.artist}</span>
                    <span className="candidate-score">Match: {Math.round(cand.score)}%</span>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {matchedTrack && (
          <section className="matched-section">
            <h2>Based on:</h2>
            <p className="matched-track">
              <strong>{matchedTrack.title}</strong> — {matchedTrack.artist}
            </p>
          </section>
        )}

        <section className="results-section">
          {isLoading && <p className="dim-text">Crunching vibes…</p>}
          {!isLoading && !recommendations.length && !error && (
            <p className="dim-text">Search for a track to get recommendations.</p>
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
      </div>

      <NowPlayingBar
        track={currentTrack}
        hasPrev={currentQueue.length > 1 && playContext.index !== null}
        hasNext={currentQueue.length > 1 && playContext.index !== null}
        onPrev={handlePrevTrack}
        onNext={handleNextTrack}
      />
    </div>
  );
}
