// frontend/src/api/client.js
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getUserId() {
  try {
    return localStorage.getItem("dscvr-user-id") || "";
  } catch {
    return "";
  }
}

function buildHeaders(extra = {}) {
  const headers = { "Content-Type": "application/json", ...extra };
  const uid = getUserId();
  if (uid) headers["X-User-ID"] = uid;
  return headers;
}

async function handleResponse(res) {
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail ?? data;
    const message =
      typeof detail === "string"
        ? detail
        : detail?.error || `Request failed with status ${res.status}`;
    const err = new Error(message);
    if (detail && typeof detail === "object") {
      err.code = detail.error;
      err.candidates = detail.candidates;
    }
    throw err;
  }
  return data;
}

// ─── Classic recommendations ──────────────────────────────────────────────────

export async function fetchRecommendations({ query, trackKey, rowIndex, topK = 10 }) {
  const payload = { top_k: topK };
  if (query) payload.query = query;
  if (trackKey) payload.track_key = trackKey;
  if (rowIndex !== undefined && rowIndex !== null) payload.row_index = rowIndex;

  const res = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function fetchSearch(q) {
  const res = await fetch(
    `${API_BASE_URL}/search?q=${encodeURIComponent(q)}`,
    { headers: buildHeaders() }
  );
  return handleResponse(res);
}

// ─── Interactions ─────────────────────────────────────────────────────────────

export async function postInteraction({ userId, trackId, interactionType, feature, tags = [] }) {
  const res = await fetch(`${API_BASE_URL}/interactions`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({
      user_id: userId,
      track_id: String(trackId),
      interaction_type: interactionType,
      feature,
      tags,
    }),
  });
  // 204 no content — just check ok
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || "Interaction failed");
  }
}

// ─── Feature: Soundtrack Your Life ───────────────────────────────────────────

export async function fetchSoundtrack(description) {
  const res = await fetch(`${API_BASE_URL}/soundtrack`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ description, user_id: getUserId() }),
  });
  return handleResponse(res);
}

// ─── Feature: Blind Taste Test ────────────────────────────────────────────────

export async function fetchBlindTasteTest() {
  const res = await fetch(`${API_BASE_URL}/blind-taste-test`, {
    headers: buildHeaders(),
  });
  return handleResponse(res);
}

export async function fetchBlindReveal(trackIndices) {
  const res = await fetch(`${API_BASE_URL}/blind-taste-test/reveal`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ track_indices: trackIndices }),
  });
  return handleResponse(res);
}

// ─── Feature: Time Machine ────────────────────────────────────────────────────

export async function fetchTimeMachine({ seedTrack, seedArtist, era }) {
  const res = await fetch(`${API_BASE_URL}/time-machine`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({
      seed_track: seedTrack,
      seed_artist: seedArtist,
      era,
      user_id: getUserId(),
    }),
  });
  return handleResponse(res);
}

// ─── Feature: Algorithmic Capture ────────────────────────────────────────────

export async function fetchAlgorithmicCapture() {
  const uid = getUserId();
  const res = await fetch(
    `${API_BASE_URL}/algorithmic-capture?user_id=${encodeURIComponent(uid)}`,
    { headers: buildHeaders() }
  );
  return handleResponse(res);
}

// ─── Feature: The Séance ─────────────────────────────────────────────────────

export async function fetchSeance(artist) {
  const res = await fetch(`${API_BASE_URL}/seance`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ artist, user_id: getUserId() }),
  });
  return handleResponse(res);
}
