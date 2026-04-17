import { useRef, useEffect, useState } from "react";

export function TrackScrollCard({
  track,
  isActive,
  isHearted = false,
  contextLine,
  onHeart,
  onSkip,
  isSummaryCard = false,
  children,
  "data-index": dataIndex,
}) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [audioError, setAudioError] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isActive && track?.preview_url && !audioError) {
      audio.play().catch(() => setAudioError(true));
      setPlaying(true);
    } else {
      audio.pause();
      setPlaying(false);
    }
  }, [isActive, track?.preview_url, audioError]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    const onTime = () => {
      if (audio.duration) setProgress((audio.currentTime / audio.duration) * 100);
    };
    audio.addEventListener("timeupdate", onTime);
    return () => audio.removeEventListener("timeupdate", onTime);
  }, []);

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio) return;
    if (playing) { audio.pause(); setPlaying(false); }
    else { audio.play().catch(() => setAudioError(true)); setPlaying(true); }
  }

  if (isSummaryCard) {
    return (
      <div className="scroll-card scroll-card--summary" data-index={dataIndex}>
        <div className="scroll-card__summary-inner">{children}</div>
      </div>
    );
  }

  const hasAudio   = !!track?.preview_url && !audioError;
  const hasYoutube = !track?.preview_url && track?.youtube_id;

  return (
    <div
      className={`scroll-card${isActive ? " scroll-card--active" : ""}`}
      data-index={dataIndex}
    >
      {track?.artwork_url && (
        <div
          className="scroll-card__bg"
          style={{ backgroundImage: `url(${track.artwork_url})` }}
        />
      )}
      <div className="scroll-card__overlay" />

      <div className="scroll-card__content">
        {/* Art */}
        <div style={{ position: "relative", display: "inline-block" }}>
          {track?.artwork_url ? (
            <img src={track.artwork_url} alt={track.name} className="scroll-card__art" />
          ) : (
            <div className="scroll-card__art-placeholder">♪</div>
          )}
          {(hasAudio || hasYoutube) && (
            <button
              onClick={togglePlay}
              aria-label={playing ? "Pause" : "Play"}
              style={{
                position: "absolute", inset: 0,
                display: "flex", alignItems: "center", justifyContent: "center",
                background: "rgba(217,217,217,0.5)", border: "none", cursor: "pointer",
                fontFamily: "var(--font-body)", fontSize: 22, color: "#000",
                opacity: 0, transition: "opacity 0.2s",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = 1)}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = 0)}
            >
              {playing ? "⏸" : "▶"}
            </button>
          )}
        </div>

        {/* Progress */}
        {hasAudio && (
          <div className="scroll-card__progress-wrap">
            <div className="scroll-card__progress-bar" style={{ width: `${progress}%` }} />
          </div>
        )}

        {/* Meta */}
        <p className="scroll-card__artist">{track?.artist}</p>
        <h2 className="scroll-card__title">{track?.name}</h2>
        {contextLine && <p className="scroll-card__context">{contextLine}</p>}

        {/* YouTube fallback */}
        {hasYoutube && (
          <a
            href={`https://www.youtube.com/watch?v=${track.youtube_id}`}
            target="_blank" rel="noopener noreferrer"
            className="scroll-card__yt-badge"
          >
            watch on youtube →
          </a>
        )}

        {/* Actions */}
        <div className="scroll-card__actions">
          <button className="scroll-card__btn" onClick={onSkip} aria-label="Skip">
            <span>✕</span> skip
          </button>
          <button
            className={`scroll-card__btn scroll-card__btn--heart${isHearted ? " scroll-card__btn--hearted" : ""}`}
            onClick={onHeart}
            aria-label={isHearted ? "Unheart" : "Heart"}
          >
            <span>{isHearted ? "♥" : "♡"}</span> {isHearted ? "hearted" : "heart"}
          </button>
        </div>
      </div>

      {hasAudio && (
        <audio
          ref={audioRef}
          src={track.preview_url}
          preload="none"
          onEnded={() => setPlaying(false)}
          onError={() => setAudioError(true)}
        />
      )}
    </div>
  );
}
