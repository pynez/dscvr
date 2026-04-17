# src/recsys/service/features/soundtrack.py
"""
Feature 1 — Soundtrack Your Life
User describes a moment/feeling → cosine candidates → Gemini selects + reasons → previews resolved.
"""
from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """\
You are a music curator helping someone find the perfect soundtrack for a personal moment.

The user described:
\"{description}\"

Here are {n} candidate tracks from the catalog:
{candidates_json}

Select the best 10-15 tracks that fit this moment. For each track, write one sentence explaining why it fits.

Return ONLY valid JSON in exactly this structure (no prose, no markdown fences):
{{
  "tracks": [
    {{
      "row_index": <integer from candidate>,
      "track_name": "<string>",
      "artist": "<string>",
      "reasoning": "<one sentence why this fits the moment>"
    }}
  ],
  "summary": "<2-3 sentences describing the playlist as a whole and how it captures the moment>"
}}
"""


async def run(
    description: str,
    recommender,
    user_id: str | None = None,
) -> dict:
    """
    1. Vectorize description → 35 cosine candidates
    2. Gemini selects + reasons for 10-15
    3. Resolve previews concurrently
    4. Return full payload
    """
    from src.recsys.service import gemini_client, preview_resolver
    import json

    # Step 1: cosine candidates
    candidates = recommender.similar_by_text(
        description, top_k=35, max_per_artist=3, include_tags=False
    )
    if not candidates:
        return {"tracks": [], "summary": "No matching tracks found for that description."}

    candidates_json = json.dumps(
        [
            {"row_index": c["row_index"], "track_name": c["name"], "artist": c["artist"]}
            for c in candidates
        ],
        indent=2,
    )

    prompt = _PROMPT_TEMPLATE.format(
        description=description,
        n=len(candidates),
        candidates_json=candidates_json,
    )

    # Step 2: Gemini call (sync → thread)
    try:
        gemini_result = await asyncio.to_thread(gemini_client.generate_json, prompt)
    except Exception as exc:
        log.error("Gemini call failed in soundtrack: %s", exc)
        # Graceful fallback: return top-10 candidates without reasoning
        gemini_result = {
            "tracks": [
                {"row_index": c["row_index"], "track_name": c["name"], "artist": c["artist"], "reasoning": ""}
                for c in candidates[:10]
            ],
            "summary": "",
        }

    # Build index lookup for enrichment
    idx_to_candidate = {c["row_index"]: c for c in candidates}

    # Step 3: Merge catalog data + resolve previews
    tracks_out = []
    for t in gemini_result.get("tracks", []):
        row_idx = t.get("row_index")
        base = idx_to_candidate.get(row_idx, {})
        tracks_out.append({
            "row_index": row_idx,
            "name": t.get("track_name") or base.get("name", ""),
            "artist": t.get("artist") or base.get("artist", ""),
            "reasoning": t.get("reasoning", ""),
            "preview_url": base.get("preview_url"),
            "artwork_url": base.get("artwork_url"),
        })

    enriched = await preview_resolver.resolve_batch(tracks_out)

    return {
        "tracks": enriched,
        "summary": gemini_result.get("summary", ""),
    }
