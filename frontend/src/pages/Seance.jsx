import { useState } from "react";
import { Link } from "react-router-dom";
import { TikTokScroll } from "../components/TikTokScroll";
import { fetchSeance } from "../api/client";

export function Seance() {
  const [artist, setArtist] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [heartedTracks, setHeartedTracks] = useState([]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!artist.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setHeartedTracks([]);
    try {
      const data = await fetchSeance(artist.trim());
      if (!data.tracks?.length) {
        setError(`No living successors found for ${artist}. Try another artist.`);
        setLoading(false);
        return;
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const summaryCard = result ? (
    <div className="summary-card">
      <span className="summary-card__eyebrow">the séance</span>
      <h2 className="summary-card__title">the spirit lives.</h2>
      <hr className="summary-card__rule" />

      {result.original_artist && (
        <p className="summary-card__seance-origin">
          successors of <em>{result.original_artist}</em>
        </p>
      )}

      {result.summary && (
        <p className="summary-card__body">{result.summary}</p>
      )}

      {heartedTracks.length > 0 && (
        <div className="summary-card__hearted">
          <p className="summary-card__hearted-label">songs you hearted</p>
          <ul className="summary-card__hearted-list">
            {heartedTracks.map((t) => (
              <li key={t.row_index} className="summary-card__hearted-item">
                <span className="summary-card__hearted-name">{t.name}</span>
                <span className="summary-card__hearted-artist">{t.artist}</span>
                {t.connection && (
                  <span className="summary-card__hearted-connection">{t.connection}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {heartedTracks.length === 0 && (
        <p className="summary-card__no-hearts">heart tracks as you swipe to save them here.</p>
      )}

      <Link to="/#features" className="summary-card__back">← back to dscvr.</Link>
    </div>
  ) : null;

  if (result) {
    return (
      <TikTokScroll
        tracks={result.tracks}
        feature="seance"
        getContextLine={(t) => t.connection || ""}
        summaryCard={summaryCard}
        onHeartChange={setHeartedTracks}
      />
    );
  }

  return (
    <div className="feature-page-shell">
      <Link to="/#features" className="feature-page-back">← dscvr.</Link>
      <h1 className="feature-page-title">the séance</h1>
      <hr className="feature-page-rule" />

      <div className="feature-page-body">
        <p style={{ fontFamily: "var(--font-body)", fontSize: 15, fontWeight: 300, lineHeight: 1.7, marginBottom: 36, opacity: 0.7 }}>
          Name a deceased artist. We'll summon their living spiritual successors — and tell you exactly what they carry forward.
        </p>

        <form onSubmit={handleSubmit}>
          <label className="fp-label" htmlFor="seance-artist">the artist</label>
          <input
            id="seance-artist"
            className="fp-input"
            placeholder="e.g. Amy Winehouse, Tupac, Kurt Cobain…"
            value={artist}
            onChange={(e) => setArtist(e.target.value)}
            disabled={loading}
          />
          {error && <p className="fp-error">{error}</p>}
          {loading && (
            <p style={{
              fontFamily: "var(--font-body)",
              fontSize: 13,
              fontWeight: 300,
              fontStyle: "italic",
              opacity: 0.5,
              marginTop: 16,
              letterSpacing: "0.06em",
            }}>
              summoning…
            </p>
          )}
          <button
            className="fp-submit"
            type="submit"
            disabled={loading || !artist.trim()}
          >
            {loading ? "summoning…" : "begin the séance →"}
          </button>
        </form>
      </div>
    </div>
  );
}
