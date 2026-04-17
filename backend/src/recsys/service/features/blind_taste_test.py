# src/recsys/service/features/blind_taste_test.py
"""
Feature 2 — Blind Taste Test
10 tracks returned with preview URLs but NO metadata.
After completion, /reveal returns full metadata + tags.
"""
from __future__ import annotations

import random
import logging
from typing import Any

log = logging.getLogger(__name__)

NUM_TRACKS = 10


def _is_playable(url) -> bool:
    """Return True only for non-DRM preview URLs the browser can actually play."""
    if not url or not isinstance(url, str) or url.strip() == "":
        return False
    return "itunes.apple.com" not in url and not url.endswith(".m4p")


def get_session(recommender) -> dict:
    """
    Select NUM_TRACKS tracks biased toward those with confirmed, playable preview URLs.
    Returns stripped payload (no name/artist/tags) — metadata added at reveal time.
    """
    meta_df = recommender.meta_df

    if meta_df is not None:
        has_preview = meta_df["preview_url"].apply(_is_playable)
        preview_indices = list(meta_df.index[has_preview])
    else:
        # Fall back to id_map
        preview_indices = [
            i for i, row in enumerate(recommender.id_map) if _is_playable(row.get("preview_url"))
        ]

    if len(preview_indices) < NUM_TRACKS:
        # Pad with any tracks
        all_indices = list(range(len(recommender.id_map)))
        extra = [i for i in all_indices if i not in set(preview_indices)]
        random.shuffle(extra)
        preview_indices = preview_indices + extra

    selected = random.sample(preview_indices, min(NUM_TRACKS, len(preview_indices)))

    tracks = []
    for idx in selected:
        row = recommender.id_map[idx]
        meta = meta_df.iloc[idx] if meta_df is not None else None
        preview = (
            (meta.get("preview_url") if hasattr(meta, "get") else None)
            or row.get("preview_url")
        )
        tracks.append({
            "row_index": int(idx),
            "preview_url": preview,
            # Deliberately omit: name, artist, tags, artwork_url
        })

    return {"tracks": tracks}


def reveal(track_indices: list[int], recommender) -> dict:
    """
    Given the row indices from the blind test session, return full metadata + tags.
    """
    meta_df = recommender.meta_df
    tracks = []
    for idx in track_indices:
        if idx < 0 or idx >= len(recommender.id_map):
            continue
        row = recommender.id_map[idx]
        meta = meta_df.iloc[idx] if meta_df is not None else None

        name = (meta.get("title") if hasattr(meta, "get") else None) or row.get("title", "")
        artist = (meta.get("artist") if hasattr(meta, "get") else None) or row.get("artist", "")
        artwork = (meta.get("artwork_url") if hasattr(meta, "get") else None) or row.get("artwork_url")
        preview = (meta.get("preview_url") if hasattr(meta, "get") else None) or row.get("preview_url")

        raw_tags = (meta.get("tags") if hasattr(meta, "get") else None) if meta is not None else []
        if raw_tags is None:
            raw_tags = []
        if hasattr(raw_tags, "tolist"):
            raw_tags = raw_tags.tolist()
        tags = [str(t) for t in raw_tags if t]

        tracks.append({
            "row_index": int(idx),
            "name": name,
            "artist": artist,
            "artwork_url": artwork,
            "preview_url": preview,
            "tags": tags[:10],
        })

    return {"tracks": tracks}
