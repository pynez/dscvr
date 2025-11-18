from __future__ import annotations
import os, time, requests
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from dotenv import load_dotenv
import json
import requests
from pathlib import Path
from src.recsys.config import PROC, SEEDS

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

    if not r.text.strip():
        raise RuntimeError(
            f"Last.fm returned empty body for params={params}. "
            f"Status={r.status_code}, headers={r.headers}"
        )
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
    
def load_seed_groups(seed_dir: Path | None = None) -> dict[str, list[tuple[str, str]]]:
    """
    Load seed tracks from JSON files in data/seeds.

    Each JSON file should be an array of objects:
      { "title": "...", "artist": "..." }

    Returns:
      { "rnb": [("Snooze", "SZA"), ...],
        "alt_rnb": [...],
        ... }
    """
    seed_dir = seed_dir or SEEDS
    groups: dict[str, list[tuple[str, str]]] = {}

    if not seed_dir.exists():
        raise RuntimeError(f"Seed directory does not exist: {seed_dir}")

    for path in sorted(seed_dir.glob("*.json")):
        group_name = path.stem  # e.g., "rnb", "alt_rnb"
        try:
            with path.open() as f:
                raw = json.load(f)
        except Exception as e:
            print(f"[load_seed_groups] ERROR reading {path}: {e}")
            continue

        seeds: list[tuple[str, str]] = []
        # Accept both [{title,artist}, ...] and [["title","artist"], ...]
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    title = item.get("title")
                    artist = item.get("artist")
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    title, artist = item[0], item[1]
                else:
                    continue
                if title and artist:
                    seeds.append((str(title), str(artist)))

        if seeds:
            groups[group_name] = seeds
            print(f"[load_seed_groups] {group_name}: loaded {len(seeds)} seeds from {path}")
        else:
            print(f"[load_seed_groups] WARNING: no valid seeds in {path}")

    if not groups:
        raise RuntimeError(f"No seed JSON files found in {seed_dir}")

    return groups

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

def build_lastfm_dataset(
    seed_dir: Path | None = None,
    out_path: str | Path = PROC / "tracks_lastfm.parquet",
) -> str:
    """
    Build a unified Last.fm-based catalog from all seed JSON files.

    - Reads seed groups from data/seeds/*.json
    - For each group, calls collect_from_seeds(...)
    - Adds a 'seed_group' column with the JSON filename stem (e.g. 'rnb')
    - Concatenates all groups and drops duplicate (title, artist) combos
    """
    seed_dir = seed_dir or SEEDS
    groups = load_seed_groups(seed_dir)

    frames: list[pd.DataFrame] = []

    for group_name, seeds in groups.items():
        print(f"[build_lastfm_dataset] collecting from group '{group_name}' with {len(seeds)} seeds")
        if not seeds:
            continue

        # collect_from_seeds is your existing function that uses track.getSimilar, tags, iTunes, etc.
        df_group = collect_from_seeds(seeds, seed_label=f"seed:{group_name}")
        df_group = df_group.copy()
        df_group["seed_group"] = group_name
        frames.append(df_group)

    if not frames:
        raise RuntimeError("No data collected from any seed groups")

    df_all = pd.concat(frames, ignore_index=True)

    before = len(df_all)
    df_all = df_all.drop_duplicates(subset=["title", "artist"])
    after = len(df_all)
    print(f"[build_lastfm_dataset] deduped from {before} to {after} rows")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_parquet(out_path, index=False)
    print(f"✅ Wrote {len(df_all)} rows → {out_path}")
    return str(out_path)

def tag_get_top_tracks(tag: str, limit: int = 100) -> list[dict]:
    """
    Get top tracks for a given Last.fm tag.
    Each item is a dict with 'title' and 'artist'.
    """
    # NOTE: method name is usually 'tag.gettoptracks' in examples,
    # but Last.fm is case-insensitive here. We'll be safe either way.
    res = _lastfm({
        "method": "tag.gettoptracks",
        "tag": tag,
        "limit": limit,
        "autocorrect": 1,
    })

    top = res.get("toptracks") or res.get("topTracks") or {}
    tracks = top.get("track") or top.get("tracks") or []

    # Some Last.fm responses use a single dict instead of a list when limit=1
    if isinstance(tracks, dict):
        tracks = [tracks]

    out: list[dict] = []
    for t in tracks:
        if not isinstance(t, dict):
            continue
        name = t.get("name") or ""
        artist_obj = t.get("artist") or {}
        if isinstance(artist_obj, dict):
            artist_name = artist_obj.get("name") or ""
        else:
            artist_name = str(artist_obj) if artist_obj else ""
        if name and artist_name:
            out.append({"title": name, "artist": artist_name})

    if not out:
        # Helpful debug so we can see if a tag is just bad
        print(f"[tag_get_top_tracks] WARNING: no top tracks for tag '{tag}'. "
              f"toptracks keys={list(top.keys()) if isinstance(top, dict) else type(top)}")

    return out