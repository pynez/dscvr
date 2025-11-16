// frontend/src/components/TrackCard.jsx
export function TrackCard({ track }) {
  const {
    name,
    artist,
    score,
    artwork_url,
    preview_url,
  } = track;

  const scorePct = Math.round(score * 100);

  return (
    <article className="track-card">
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
        {preview_url && (
          <audio
            className="track-audio"
            controls
            preload="none"
            src={preview_url}
          >
            Your browser does not support the audio element.
          </audio>
        )}
      </div>
    </article>
  );
}
