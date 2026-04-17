# src/recsys/service/features/time_machine.py
"""
Feature 3 — The Time Machine
Seed track + era → finds what user would have been obsessed with in that era.
Uses era-tag filtering on cosine similarity. No external API calls at request time.
"""
from __future__ import annotations

import asyncio
import logging

log = logging.getLogger(__name__)

# Map frontend era values to Last.fm tag synonyms
ERA_TAG_MAP: dict[str, list[str]] = {
    "60s": ["60s", "1960s", "sixties", "classic rock", "soul", "motown"],
    "70s": ["70s", "1970s", "seventies", "classic rock", "funk", "disco", "soul"],
    "80s": ["80s", "1980s", "eighties", "new wave", "synth-pop", "post-punk", "classic pop"],
    "90s": ["90s", "1990s", "nineties", "alternative", "grunge", "britpop", "r&b", "hip-hop"],
    "00s": ["00s", "2000s", "2000s", "indie", "pop punk", "emo", "nu-metal"],
}


async def run(
    seed_track: str,
    seed_artist: str,
    era: str,
    recommender,
    search_index,
) -> dict:
    """
    1. Resolve seed track to row_index via search
    2. Run era-filtered cosine similarity
    3. Resolve previews
    4. Return tracks + era summary
    """
    from src.recsys.service import preview_resolver

    era_tags = ERA_TAG_MAP.get(era, ERA_TAG_MAP["80s"])

    # Resolve seed track
    seed_idx = None
    try:
        best_idx, best_score, _ = search_index.match(
            f"{seed_track} {seed_artist}", limit=1
        )
        if best_idx is not None and best_score >= 70:
            seed_idx = best_idx
    except Exception as exc:
        log.warning("Time machine seed resolution failed: %s", exc)

    if seed_idx is None:
        return {
            "tracks": [],
            "era": era,
            "summary": f"Could not find '{seed_track}' by {seed_artist} in the catalog.",
        }

    # Era-filtered cosine similarity
    candidates = recommender.similar_by_index_era(
        seed_idx, era_tags=era_tags, top_k=15, max_per_artist=2
    )

    if not candidates:
        return {
            "tracks": [],
            "era": era,
            "summary": f"No {era} tracks found similar to {seed_track} by {seed_artist}.",
        }

    enriched = await preview_resolver.resolve_batch(candidates)

    summary = (
        f"If you were obsessed with {seed_track} by {seed_artist} you would have been "
        f"deep in these {era} tracks."
    )

    return {
        "tracks": enriched,
        "era": era,
        "seed_track": seed_track,
        "seed_artist": seed_artist,
        "summary": summary,
    }
