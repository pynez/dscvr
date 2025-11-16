// frontend/src/hooks/useRecommendations.js
import { useState } from "react";
import { fetchRecommendations } from "../api/client";

export function useRecommendations() {
  const [query, setQuery] = useState("");
  const [matchedTrack, setMatchedTrack] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(newQuery) {
    const q = newQuery ?? query;
    if (!q.trim()) return;

    setIsLoading(true);
    setError("");
    setRecommendations([]);
    setMatchedTrack(null);

    try {
      const data = await fetchRecommendations(q, 10);
      setMatchedTrack({
        title: data.resolved_name,
        artist: data.resolved_artist,
      });
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error(err);
      setError(err.message || "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  return {
    query,
    setQuery,
    submit,
    matchedTrack,
    recommendations,
    isLoading,
    error,
  };
}
