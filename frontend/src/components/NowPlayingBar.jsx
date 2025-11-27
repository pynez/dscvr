// frontend/src/components/NowPlayingBar.jsx
import { useEffect, useRef, useState } from "react";

export function NowPlayingBar({ track, hasPrev, hasNext, onPrev, onNext }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  // Auto-play when the track or its preview changes
  useEffect(() => {
    if (!track || !track.preview_url || !audioRef.current) {
      setIsPlaying(false);
      return;
    }

    // Load new source and play
    audioRef.current.load();
    audioRef.current
      .play()
      .then(() => setIsPlaying(true))
      .catch(() => setIsPlaying(false));
  }, [track?.preview_url]);

  if (!track || !track.preview_url) {
    // If there's nothing to play, don't show the bar
    return null;
  }

  const handleTogglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    }
  };

  return (
    <div className="now-playing">
      <div className="now-playing-info">
        {track.artwork_url && (
          <img
            src={track.artwork_url}
            alt={`Artwork for ${track.name} by ${track.artist}`}
            className="now-playing-art"
          />
        )}
        <div className="now-playing-text">
          <span className="now-playing-label">Now playing</span>
          <div className="now-playing-title">{track.name}</div>
          <div className="now-playing-artist">{track.artist}</div>
        </div>
      </div>

      <div className="now-playing-controls">
        <button
          type="button"
          className="np-btn"
          onClick={onPrev}
          disabled={!hasPrev}
          aria-label="Previous track"
        >
          ⏮
        </button>
        <button
          type="button"
          className="np-btn np-btn-main"
          onClick={handleTogglePlay}
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? "⏸" : "▶"}
        </button>
        <button
          type="button"
          className="np-btn"
          onClick={onNext}
          disabled={!hasNext}
          aria-label="Next track"
        >
          ⏭
        </button>
      </div>

      {/* Hidden audio element controlled by the bar */}
      <audio ref={audioRef} className="now-playing-audio">
        <source src={track.preview_url} type="audio/mpeg" />
        Your browser does not support the audio element.
      </audio>
    </div>
  );
}
