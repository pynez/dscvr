# src/recsys/service/features/algorithmic_capture.py
"""
Feature 4 — Algorithmic Capture
Measures how homogenous vs diverse a user's taste is, then serves escape tracks.
"""
from __future__ import annotations

import logging
import math
from collections import Counter

import numpy as np

log = logging.getLogger(__name__)

MIN_INTERACTIONS = 5  # require at least this many to compute a meaningful score
NUM_DOMINANT = 5
NUM_SECONDARY = 8
NUM_ESCAPE = 15


def _get_tags_for_track(idx: int, recommender) -> list[str]:
    meta_df = recommender.meta_df
    if meta_df is None:
        return []
    meta = meta_df.iloc[idx]
    raw = meta.get("tags") if hasattr(meta, "get") else None
    if raw is None:
        return []
    if hasattr(raw, "tolist"):
        raw = raw.tolist()
    return [str(t).lower() for t in raw if t]


def _shannon_entropy(counts: Counter) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


async def run(user_id: str, recommender) -> dict:
    """
    1. Pull interaction history from Supabase
    2. Aggregate tags from hearted/completed tracks
    3. Compute capture score (1 - normalized entropy)
    4. Find escape tracks (outside dominant tags, within secondary overlap)
    5. Return score + breakdown + escape tracks
    """
    from src.recsys.service import db, preview_resolver
    import asyncio

    # ── Interaction history ────────────────────────────────────────────────────
    history = await asyncio.to_thread(
        db.get_interaction_history, user_id, ["heart", "complete"]
    )

    if len(history) < MIN_INTERACTIONS:
        return {
            "capture_score": None,
            "dominant_tags": [],
            "underexplored_tags": [],
            "escape_tracks": [],
            "insufficient_data": True,
            "interactions_needed": MIN_INTERACTIONS - len(history),
        }

    # ── Tag aggregation ────────────────────────────────────────────────────────
    tag_counter: Counter = Counter()
    track_indices: list[int] = []
    weight_map = {"heart": 1.0, "complete": 0.5}

    for interaction in history:
        try:
            idx = int(interaction["track_id"])
        except (ValueError, TypeError):
            continue
        track_indices.append(idx)
        tags = _get_tags_for_track(idx, recommender)
        w = weight_map.get(interaction["interaction_type"], 0.5)
        for tag in tags:
            tag_counter[tag] += w

    if not tag_counter:
        return {
            "capture_score": None,
            "dominant_tags": [],
            "underexplored_tags": [],
            "escape_tracks": [],
            "insufficient_data": True,
            "interactions_needed": MIN_INTERACTIONS,
        }

    # ── Capture score ──────────────────────────────────────────────────────────
    # capture_score = 1 - (entropy / log2(num_unique_tags))
    # High score → very captured (homogenous), Low score → diverse
    n_unique = len(tag_counter)
    max_entropy = math.log2(n_unique) if n_unique > 1 else 1.0
    entropy = _shannon_entropy(tag_counter)
    capture_score = round(max(0.0, min(1.0, 1.0 - (entropy / max_entropy))), 3)

    # ── Tag breakdown ──────────────────────────────────────────────────────────
    sorted_tags = tag_counter.most_common()
    dominant_tags = [t for t, _ in sorted_tags[:NUM_DOMINANT]]
    secondary_tags = [t for t, _ in sorted_tags[NUM_DOMINANT : NUM_DOMINANT + NUM_SECONDARY]]
    all_tags = [t for t, _ in sorted_tags]
    underexplored = [t for t in all_tags if t not in set(dominant_tags)][:10]

    # ── User taste vector (centroid of hearted track embeddings) ───────────────
    user_vector = recommender.get_user_taste_vector(track_indices)

    # ── Escape tracks ──────────────────────────────────────────────────────────
    escape_candidates = recommender.escape_route_tracks(
        dominant_tags=dominant_tags,
        secondary_tags=secondary_tags,
        user_vector=user_vector,
        top_k=NUM_ESCAPE,
    )
    escape_tracks = await preview_resolver.resolve_batch(escape_candidates)

    return {
        "capture_score": capture_score,
        "capture_percent": round(capture_score * 100),
        "dominant_tags": dominant_tags,
        "secondary_tags": secondary_tags,
        "underexplored_tags": underexplored,
        "tag_distribution": [
            {"tag": t, "score": round(s, 2)} for t, s in sorted_tags[:20]
        ],
        "escape_tracks": escape_tracks,
        "insufficient_data": False,
        "total_interactions": len(history),
    }
