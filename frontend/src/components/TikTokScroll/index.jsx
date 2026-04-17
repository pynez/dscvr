// frontend/src/components/TikTokScroll/index.jsx
import { useRef, useState, useEffect, useCallback } from "react";
import { TrackScrollCard } from "./TrackScrollCard";
import { useInteractions } from "../../hooks/useInteractions";

/**
 * TikTokScroll — universal playback mechanic.
 *
 * Props:
 *   tracks          — array of track objects
 *   feature         — string slug for interaction attribution
 *   getContextLine  — fn(track) → string shown on each card
 *   featureAccent   — hex color for feature-specific accent
 *   summaryCard     — React node rendered as the final card (optional)
 *   onComplete      — called when user reaches the summary card
 *   onHeartChange   — called with array of currently hearted track objects whenever it changes
 */
export function TikTokScroll({
  tracks = [],
  feature = "unknown",
  getContextLine = () => "",
  featureAccent = "#d49019",
  summaryCard = null,
  onComplete = () => {},
  onHeartChange = null,
}) {
  const { track: logInteraction } = useInteractions(feature);
  const containerRef = useRef(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [hearted, setHearted] = useState(new Set());
  const [skipped, setSkipped] = useState(new Set());

  // Bubble hearted tracks up to parent whenever the set changes
  useEffect(() => {
    if (onHeartChange) {
      onHeartChange(tracks.filter((_, i) => hearted.has(i)));
    }
  }, [hearted]);
  const totalCards = tracks.length + (summaryCard ? 1 : 0);

  // ── IntersectionObserver: track which card is visible ─────────────────────
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const cards = container.querySelectorAll(".scroll-card");
    if (!cards.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.6) {
            const idx = parseInt(entry.target.dataset.index, 10);
            setActiveIndex(idx);
            if (idx === totalCards - 1 && summaryCard) {
              onComplete();
            }
          }
        }
      },
      { root: container, threshold: 0.6 }
    );

    cards.forEach((card) => observer.observe(card));
    return () => observer.disconnect();
  }, [tracks, summaryCard, totalCards, onComplete]);

  // ── Log "complete" when a card is exited naturally (scrolled past) ─────────
  const prevActive = useRef(0);
  useEffect(() => {
    const prev = prevActive.current;
    if (activeIndex > prev && prev < tracks.length) {
      const t = tracks[prev];
      if (!skipped.has(prev) && !hearted.has(prev)) {
        logInteraction(t.row_index, "complete", t.tags || []);
      }
    }
    prevActive.current = activeIndex;
  }, [activeIndex]);

  // ── Swipe / wheel navigation ───────────────────────────────────────────────
  const touchStartY = useRef(null);

  const scrollToIndex = useCallback((idx) => {
    const container = containerRef.current;
    if (!container) return;
    const cards = container.querySelectorAll(".scroll-card");
    cards[idx]?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  function handleTouchStart(e) {
    touchStartY.current = e.touches[0].clientY;
  }

  function handleTouchEnd(e) {
    if (touchStartY.current === null) return;
    const delta = touchStartY.current - e.changedTouches[0].clientY;
    if (Math.abs(delta) < 40) return;
    const next = delta > 0
      ? Math.min(activeIndex + 1, totalCards - 1)
      : Math.max(activeIndex - 1, 0);
    scrollToIndex(next);
    touchStartY.current = null;
  }

  function handleHeart(track, idx) {
    setHearted((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
        logInteraction(track.row_index, "heart", track.tags || []);
      }
      return next;
    });
  }

  function handleSkip(track, idx) {
    setSkipped((prev) => new Set([...prev, idx]));
    logInteraction(track.row_index, "skip", track.tags || []);
    scrollToIndex(Math.min(idx + 1, totalCards - 1));
  }

  return (
    <div
      className="tiktok-scroll"
      ref={containerRef}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {tracks.map((track, i) => (
        <TrackScrollCard
          key={track.row_index ?? i}
          data-index={i}
          track={track}
          isActive={i === activeIndex}
          isHearted={hearted.has(i)}
          contextLine={getContextLine(track)}
          featureAccent={featureAccent}
          onHeart={() => handleHeart(track, i)}
          onSkip={() => handleSkip(track, i)}
        />
      ))}

      {summaryCard && (
        <TrackScrollCard
          key="summary"
          data-index={tracks.length}
          isSummaryCard
          isActive={activeIndex === tracks.length}
        >
          {summaryCard}
        </TrackScrollCard>
      )}

      {/* Dot navigation */}
      <div className="tiktok-scroll__dots">
        {Array.from({ length: totalCards }).map((_, i) => (
          <button
            key={i}
            className={`tiktok-scroll__dot ${i === activeIndex ? "tiktok-scroll__dot--active" : ""}`}
            style={i === activeIndex ? { backgroundColor: featureAccent } : {}}
            onClick={() => scrollToIndex(i)}
            aria-label={`Go to card ${i + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
