# src/recsys/service/preview_resolver.py
"""
Preview Resolution Service — used by every feature.

Priority:
  1. Deezer public API  → 30s MP3 preview + cover art
  2. YouTube Data API   → embeddable video ID (fallback if no Deezer preview)

Cover art:  Deezer album cover → existing artwork_url from catalog → None

All public; no Deezer API key required.
"""
from __future__ import annotations

import asyncio
import logging
import os
import urllib.parse

import httpx
from rapidfuzz import fuzz

log = logging.getLogger(__name__)

DEEZER_SEARCH = "https://api.deezer.com/search"
YOUTUBE_SEARCH = "https://www.googleapis.com/youtube/v3/search"

_MATCH_THRESHOLD = 60  # fuzz score out of 100


def _fuzz_score(a: str, b: str) -> float:
    return fuzz.token_set_ratio(a.lower(), b.lower())


def _is_drm_url(url: str | None) -> bool:
    """Return True for Apple FairPlay DRM previews — unplayable in all browsers."""
    if not url:
        return False
    return "itunes.apple.com" in url or url.endswith(".m4p")


async def _resolve_single(
    client: httpx.AsyncClient,
    track_name: str,
    artist: str,
    existing_preview: str | None = None,
    existing_artwork: str | None = None,
) -> dict:
    """Resolve one track. Returns dict with preview_url, artwork_url, youtube_id."""
    # Strip DRM-locked iTunes previews — keeping them is worse than null
    # because the browser will silently fail to load them.
    if _is_drm_url(existing_preview):
        existing_preview = None

    preview_url = existing_preview
    artwork_url = existing_artwork
    youtube_id = None

    # ── 1. Deezer ────────────────────────────────────────────────────────────
    try:
        q = urllib.parse.quote(f"{track_name} {artist}")
        resp = await client.get(f"{DEEZER_SEARCH}?q={q}", timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            best = None
            best_score = 0.0
            for item in data[:10]:
                t_score = _fuzz_score(item.get("title", ""), track_name)
                a_score = _fuzz_score(item.get("artist", {}).get("name", ""), artist)
                combined = (t_score + a_score) / 2
                if combined > best_score:
                    best_score = combined
                    best = item
            if best and best_score >= _MATCH_THRESHOLD:
                if best.get("preview"):
                    preview_url = best["preview"]
                cover = (
                    best.get("album", {}).get("cover_medium")
                    or best.get("album", {}).get("cover")
                )
                if cover:
                    artwork_url = cover
    except Exception as exc:
        log.debug("Deezer lookup failed for '%s': %s", track_name, exc)

    # ── 2. YouTube fallback (only if no Deezer preview) ─────────────────────
    yt_key = os.environ.get("YOUTUBE_DATA_API_KEY", "")
    if not preview_url and yt_key:
        try:
            q = urllib.parse.quote(f"{track_name} {artist} official audio")
            params = {
                "part": "snippet",
                "q": q,
                "type": "video",
                "maxResults": 1,
                "key": yt_key,
            }
            resp = await client.get(YOUTUBE_SEARCH, params=params, timeout=5)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    youtube_id = items[0]["id"].get("videoId")
                    # Use YouTube thumbnail as artwork fallback
                    if not artwork_url:
                        thumbs = items[0].get("snippet", {}).get("thumbnails", {})
                        thumb = (
                            thumbs.get("high", {}).get("url")
                            or thumbs.get("medium", {}).get("url")
                        )
                        if thumb:
                            artwork_url = thumb
        except Exception as exc:
            log.debug("YouTube lookup failed for '%s': %s", track_name, exc)

    return {
        "preview_url": preview_url,
        "artwork_url": artwork_url,
        "youtube_id": youtube_id,
    }


async def resolve_batch(tracks: list[dict]) -> list[dict]:
    """
    Enrich a list of track dicts with resolved preview_url, artwork_url, youtube_id.
    Each dict must have 'name' (or 'track_name') and 'artist'.
    Existing preview_url / artwork_url are passed through and only overridden
    if a fresher source is found.

    Returns the same list with each dict updated in place (and returned).
    """
    async with httpx.AsyncClient() as client:
        tasks = []
        for t in tracks:
            name = t.get("name") or t.get("track_name") or ""
            artist = t.get("artist") or ""
            tasks.append(
                _resolve_single(
                    client,
                    name,
                    artist,
                    existing_preview=t.get("preview_url"),
                    existing_artwork=t.get("artwork_url"),
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)

    enriched = []
    for track, result in zip(tracks, results):
        out = dict(track)
        if isinstance(result, Exception):
            log.warning("resolve_batch error for '%s': %s", track.get("name"), result)
        else:
            out["preview_url"] = result["preview_url"]
            out["artwork_url"] = result["artwork_url"]
            out["youtube_id"] = result.get("youtube_id")
        enriched.append(out)

    return enriched
