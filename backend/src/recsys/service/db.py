# src/recsys/service/db.py
"""
Supabase client — initialised once at import time.
All DB calls are synchronous (supabase-py v2 sync client).
Use asyncio.to_thread() at the call site to avoid blocking the event loop.
"""
from __future__ import annotations

import os
import logging

log = logging.getLogger(__name__)

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_ANON_KEY", "")

    if not url or not key:
        log.warning("SUPABASE_URL / SUPABASE_ANON_KEY not set — DB features disabled")
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        log.info("Supabase client initialised ✓")
    except Exception as exc:
        log.error("Failed to initialise Supabase client: %s", exc)
        _client = None

    return _client


# ─── User helpers ─────────────────────────────────────────────────────────────

def register_user(user_id: str) -> None:
    """Upsert user row — silently no-ops if Supabase is unavailable."""
    db = get_client()
    if db is None:
        return
    try:
        db.table("users").upsert({"id": user_id}, on_conflict="id").execute()
    except Exception as exc:
        log.warning("register_user failed: %s", exc)


# ─── Interaction helpers ───────────────────────────────────────────────────────

_INTERACTION_WEIGHTS = {"heart": 1.0, "complete": 0.5, "skip": -0.3}


def log_interaction(
    user_id: str,
    track_id: str,
    interaction_type: str,
    feature: str | None = None,
) -> None:
    db = get_client()
    if db is None:
        return
    try:
        # Ensure user exists before inserting — prevents FK violation on first interaction
        db.table("users").upsert({"id": user_id}, on_conflict="id").execute()
        db.table("interactions").insert(
            {
                "user_id": user_id,
                "track_id": track_id,
                "interaction_type": interaction_type,
                "feature": feature,
            }
        ).execute()
    except Exception as exc:
        log.warning("log_interaction failed: %s", exc)


def update_taste_profile(
    user_id: str,
    tags: list[str],
    interaction_type: str,
) -> None:
    """Increment/decrement tag scores in the taste_profile table."""
    db = get_client()
    if db is None:
        return
    weight = _INTERACTION_WEIGHTS.get(interaction_type, 0)
    if weight == 0 or not tags:
        return
    try:
        # Fetch existing scores for these tags
        resp = (
            db.table("taste_profile")
            .select("tag,score")
            .eq("user_id", user_id)
            .in_("tag", tags)
            .execute()
        )
        existing = {r["tag"]: r["score"] for r in (resp.data or [])}
        rows = [
            {
                "user_id": user_id,
                "tag": tag,
                "score": existing.get(tag, 0.0) + weight,
                "updated_at": "now()",
            }
            for tag in tags
        ]
        db.table("taste_profile").upsert(
            rows, on_conflict="user_id,tag"
        ).execute()
    except Exception as exc:
        log.warning("update_taste_profile failed: %s", exc)


def get_taste_profile(user_id: str) -> list[dict]:
    """Return list of {tag, score} sorted by score desc."""
    db = get_client()
    if db is None:
        return []
    try:
        resp = (
            db.table("taste_profile")
            .select("tag,score")
            .eq("user_id", user_id)
            .order("score", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        log.warning("get_taste_profile failed: %s", exc)
        return []


def get_interaction_history(user_id: str, types: list[str] | None = None) -> list[dict]:
    """Return list of {track_id, interaction_type} for a user."""
    db = get_client()
    if db is None:
        return []
    try:
        q = (
            db.table("interactions")
            .select("track_id,interaction_type,feature,timestamp")
            .eq("user_id", user_id)
            .order("timestamp", desc=True)
        )
        if types:
            q = q.in_("interaction_type", types)
        resp = q.execute()
        return resp.data or []
    except Exception as exc:
        log.warning("get_interaction_history failed: %s", exc)
        return []
