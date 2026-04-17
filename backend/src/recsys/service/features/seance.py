# src/recsys/service/features/seance.py
"""
Feature 5 — The Séance
Pick a deceased artist → DSCVR finds their living spiritual successors.
Uses Last.fm for similar artists + Gemini to filter living artists + reason connections.
"""
from __future__ import annotations

import asyncio
import logging
import os

import requests

log = logging.getLogger(__name__)

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"

_LIVING_FILTER_PROMPT = """\
I have a list of music artists. Some of them are deceased.

Original artist: {original_artist}

Candidate artists:
{artist_list}

Return ONLY valid JSON — an array of artist names that are LIVING (not deceased) from the list above.
Example: ["Artist One", "Artist Two"]

If you are uncertain about an artist, include them (err on the side of inclusion).
"""

_REASONING_PROMPT = """\
You are a music historian and critic. The artist "{original_artist}" has passed away.

I found these living artists who carry their sonic DNA forward:
{candidates_json}

Select the best 10-15 tracks from this list that most spiritually connect to {original_artist}.
For each track, write one sentence explaining the sonic or spiritual connection.

Return ONLY valid JSON in exactly this structure (no markdown fences):
{{
  "tracks": [
    {{
      "row_index": <integer>,
      "track_name": "<string>",
      "artist": "<string>",
      "connection": "<one sentence explaining the spiritual connection to {original_artist}>"
    }}
  ],
  "summary": "<2-3 sentences: who carries {original_artist}'s spirit forward today and why>"
}}
"""


def _lastfm_similar_artists(artist: str) -> list[str]:
    key = os.environ.get("LASTFM_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            LASTFM_URL,
            params={
                "method": "artist.getsimilar",
                "artist": artist,
                "api_key": key,
                "format": "json",
                "limit": 30,
            },
            timeout=8,
        )
        data = resp.json()
        similar = data.get("similarartists", {}).get("artist", [])
        return [a["name"] for a in similar]
    except Exception as exc:
        log.warning("Last.fm similar artists failed for '%s': %s", artist, exc)
        return []


async def run(artist: str, recommender) -> dict:
    """
    1. Get Last.fm similar artists
    2. Ask Gemini which are living
    3. Find their tracks in catalog via cosine similarity to original artist
    4. Ask Gemini to select 10-15 + write connection sentences
    5. Resolve previews
    """
    from src.recsys.service import gemini_client, preview_resolver
    import json

    # Step 1: Last.fm similar artists (sync → thread)
    similar_artists = await asyncio.to_thread(_lastfm_similar_artists, artist)

    if not similar_artists:
        return {
            "original_artist": artist,
            "tracks": [],
            "summary": f"Could not find similar artists for {artist} via Last.fm.",
        }

    # Step 2: Gemini filters for living artists
    living_prompt = _LIVING_FILTER_PROMPT.format(
        original_artist=artist,
        artist_list="\n".join(f"- {a}" for a in similar_artists),
    )
    try:
        living_artists: list[str] = await asyncio.to_thread(
            gemini_client.generate_json, living_prompt
        )
        if not isinstance(living_artists, list):
            living_artists = similar_artists  # fallback: use all
    except Exception as exc:
        log.warning("Gemini living filter failed: %s", exc)
        living_artists = similar_artists

    if not living_artists:
        living_artists = similar_artists[:15]

    # Step 3: Find tracks in catalog from living similar artists
    # Get original artist's tracks and compute centroid
    original_tracks = recommender.tracks_by_artist(artist, top_k=10)
    original_indices = [t["row_index"] for t in original_tracks]
    seed_vector = recommender.get_user_taste_vector(original_indices)

    # Collect catalog tracks from living similar artists
    living_set = {a.lower() for a in living_artists}
    candidates = []
    for j, row in enumerate(recommender.id_map):
        if row["artist"].lower() in living_set:
            candidates.append(recommender._row_to_dict(j, 0.0, include_tags=False))

    # Rank by cosine sim to original artist centroid
    if seed_vector is not None and candidates:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        idxs = [c["row_index"] for c in candidates]
        vecs = recommender.X[idxs]
        sims = cosine_similarity(seed_vector.reshape(1, -1), vecs)[0]
        for c, s in zip(candidates, sims):
            c["score"] = float(s)
        candidates.sort(key=lambda x: -x["score"])

    candidates = candidates[:40]

    if not candidates:
        return {
            "tracks": [],
            "summary": f"No tracks found in catalog from artists similar to {artist}.",
        }

    # Step 4: Gemini selects + reasons
    candidates_json = json.dumps(
        [
            {"row_index": c["row_index"], "track_name": c["name"], "artist": c["artist"]}
            for c in candidates
        ],
        indent=2,
    )
    reasoning_prompt = _REASONING_PROMPT.format(
        original_artist=artist,
        candidates_json=candidates_json,
    )
    try:
        gemini_result = await asyncio.to_thread(
            gemini_client.generate_json, reasoning_prompt
        )
    except Exception as exc:
        log.error("Gemini reasoning failed in seance: %s", exc)
        gemini_result = {
            "tracks": [
                {
                    "row_index": c["row_index"],
                    "track_name": c["name"],
                    "artist": c["artist"],
                    "connection": "",
                }
                for c in candidates[:10]
            ],
            "summary": "",
        }

    # Step 5: Merge + resolve previews
    idx_to_candidate = {c["row_index"]: c for c in candidates}
    tracks_out = []
    for t in gemini_result.get("tracks", []):
        row_idx = t.get("row_index")
        base = idx_to_candidate.get(row_idx, {})
        tracks_out.append({
            "row_index": row_idx,
            "name": t.get("track_name") or base.get("name", ""),
            "artist": t.get("artist") or base.get("artist", ""),
            "connection": t.get("connection", ""),
            "preview_url": base.get("preview_url"),
            "artwork_url": base.get("artwork_url"),
        })

    enriched = await preview_resolver.resolve_batch(tracks_out)

    return {
        "original_artist": artist,
        "tracks": enriched,
        "summary": gemini_result.get("summary", ""),
    }
