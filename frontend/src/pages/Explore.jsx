import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useRecommendations } from "../hooks/useRecommendations";
import { useFavorites } from "../hooks/useFavorites";
import { useInteractions } from "../hooks/useInteractions";
import { NowPlayingBar } from "../components/NowPlayingBar";

export function Explore() {
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
  const { track: logInteraction } = useInteractions("explore");
  const [playContext, setPlayContext] = useState({ type: "recs", index: null });

  useMemo(() => {
    setPlayContext({ type: "recs", index: null });
  }, [recommendations]);

  const currentQueue =
    playContext.type === "favorites" ? favorites : recommendations;
  const currentTrack =
    playContext.index !== null ? currentQueue[playContext.index] ?? null : null;

  function handlePlay(idx) {
    setPlayContext({ type: "recs", index: idx });
  }
  function handlePlayFavorite(idx) {
    setPlayContext({ type: "favorites", index: idx });
  }
  function handleNext() {
    if (!currentQueue.length || playContext.index === null) return;
    setPlayContext((p) => ({ ...p, index: (p.index + 1) % currentQueue.length }));
  }
  function handlePrev() {
    if (!currentQueue.length || playContext.index === null) return;
    setPlayContext((p) => ({
      ...p,
      index: (p.index - 1 + currentQueue.length) % currentQueue.length,
    }));
  }

  return (
    <div className="explore-page">
      {/* Header */}
      <Link to="/#features" className="feature-page-back">← dscvr.</Link>

      <span
        style={{
          fontFamily: "var(--font-wordmark)",
          fontSize: "clamp(36px, 5vw, 56px)",
          fontWeight: 400,
          letterSpacing: "-0.01em",
          lineHeight: 1.05,
          display: "block",
          marginBottom: 6,
        }}
      >
        explore
      </span>
      <hr className="feature-page-rule" />

      {/* Search */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const val = e.target.elements.q.value.trim();
          if (val) submit(val);
        }}
      >
        <div className="explore-search-row">
          <input
            name="q"
            className="explore-search-input"
            placeholder="artist — track name, e.g. SZA — Snooze"
            defaultValue={query}
            disabled={isLoading}
            autoComplete="off"
          />
          <button
            type="submit"
            className="explore-search-btn"
            disabled={isLoading}
          >
            {isLoading ? "searching…" : "recommend →"}
          </button>
        </div>
      </form>

      {error && <p className="fp-error">{error}</p>}

      {/* Candidates */}
      {candidates.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <p className="dim-text" style={{ marginBottom: 12 }}>
            Did you mean one of these?
          </p>
          <div className="explore-candidates">
            {candidates.map((c) => (
              <button
                key={c.row_index}
                className="explore-candidate-btn"
                onClick={() => chooseCandidate(c)}
                disabled={isLoading}
              >
                {c.title} — {c.artist}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Matched track */}
      {matchedTrack && (
        <p
          className="dim-text"
          style={{ marginBottom: 28 }}
        >
          based on{" "}
          <em>
            {matchedTrack.title} — {matchedTrack.artist}
          </em>
        </p>
      )}

      {/* Results */}
      {!isLoading && !recommendations.length && !error && (
        <p className="dim-text">enter a track above to get recommendations.</p>
      )}

      {recommendations.length > 0 && (
        <div className="explore-results">
          {recommendations.map((track, i) => (
            <div
              key={`${track.row_index}-${i}`}
              className="explore-track-card"
            >
              {track.artwork_url ? (
                <img
                  className="explore-track-art"
                  src={track.artwork_url}
                  alt={track.name}
                  loading="lazy"
                />
              ) : (
                <div className="explore-track-art-placeholder">♪</div>
              )}
              <p className="explore-track-name">{track.name}</p>
              <p className="explore-track-artist">{track.artist}</p>
              <p className="explore-track-score">
                {Math.round(track.score * 100)}% match
              </p>
              <div className="explore-track-actions">
                {track.preview_url && (
                  <button
                    className={`explore-track-btn ${
                      playContext.index === i && playContext.type === "recs"
                        ? "explore-track-btn--active"
                        : ""
                    }`}
                    onClick={() => handlePlay(i)}
                  >
                    {playContext.index === i && playContext.type === "recs"
                      ? "▶ playing"
                      : "▶ play"}
                  </button>
                )}
                <button
                  className={`explore-track-btn ${
                    isFavorite(track) ? "explore-track-btn--active" : ""
                  }`}
                  onClick={() => {
                    const wasSaved = isFavorite(track);
                    toggleFavorite(track);
                    if (!wasSaved) {
                      logInteraction(track.row_index, "heart", track.tags || []);
                    }
                  }}
                >
                  {isFavorite(track) ? "♥ saved" : "♡ save"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Saved tracks */}
      {favorites.length > 0 && (
        <div className="explore-saved">
          <div className="explore-saved-header">
            <span className="explore-saved-title">saved.</span>
            <span className="explore-saved-count">{favorites.length} track{favorites.length !== 1 ? "s" : ""}</span>
          </div>
          <hr className="feature-page-rule" style={{ marginBottom: 0 }} />
          <div className="explore-results">
            {favorites.map((track, i) => (
              <div
                key={`fav-${track.row_index ?? i}`}
                className="explore-track-card"
              >
                {track.artwork_url ? (
                  <img
                    className="explore-track-art"
                    src={track.artwork_url}
                    alt={track.name}
                    loading="lazy"
                  />
                ) : (
                  <div className="explore-track-art-placeholder">♪</div>
                )}
                <p className="explore-track-name">{track.name}</p>
                <p className="explore-track-artist">{track.artist}</p>
                <div className="explore-track-actions">
                  {track.preview_url && (
                    <button
                      className={`explore-track-btn ${
                        playContext.index === i && playContext.type === "favorites"
                          ? "explore-track-btn--active"
                          : ""
                      }`}
                      onClick={() => handlePlayFavorite(i)}
                    >
                      {playContext.index === i && playContext.type === "favorites"
                        ? "▶ playing"
                        : "▶ play"}
                    </button>
                  )}
                  <button
                    className="explore-track-btn explore-track-btn--active"
                    onClick={() => {
                      // if this track is currently playing, stop it
                      if (playContext.type === "favorites" && playContext.index === i) {
                        setPlayContext({ type: "favorites", index: null });
                      }
                      toggleFavorite(track);
                    }}
                  >
                    ♥ saved
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <NowPlayingBar
        track={currentTrack}
        hasPrev={currentQueue.length > 1 && playContext.index !== null}
        hasNext={currentQueue.length > 1 && playContext.index !== null}
        onPrev={handlePrev}
        onNext={handleNext}
      />
    </div>
  );
}
