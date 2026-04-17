import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useFavorites } from "../../hooks/useFavorites";

const TRACK_A = { name: "Song A", artist: "Artist A", row_index: 1 };
const TRACK_B = { name: "Song B", artist: "Artist B", row_index: 2 };

describe("useFavorites", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    localStorage.clear();
  });

  it("starts with empty favorites", () => {
    const { result } = renderHook(() => useFavorites());
    expect(result.current.favorites).toEqual([]);
  });

  it("isFavorite returns false for unknown track", () => {
    const { result } = renderHook(() => useFavorites());
    expect(result.current.isFavorite(TRACK_A)).toBe(false);
  });

  it("toggleFavorite adds a track", () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite(TRACK_A));
    expect(result.current.favorites).toHaveLength(1);
    expect(result.current.isFavorite(TRACK_A)).toBe(true);
  });

  it("toggleFavorite removes a track when already saved", () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite(TRACK_A));
    act(() => result.current.toggleFavorite(TRACK_A));
    expect(result.current.favorites).toHaveLength(0);
    expect(result.current.isFavorite(TRACK_A)).toBe(false);
  });

  it("can save multiple different tracks", () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite(TRACK_A));
    act(() => result.current.toggleFavorite(TRACK_B));
    expect(result.current.favorites).toHaveLength(2);
    expect(result.current.isFavorite(TRACK_A)).toBe(true);
    expect(result.current.isFavorite(TRACK_B)).toBe(true);
  });

  it("removing one track does not remove others", () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite(TRACK_A));
    act(() => result.current.toggleFavorite(TRACK_B));
    act(() => result.current.toggleFavorite(TRACK_A)); // remove A
    expect(result.current.isFavorite(TRACK_A)).toBe(false);
    expect(result.current.isFavorite(TRACK_B)).toBe(true);
  });

  it("persists favorites to localStorage", () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite(TRACK_A));
    const stored = JSON.parse(localStorage.getItem("dscvr-favorites"));
    expect(stored).toHaveLength(1);
    expect(stored[0].name).toBe("Song A");
  });

  it("loads favorites from localStorage on init", () => {
    localStorage.setItem("dscvr-favorites", JSON.stringify([TRACK_A]));
    const { result } = renderHook(() => useFavorites());
    expect(result.current.favorites).toHaveLength(1);
    expect(result.current.isFavorite(TRACK_A)).toBe(true);
  });

  it("handles corrupt localStorage data gracefully", () => {
    localStorage.setItem("dscvr-favorites", "{{not-json}}");
    const { result } = renderHook(() => useFavorites());
    expect(result.current.favorites).toEqual([]);
  });

  it("clearFavorites empties the list", () => {
    const { result } = renderHook(() => useFavorites());
    act(() => result.current.toggleFavorite(TRACK_A));
    act(() => result.current.toggleFavorite(TRACK_B));
    act(() => result.current.clearFavorites());
    expect(result.current.favorites).toHaveLength(0);
  });

  it("deduplication is based on name+artist not row_index", () => {
    const { result } = renderHook(() => useFavorites());
    // Same name/artist, different row_index
    const dup = { ...TRACK_A, row_index: 999 };
    act(() => result.current.toggleFavorite(TRACK_A));
    act(() => result.current.toggleFavorite(dup)); // should remove, not add
    expect(result.current.favorites).toHaveLength(0);
  });
});
