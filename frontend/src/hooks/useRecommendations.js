// frontend/src/hooks/useRecommendations.js
import { useState } from "react";
import { fetchRecommendations } from "../api/client";

export function useRecommendations() {
  const [query, setQuery] = useState("");
  const [matchedTrack, setMatchedTrack] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function runRecommendation(payload) {
    setIsLoading(true);
    setError("");
    setRecommendations([]);
    setMatchedTrack(null);
    setCandidates([]);

    try {
      const data = await fetchRecommendations(payload);
      setMatchedTrack({
        title: data.resolved_name,
        artist: data.resolved_artist,
      });
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error(err);
      if (err.code === "AMBIGUOUS_QUERY" && err.candidates?.length) {
        setCandidates(err.candidates);
        setError("We haven't DSCVRed that one yet. Here's some recommendations.");
      } else {
        setError(err.message || "Something went wrong.");
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function submit(newQuery) {
    const q = newQuery ?? query;
    if (!q?.trim()) return;
    setQuery(q);
    await runRecommendation({ query: q, topK: 12 });
  }

  async function chooseCandidate(candidate) {
    if (!candidate) return;
    await runRecommendation({
      query,
      trackKey: candidate.track_key,
      rowIndex: candidate.row_index,
      topK: 12,
    });
  }

  return {
    query,
    setQuery,
    submit,
    chooseCandidate,
    matchedTrack,
    recommendations,
    candidates,
    isLoading,
    error,
  };
}
