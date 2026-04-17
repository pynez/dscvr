import { useState } from "react";
import { Link } from "react-router-dom";
import { TikTokScroll } from "../components/TikTokScroll";
import { fetchSoundtrack } from "../api/client";

export function Soundtrack() {
  const [description, setDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [heartedTracks, setHeartedTracks] = useState([]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setHeartedTracks([]);
    try {
      const data = await fetchSoundtrack(description.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const summaryCard = result ? (
    <div className="summary-card">
      <span className="summary-card__eyebrow">your soundtrack</span>
      <h2 className="summary-card__title">the verdict.</h2>
      <hr className="summary-card__rule" />
      {result.summary && <p className="summary-card__body">{result.summary}</p>}

      {heartedTracks.length > 0 && (
        <div className="summary-card__hearted">
          <p className="summary-card__hearted-label">songs you hearted</p>
          <ul className="summary-card__hearted-list">
            {heartedTracks.map((t) => (
              <li key={t.row_index} className="summary-card__hearted-item">
                <span className="summary-card__hearted-name">{t.name}</span>
                <span className="summary-card__hearted-artist">{t.artist}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {heartedTracks.length === 0 && (
        <p className="summary-card__no-hearts">heart songs as you swipe to save them here.</p>
      )}

      <Link to="/#features" className="summary-card__back">← back to dscvr.</Link>
    </div>
  ) : null;

  if (result) {
    return (
      <TikTokScroll
        tracks={result.tracks}
        feature="soundtrack"
        getContextLine={(t) => t.reasoning || ""}
        summaryCard={summaryCard}
        onHeartChange={setHeartedTracks}
      />
    );
  }

  return (
    <div className="feature-page-shell">
      <Link to="/#features" className="feature-page-back">← dscvr.</Link>
      <h1 className="feature-page-title">soundtrack your life</h1>
      <hr className="feature-page-rule" />

      <div className="feature-page-body">
        <p style={{ fontFamily: "var(--font-body)", fontSize: 15, fontWeight: 300, lineHeight: 1.7, marginBottom: 36, opacity: 0.7 }}>
          Describe a moment, a feeling, a memory. We'll find the songs that should have been playing.
        </p>

        <form onSubmit={handleSubmit}>
          <label className="fp-label" htmlFor="soundtrack-desc">describe the moment</label>
          <textarea
            id="soundtrack-desc"
            className="fp-textarea"
            rows={5}
            placeholder="driving home alone at 2am after the best night of your life, windows down, every traffic light green…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={loading}
          />
          {error && <p className="fp-error">{error}</p>}
          <button
            className="fp-submit"
            type="submit"
            disabled={loading || !description.trim()}
          >
            {loading ? "finding your soundtrack…" : "find my soundtrack →"}
          </button>
        </form>
      </div>
    </div>
  );
}
