import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

// Mock global fetch before importing the client
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

// Helpers to simulate fetch responses
function mockResponse(body, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
}

function mockEmptyResponse(status = 204) {
  return Promise.resolve({
    ok: true,
    status,
    json: () => Promise.reject(new Error("no body")),
  });
}

// Seed a userId in localStorage for header tests
beforeEach(() => {
  localStorage.setItem("dscvr-user-id", "test-user-abc");
  mockFetch.mockClear();
});
afterEach(() => {
  localStorage.clear();
});

// ── fetchRecommendations ───────────────────────────────────────────────────

describe("fetchRecommendations", () => {
  it("POSTs to /recommend with row_index", async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ recommendations: [] }));
    const { fetchRecommendations } = await import("../../api/client.js");
    await fetchRecommendations({ rowIndex: 5 });
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain("/recommend");
    expect(JSON.parse(opts.body)).toMatchObject({ row_index: 5 });
  });

  it("includes X-User-ID header", async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ recommendations: [] }));
    const { fetchRecommendations } = await import("../../api/client.js");
    await fetchRecommendations({ rowIndex: 0 });
    const headers = mockFetch.mock.calls[0][1].headers;
    expect(headers["X-User-ID"]).toBe("test-user-abc");
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ detail: "Song not found in catalog." }, 404)
    );
    const { fetchRecommendations } = await import("../../api/client.js");
    await expect(fetchRecommendations({ rowIndex: 999 })).rejects.toThrow(
      "Song not found in catalog."
    );
  });
});

// ── postInteraction ────────────────────────────────────────────────────────

describe("postInteraction", () => {
  it("POSTs to /interactions", async () => {
    mockFetch.mockReturnValueOnce(mockEmptyResponse(204));
    const { postInteraction } = await import("../../api/client.js");
    await postInteraction({
      userId: "u1",
      trackId: "5",
      interactionType: "heart",
      feature: "soundtrack",
      tags: ["pop"],
    });
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/interactions");
  });

  it("sends correct body", async () => {
    mockFetch.mockReturnValueOnce(mockEmptyResponse(204));
    const { postInteraction } = await import("../../api/client.js");
    await postInteraction({
      userId: "u1",
      trackId: "5",
      interactionType: "heart",
      feature: "soundtrack",
      tags: ["pop"],
    });
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body).toMatchObject({
      user_id: "u1",
      track_id: "5",
      interaction_type: "heart",
      feature: "soundtrack",
      tags: ["pop"],
    });
  });

  it("throws on non-ok response", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ detail: "Interaction failed" }, 500)
    );
    const { postInteraction } = await import("../../api/client.js");
    await expect(
      postInteraction({
        userId: "u1",
        trackId: "5",
        interactionType: "heart",
        feature: null,
        tags: [],
      })
    ).rejects.toThrow();
  });
});

// ── fetchSoundtrack ────────────────────────────────────────────────────────

describe("fetchSoundtrack", () => {
  it("POSTs to /soundtrack", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ tracks: [], summary: "great" })
    );
    const { fetchSoundtrack } = await import("../../api/client.js");
    await fetchSoundtrack("a rainy evening");
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/soundtrack");
  });

  it("sends the description in body", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ tracks: [], summary: "" })
    );
    const { fetchSoundtrack } = await import("../../api/client.js");
    await fetchSoundtrack("my description");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.description).toBe("my description");
  });
});

// ── fetchSearch ────────────────────────────────────────────────────────────

describe("fetchSearch", () => {
  it("GETs /search with encoded query", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ query: "SZA", results: [] })
    );
    const { fetchSearch } = await import("../../api/client.js");
    await fetchSearch("SZA Snooze");
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/search");
    expect(url).toContain("SZA");
  });
});

// ── fetchBlindTasteTest ────────────────────────────────────────────────────

describe("fetchBlindTasteTest", () => {
  it("GETs /blind-taste-test", async () => {
    mockFetch.mockReturnValueOnce(mockResponse({ tracks: [] }));
    const { fetchBlindTasteTest } = await import("../../api/client.js");
    await fetchBlindTasteTest();
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/blind-taste-test");
  });
});

// ── fetchTimeMachine ───────────────────────────────────────────────────────

describe("fetchTimeMachine", () => {
  it("POSTs to /time-machine with correct body", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ tracks: [], era: "80s", seed_track: "t", seed_artist: "a", summary: "" })
    );
    const { fetchTimeMachine } = await import("../../api/client.js");
    await fetchTimeMachine({ seedTrack: "Bohemian Rhapsody", seedArtist: "Queen", era: "70s" });
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body).toMatchObject({
      seed_track: "Bohemian Rhapsody",
      seed_artist: "Queen",
      era: "70s",
    });
  });
});

// ── fetchSeance ────────────────────────────────────────────────────────────

describe("fetchSeance", () => {
  it("POSTs to /seance with artist name", async () => {
    mockFetch.mockReturnValueOnce(
      mockResponse({ original_artist: "Kurt Cobain", tracks: [], summary: "" })
    );
    const { fetchSeance } = await import("../../api/client.js");
    await fetchSeance("Kurt Cobain");
    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.artist).toBe("Kurt Cobain");
  });
});
