import { useRef, useEffect, useState } from "react";

export function NowPlayingBar({ track, hasPrev, hasNext, onPrev, onNext }) {
  const audioRef = useRef(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (track?.preview_url) {
      audio.pause();
      audio.currentTime = 0;
      audio.load();
      audio.play()
        .then(() => setPlaying(true))
        .catch(() => setPlaying(false));
    } else {
      audio.pause();
      setPlaying(false);
    }
  }, [track]);

  function togglePlay() {
    const audio = audioRef.current;
    if (!audio || !track?.preview_url) return;
    if (playing) {
      audio.pause();
      setPlaying(false);
    } else {
      audio.play().then(() => setPlaying(true)).catch(() => setPlaying(false));
    }
  }

  if (!track) return null;

  return (
    <div className="now-playing-bar">
      {track.artwork_url && (
        <img
          src={track.artwork_url}
          alt={track.name}
          style={{ width: 36, height: 36, objectFit: "cover", flexShrink: 0 }}
        />
      )}

      <div className="now-playing-info">
        <p className="now-playing-title">{track.name}</p>
        <p className="now-playing-artist">{track.artist}</p>
      </div>

      <div className="now-playing-controls">
        <button
          className="np-ctrl-btn"
          onClick={onPrev}
          disabled={!hasPrev}
          aria-label="Previous"
        >
          ←
        </button>
        <button
          className="np-ctrl-btn"
          onClick={togglePlay}
          aria-label={playing ? "Pause" : "Play"}
          style={{ opacity: 1, fontSize: 18 }}
        >
          {playing ? "⏸" : "▶"}
        </button>
        <button
          className="np-ctrl-btn"
          onClick={onNext}
          disabled={!hasNext}
          aria-label="Next"
        >
          →
        </button>
      </div>

      {track.preview_url && (
        <audio
          ref={audioRef}
          onEnded={() => { setPlaying(false); onNext?.(); }}
          style={{ display: "none" }}
        >
          <source src={track.preview_url} type="audio/mpeg" />
        </audio>
      )}
    </div>
  );
}
