import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useSession } from "../../hooks/useSession";

const STORAGE_KEY = "dscvr-user-id";

describe("useSession", () => {
  beforeEach(() => {
    localStorage.clear();
  });
  afterEach(() => {
    localStorage.clear();
  });

  it("returns a non-empty userId", () => {
    const { result } = renderHook(() => useSession());
    expect(result.current.userId).toBeTruthy();
    expect(typeof result.current.userId).toBe("string");
  });

  it("userId looks like a UUID", () => {
    const { result } = renderHook(() => useSession());
    const uuid = result.current.userId;
    expect(uuid).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    );
  });

  it("persists userId to localStorage on first call", () => {
    renderHook(() => useSession());
    expect(localStorage.getItem(STORAGE_KEY)).toBeTruthy();
  });

  it("returns the same userId on subsequent renders", () => {
    const { result: r1 } = renderHook(() => useSession());
    const { result: r2 } = renderHook(() => useSession());
    expect(r1.current.userId).toBe(r2.current.userId);
  });

  it("reuses an existing ID from localStorage", () => {
    const existingId = "test-existing-uuid-1234";
    localStorage.setItem(STORAGE_KEY, existingId);
    const { result } = renderHook(() => useSession());
    expect(result.current.userId).toBe(existingId);
  });

  it("does not overwrite an existing localStorage ID", () => {
    const existingId = "my-stable-id";
    localStorage.setItem(STORAGE_KEY, existingId);
    renderHook(() => useSession());
    expect(localStorage.getItem(STORAGE_KEY)).toBe(existingId);
  });
});
