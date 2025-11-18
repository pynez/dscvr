// frontend/src/components/TrackCard.jsx
export function TrackCard({ track, index, onPlay, isActive, isFavorite, onToggleFavorite }) {
  const {
    name,
    artist,
    score,
    artwork_url,
    preview_url,
  } = track;

  const scorePct = Math.round(score * 100);

  return (
    <article className={`track-card ${isActive ? "track-card--active" : ""}`}>
      {artwork_url && (
        <img
          className="track-art"
          src={artwork_url}
          alt={`Artwork for ${name} by ${artist}`}
          loading="lazy"
        />
      )}
      <div className="track-body">
        <h3 className="track-title">{name}</h3>
        <p className="track-artist">{artist}</p>
        <p className="track-score">Similarity: {scorePct}%</p>

        <div className="track-actions">
          {preview_url && (
            <button
              type="button"
              className="track-play-btn"
              onClick={() => onPlay(index)}
            >
              {isActive ? "Playing in mini player" : "Play in mini player"}
            </button>
          )}

            <button
            type="button"
            className="track-fav-btn"
            onClick={() => onToggleFavorite(track)}
            aria-label={isFavorite ? "Remove from favorites" : "Add to favorites"}
          >
            {isFavorite ? "♥" : "♡"}
          </button>
          
        </div>
      </div>
    </article>
  );
}
