// frontend/src/components/FavoritesPlaylist.jsx
export function FavoritesPlaylist({
  favorites,
  onPlay,
  isFavorite,
  onToggleFavorite,
  activeIndex,
}) {
  return (
    <section className="favorites-section">
      <div className="favorites-header">
        <h2>Your favorites</h2>
        <span className="favorites-count">
          {favorites.length === 0
            ? "No favorites yet"
            : `${favorites.length} track${favorites.length === 1 ? "" : "s"}`}
        </span>
      </div>

      {favorites.length === 0 ? (
        <p className="dim-text">
          Tap the heart on any recommendation to add it to your favorites.
        </p>
      ) : (
        <ul className="favorites-list">
          {favorites.map((track, i) => {
            const key = `${track.name} — ${track.artist}`;
            const isActiveRow = activeIndex === i;
            return (
              <li
                key={key}
                className={`favorites-item ${
                  isActiveRow ? "favorites-item--active" : ""
                }`}
              >
                <button
                  type="button"
                  className="favorites-play"
                  onClick={() => onPlay(i)}
                >
                  ▶️
                </button>
                <div className="favorites-meta">
                  <div className="favorites-title">{track.name}</div>
                  <div className="favorites-artist">{track.artist}</div>
                </div>
                <button
                  type="button"
                  className="favorites-heart"
                  onClick={() => onToggleFavorite(track)}
                  aria-label={
                    isFavorite(track)
                      ? "Remove from favorites"
                      : "Add to favorites"
                  }
                >
                  {isFavorite(track) ? "♥" : "♡"}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}