import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { TikTokScroll } from "../components/TikTokScroll";
import { fetchAlgorithmicCapture } from "../api/client";

function CaptureRadar({ tagDistribution = [] }) {
  const canvasRef = useRef(null);
  const tags = tagDistribution.slice(0, 8);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !tags.length) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2;
    const radius = Math.min(cx, cy) - 32;
    const n = tags.length;
    const maxScore = Math.max(...tags.map((t) => t.score), 1);

    ctx.clearRect(0, 0, w, h);

    // Grid rings
    [0.25, 0.5, 0.75, 1].forEach((r) => {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(0,0,0,0.08)";
      ctx.lineWidth = 1;
      tags.forEach((_, i) => {
        const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
        const x = cx + radius * r * Math.cos(angle);
        const y = cy + radius * r * Math.sin(angle);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.stroke();
    });

    // Axes
    tags.forEach((_, i) => {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      ctx.beginPath();
      ctx.strokeStyle = "rgba(0,0,0,0.1)";
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
      ctx.stroke();
    });

    // Data polygon
    ctx.beginPath();
    tags.forEach((t, i) => {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      const r = (t.score / maxScore) * radius;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.fillStyle = "rgba(0,0,0,0.08)";
    ctx.fill();
    ctx.strokeStyle = "#000";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Labels
    ctx.font = "11px 'Source Serif 4', serif";
    ctx.fillStyle = "rgba(0,0,0,0.5)";
    ctx.textAlign = "center";
    tags.forEach((t, i) => {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      const x = cx + (radius + 20) * Math.cos(angle);
      const y = cy + (radius + 20) * Math.sin(angle) + 4;
      ctx.fillText(t.tag.length > 10 ? t.tag.slice(0, 10) + "…" : t.tag, x, y);
    });
  }, [tags]);

  return <canvas ref={canvasRef} width={260} height={260} />;
}

export function AlgorithmicCapture() {
  const [phase, setPhase] = useState("intro");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function load() {
    setPhase("loading");
    setError(null);
    try {
      const data = await fetchAlgorithmicCapture();
      setResult(data);
      setPhase("results");
    } catch (err) {
      setError(err.message);
      setPhase("intro");
    }
  }

  const summaryCard = (
    <div className="summary-card">
      <span className="summary-card__eyebrow">algorithmic capture</span>
      <h2 className="summary-card__title">escape complete.</h2>
      <hr className="summary-card__rule" />
      <p className="summary-card__body">
        You've listened beyond your boundaries. Keep going.
      </p>
      <Link to="/#features" className="summary-card__back">← back to dscvr.</Link>
    </div>
  );

  if (phase === "results" && result?.insufficient_data) {
    return (
      <div className="feature-page-shell">
        <Link to="/#features" className="feature-page-back">← dscvr.</Link>
        <h1 className="feature-page-title">not enough data.</h1>
        <hr className="feature-page-rule" />
        <p style={{ fontFamily: "var(--font-body)", fontSize: 15, fontWeight: 300, lineHeight: 1.7, opacity: 0.7, maxWidth: 480 }}>
          We need at least {result.interactions_needed} more interactions to compute your capture score. Heart some tracks in other features first, then come back.
        </p>
        <Link to="/#features" className="fp-submit" style={{ display: "inline-block", marginTop: 32, textDecoration: "none" }}>
          explore features →
        </Link>
      </div>
    );
  }

  if (phase === "results" && result) {
    return (
      <div style={{ background: "var(--color-bg)" }}>
        {/* Score screen */}
        <div className="feature-page-shell">
          <Link to="/#features" className="feature-page-back">← dscvr.</Link>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 0 }}>
            <p style={{ fontFamily: "var(--font-footer)", fontSize: 10, letterSpacing: "0.16em", textTransform: "uppercase", opacity: 0.4, marginBottom: 8 }}>
              you are
            </p>
            <p style={{ fontFamily: "var(--font-wordmark)", fontSize: "clamp(72px, 14vw, 140px)", fontWeight: 400, lineHeight: 1, letterSpacing: "-0.02em", marginBottom: 4 }}>
              {result.capture_percent}%
            </p>
            <p style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 300, letterSpacing: "0.12em", textTransform: "uppercase", opacity: 0.5, marginBottom: 32 }}>
              algorithmically captured
            </p>
          </div>

          <hr className="feature-page-rule" />

          <div style={{ display: "flex", gap: 40, alignItems: "flex-start", flexWrap: "wrap", paddingTop: 32 }}>
            <CaptureRadar tagDistribution={result.tag_distribution} />

            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div>
                <p className="fp-label">dominant taste</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                  {result.dominant_tags.map((t) => (
                    <span key={t} style={{
                      fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 400,
                      border: "1px solid #000", padding: "4px 10px",
                    }}>{t}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="fp-label">underexplored</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                  {result.underexplored_tags.slice(0, 6).map((t) => (
                    <span key={t} style={{
                      fontFamily: "var(--font-body)", fontSize: 12, fontWeight: 300,
                      border: "1px solid rgba(0,0,0,0.3)", padding: "4px 10px", opacity: 0.6,
                    }}>{t}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <p style={{ fontFamily: "var(--font-body)", fontSize: 13, fontWeight: 300, opacity: 0.5, marginTop: 32 }}>
            escape routes below ↓
          </p>
        </div>

        <TikTokScroll
          tracks={result.escape_tracks}
          feature="algorithmic-capture"
          getContextLine={(t) =>
            t.escape_tag ? `you never explore "${t.escape_tag}" — here's what you're missing` : ""
          }
          summaryCard={summaryCard}
        />
      </div>
    );
  }

  return (
    <div className="feature-page-shell">
      <Link to="/#features" className="feature-page-back">← dscvr.</Link>
      <h1 className="feature-page-title">algorithmic capture</h1>
      <hr className="feature-page-rule" />

      <div className="feature-page-body">
        <p style={{ fontFamily: "var(--font-body)", fontSize: 15, fontWeight: 300, lineHeight: 1.7, marginBottom: 36, opacity: 0.7 }}>
          How homogenized has your taste become? We'll measure your tag distribution, compute a capture score, and find the tracks that break the pattern.
        </p>
        {error && <p className="fp-error">{error}</p>}
        <button className="fp-submit" onClick={load} disabled={phase === "loading"}>
          {phase === "loading" ? "analysing your taste…" : "measure my capture →"}
        </button>
      </div>
    </div>
  );
}
