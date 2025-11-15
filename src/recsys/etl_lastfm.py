from __future__ import annotations
import os, time, requests
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from dotenv import load_dotenv

from src.recsys.config import PROC

LASTFM = "https://ws.audioscrobbler.com/2.0/"
ITUNES = "https://itunes.apple.com/search"

@dataclass
class TrackRow:
    title: str
    artist: str
    mbid: Optional[str]
    match_score: Optional[float]
    tags: list[str]
    similar: list[dict]          # [{"title":..., "artist":...}, ...]
    preview_url: Optional[str]   # from iTunes
    artwork_url: Optional[str]   # from iTunes
    source: str                  # e.g., "seed:rnb"

def _lastfm(params: dict) -> dict:
    """
    Call Last.fm and return JSON. Adds a User-Agent and prints helpful errors when
    the response isn't JSON (e.g., invalid key, HTML error page, rate limit).
    """
    load_dotenv()
    k = os.getenv("LASTFM_API_KEY")
    if not k:
        raise RuntimeError("Missing LASTFM_API_KEY in .env")

    q = {"api_key": k, "format": "json", **params}
    headers = {
        "User-Agent": "dscvr/0.1 (contact: pynej001@umn.edu)"  # put any contact string
    }
    r = requests.get(LASTFM, params=q, headers=headers, timeout=20)

    # If Last.fm returns a non-200, raise with body
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"Last.fm HTTP {r.status_code}: {r.text[:300]}") from e

    # Ensure we really got JSON; otherwise show first 300 chars for debugging
    ctype = r.headers.get("Content-Type","")
    if "json" not in ctype.lower():
        snippet = (r.text or "")[:300]
        raise RuntimeError(f"Last.fm returned non-JSON (Content-Type={ctype}). First 300 chars:\n{snippet}")

    data = r.json()

    # Last.fm sometimes returns an 'error' field in JSON
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"Last.fm error {data['error']}: {data.get('message')}")
    return data


def _itunes_preview(title: str, artist: str) -> tuple[Optional[str], Optional[str]]:
    # Use iTunes Search to get artwork + 30s preview for UI / optional audio embeddings
    q = f"{title} {artist}"
    r = requests.get(ITUNES, params={"term": q, "media": "music", "limit": 1}, timeout=15)
    if r.status_code != 200: return None, None
    items = r.json().get("results", [])
    if not items: return None, None
    it = items[0]
    return it.get("previewUrl"), it.get("artworkUrl100")

def track_search(title: str, artist: Optional[str] = None) -> dict:
    if artist:
        return _lastfm({"method":"track.getInfo", "track": title, "artist": artist})
    # fallback: search then pick best match
    res = _lastfm({"method":"track.search", "track": title, "limit": 1})
    return res

def track_get_similar(title: str, artist: str, limit=20) -> list[dict]:
    res = _lastfm({"method":"track.getSimilar", "track": title, "artist": artist, "limit": limit})
    tracks = (res.get("similartracks") or {}).get("track", [])
    out = []
    for t in tracks:
        out.append({"title": t.get("name",""), "artist": (t.get("artist") or {}).get("name","")})
    return out

def track_get_tags(title: str, artist: str, kind="track") -> list[str]:
    params = {"artist": artist, "track": title} if kind=="track" else {"artist": artist}
    method = "track.getTopTags" if kind=="track" else "artist.getTopTags"
    try:
        res = _lastfm({"method": method, **params})
        taglist = (res.get("toptags") or {}).get("tag", [])
        return [t.get("name","") for t in taglist[:20]]
    except Exception:
        return []

def collect_from_seeds(seeds: list[tuple[str,str]], seed_label="seed:rnb") -> pd.DataFrame:
    rows: List[TrackRow] = []
    for title, artist in seeds:
        sim = track_get_similar(title, artist, limit=25)
        tags = list(dict.fromkeys(
            track_get_tags(title, artist, "track") +
            track_get_tags(title, artist, "artist")
        ))
        prev, art = _itunes_preview(title, artist)
        rows.append(TrackRow(
            title=title, artist=artist, mbid=None, match_score=None,
            tags=tags, similar=sim, preview_url=prev, artwork_url=art, source=seed_label
        ))
        time.sleep(0.15)

        # Also collect the similar tracks themselves (light metadata + tags)
        for s in sim[:15]:
            t_tags = list(dict.fromkeys(
                track_get_tags(s["title"], s["artist"], "track") +
                track_get_tags(s["title"], s["artist"], "artist")
            ))
            prev2, art2 = _itunes_preview(s["title"], s["artist"])
            rows.append(TrackRow(
                title=s["title"], artist=s["artist"], mbid=None, match_score=None,
                tags=t_tags, similar=[], preview_url=prev2, artwork_url=art2, source="similar"
            ))
            time.sleep(0.12)
    df = pd.DataFrame([r.__dict__ for r in rows]).drop_duplicates(subset=["title","artist"])
    return df

def build_lastfm_dataset(out_path: str = str(PROC / "tracks_lastfm.parquet")) -> str:
    # Start tiny (R&B); you can expand later or load from a config file
    rnb_seeds = [
        ("Snooze","SZA"),
        ("CUFF IT","Beyoncé"),
        ("Blinding Lights","The Weeknd"),
        ("Bad Habit","Steve Lacy"),
        ("Leave The Door Open","Bruno Mars")
    ]
    df = collect_from_seeds(rnb_seeds, seed_label="seed:rnb")
    df.to_parquet(out_path, index=False)
    print(f"✅ Wrote {len(df)} rows → {out_path}")
    return out_path
