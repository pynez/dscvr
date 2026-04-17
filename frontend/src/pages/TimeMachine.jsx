import { useState } from "react";
import { Link } from "react-router-dom";
import { TikTokScroll } from "../components/TikTokScroll";
import { fetchTimeMachine, fetchSearch } from "../api/client";

const ERAS = [
  { value: "60s", label: "1960s" },
  { value: "70s", label: "1970s" },
  { value: "80s", label: "1980s" },
  { value: "90s", label: "1990s" },
  { value: "00s", label: "2000s" },
];

export function TimeMachine() {
  const [seedTrack, setSeedTrack] = useState("");
  const [seedArtist, setSeedArtist] = useState("");
  const [era, setEra] = useState("80s");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [searchTimeout, setSearchTimeout] = useState(null);

  function handleSearchChange(val) {
    setSeedTrack(val);
    setSeedArtist("");
    clearTimeout(searchTimeout);
    if (!val.trim() || val.length < 2) { setSuggestions([]); return; }
    setSearchTimeout(setTimeout(async () => {
      try {
        const data = await fetchSearch(val);
        setSuggestions(data.results?.slice(0, 5) || []);
      } catch { setSuggestions([]); }
    }, 300));
  }

  function selectSuggestion(s) {
    setSeedTrack(s.title);
    setSeedArtist(s.artist);
    setSuggestions([]);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!seedTrack.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await fetchTimeMachine({ seedTrack: seedTrack.trim(), seedArtist: seedArtist.trim(), era });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const summaryCard = result ? (
    <div className="summary-card">
      <span className="summary-card__eyebrow">the time machine — {result.era}</span>
      <h2 className="summary-card__title">your {result.era} taste.</h2>
      <hr className="summary-card__rule" />
      <p className="summary-card__body">{result.summary}</p>
      <Link to="/#features" className="summary-card__back">← back to dscvr.</Link>
    </div>
  ) : null;

  if (result) {
    return (
      <TikTokScroll
        tracks={result.tracks}
        feature="time-machine"
        getContextLine={(t) => (t.tags || []).slice(0, 3).join(" · ")}
        summaryCard={summaryCard}
      />
    );
  }

  return (
    <div className="feature-page-shell">
      <Link to="/#features" className="feature-page-back">← dscvr.</Link>
      <h1 className="feature-page-title">the time machine</h1>
      <hr className="feature-page-rule" />

      <div className="feature-page-body">
        <p style={{ fontFamily: "var(--font-body)", fontSize: 15, fontWeight: 300, lineHeight: 1.7, marginBottom: 36, opacity: 0.7 }}>
          Give us a seed track and an era. We'll find what you would have been obsessed with.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          {/* Seed track */}
          <div style={{ position: "relative" }}>
            <label className="fp-label" htmlFor="seed">seed track</label>
            <input
              id="seed"
              className="fp-input"
              placeholder="e.g. Blinding Lights"
              value={seedTrack}
              onChange={(e) => handleSearchChange(e.target.value)}
              disabled={loading}
              autoComplete="off"
            />
            {suggestions.length > 0 && (
              <ul style={{
                position: "absolute", top: "100%", left: 0, right: 0, zIndex: 20,
                background: "#d9d9d9", border: "1px solid #000", listStyle: "none",
              }}>
                {suggestions.map((s) => (
                  <li
                    key={s.row_index}
                    onClick={() => selectSuggestion(s)}
                    style={{
                      padding: "10px 14px", cursor: "pointer",
                      fontFamily: "var(--font-body)", fontSize: 13,
                      borderBottom: "1px solid rgba(0,0,0,0.1)",
                    }}
                  >
                    <span style={{ fontWeight: 500 }}>{s.title}</span>
                    <span style={{ opacity: 0.5 }}> — {s.artist}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Era */}
          <div>
            <label className="fp-label">era</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {ERAS.map((e) => (
                <button
                  key={e.value}
                  type="button"
                  onClick={() => setEra(e.value)}
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: 13,
                    fontWeight: era === e.value ? 500 : 300,
                    padding: "8px 18px",
                    border: "1px solid #000",
                    background: era === e.value ? "#000" : "transparent",
                    color: era === e.value ? "#d9d9d9" : "#000",
                    cursor: "pointer",
                    transition: "background 0.15s, color 0.15s",
                  }}
                >
                  {e.label}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="fp-error">{error}</p>}
          <button className="fp-submit" type="submit" disabled={loading || !seedTrack.trim()}>
            {loading ? `travelling to the ${era}…` : `take me to the ${era} →`}
          </button>
        </form>
      </div>
    </div>
  );
}
