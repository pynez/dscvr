import { useState } from "react";
import { Link } from "react-router-dom";
import { TikTokScroll } from "../components/TikTokScroll";
import { fetchBlindTasteTest, fetchBlindReveal } from "../api/client";

export function BlindTasteTest() {
  const [phase, setPhase] = useState("intro"); // intro | loading | playing | reveal
  const [tracks, setTracks] = useState([]);
  const [ratings, setRatings] = useState({});
  const [revealed, setRevealed] = useState([]);
  const [error, setError] = useState(null);

  async function startTest() {
    setPhase("loading");
    setError(null);
    try {
      const data = await fetchBlindTasteTest();
      setTracks(data.tracks);
      setPhase("playing");
    } catch (err) {
      setError(err.message);
      setPhase("intro");
    }
  }

  async function handleComplete() {
    const indices = tracks.map((t) => t.row_index);
    try {
      const data = await fetchBlindReveal(indices);
      setRevealed(data.tracks.map((t) => ({ ...t, rating: ratings[t.row_index] || "neutral" })));
      setPhase("reveal");
    } catch (err) {
      setError(err.message);
    }
  }

  const blindTracks = tracks.map((t) => ({
    ...t,
    name: "unknown track",
    artist: "unknown artist",
    artwork_url: null,
    tags: [],
  }));

  const summaryCard = (
    <div className="summary-card">
      <span className="summary-card__eyebrow">blind taste test</span>
      <h2 className="summary-card__title">all done.</h2>
      <hr className="summary-card__rule" />
      <p className="summary-card__body">Ready to see what you were actually listening to?</p>
      <button
        className="fp-submit"
        style={{ marginTop: 24 }}
        onClick={handleComplete}
      >
        reveal everything →
      </button>
    </div>
  );

  if (phase === "playing") {
    return (
      <TikTokScroll
        tracks={blindTracks}
        feature="blind-taste-test"
        getContextLine={() => ""}
        summaryCard={summaryCard}
      />
    );
  }

  if (phase === "reveal") {
    return (
      <div className="feature-page-shell" style={{ paddingBottom: 80 }}>
        <Link to="/#features" className="feature-page-back">← dscvr.</Link>
        <h1 className="feature-page-title">the reveal.</h1>
        <hr className="feature-page-rule" />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 1, background: "#000", border: "1px solid #000" }}>
          {revealed.map((t) => (
            <div
              key={t.row_index}
              style={{ background: "#d9d9d9", padding: "16px 20px", display: "flex", gap: 14 }}
            >
              {t.artwork_url && (
                <img src={t.artwork_url} alt={t.name} style={{ width: 60, height: 60, objectFit: "cover", flexShrink: 0 }} />
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontFamily: "var(--font-body)", fontSize: 14, fontWeight: 500, marginBottom: 2 }}>{t.name}</p>
                <p style={{ fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 300, opacity: 0.6, marginBottom: 6 }}>{t.artist}</p>
                <span style={{
                  fontFamily: "var(--font-footer)",
                  fontSize: 9,
                  letterSpacing: "0.12em",
                  textTransform: "uppercase",
                  padding: "3px 8px",
                  border: "1px solid #000",
                  opacity: t.rating === "heart" ? 1 : 0.35,
                }}>
                  {t.rating === "heart" ? "♥ loved" : t.rating === "skip" ? "✕ skipped" : "— heard"}
                </span>
              </div>
            </div>
          ))}
        </div>
        <Link to="/#features" className="feature-page-back" style={{ marginTop: 40, display: "inline-block" }}>← back to dscvr.</Link>
      </div>
    );
  }

  return (
    <div className="feature-page-shell">
      <Link to="/#features" className="feature-page-back">← dscvr.</Link>
      <h1 className="feature-page-title">blind taste test</h1>
      <hr className="feature-page-rule" />

      <div className="feature-page-body">
        <p style={{ fontFamily: "var(--font-body)", fontSize: 15, fontWeight: 300, lineHeight: 1.7, marginBottom: 36, opacity: 0.7 }}>
          Ten tracks. No names. No artists. No context. Just the music. Heart what moves you, skip what doesn't. Then see how well you know yourself.
        </p>
        {error && <p className="fp-error">{error}</p>}
        <button
          className="fp-submit"
          onClick={startTest}
          disabled={phase === "loading"}
        >
          {phase === "loading" ? "loading tracks…" : "start the test →"}
        </button>
      </div>
    </div>
  );
}
