// frontend/src/hooks/useFavorites.js
import { useEffect, useState } from "react";

const FAV_KEY = "dscvr-favorites";

// Simple "key" for deduping tracks
function trackKey(track) {
  return `${track.name} — ${track.artist}`;
}

export function useFavorites() {
  const [favorites, setFavorites] = useState(() => {
    if (typeof window === "undefined") return [];
    try {
      const raw = window.localStorage.getItem(FAV_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(FAV_KEY, JSON.stringify(favorites));
    } catch {
      // ignore storage errors
    }
  }, [favorites]);

  function isFavorite(track) {
    const key = trackKey(track);
    return favorites.some((f) => trackKey(f) === key);
  }

  function toggleFavorite(track) {
    const key = trackKey(track);
    setFavorites((prev) => {
      const exists = prev.some((f) => trackKey(f) === key);
      if (exists) {
        return prev.filter((f) => trackKey(f) !== key);
      }
      // When adding, you can drop score if you want. We'll keep it.
      return [...prev, track];
    });
  }

  function clearFavorites() {
    setFavorites([]);
  }

  return { favorites, isFavorite, toggleFavorite, clearFavorites };
}