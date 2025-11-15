from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional, Tuple
from time import sleep
import os
import math
import logging

import pandas as pd
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.recsys.config import RAW, PROC, DEFAULT_MARKET

# ---------- Logging ----------
logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(ch)

# ---------- Models ----------
@dataclass
class TrackMeta:
    track_id: str
    name: str
    artist: str
    artist_id: str | None
    album: str | None
    album_id: str | None
    isrc: str | None
    seed_tag: str  # where this came from (playlist/search/artist/etc.)

# ---------- Auth ----------
def spotify_client() -> spotipy.Spotify:
    load_dotenv()
    cid = os.getenv("SPOTIFY_CLIENT_ID")
    secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not cid or not secret:
        raise RuntimeError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in .env")
    auth = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    return spotipy.Spotify(auth_manager=auth)

# ---------- Utilities ----------
def _safe_next(sp: spotipy.Spotify, results: dict, pause: float = 0.2):
    """Paginate safely with a tiny delay to be polite."""
    nxt = results.get("next")
    if nxt:
        sleep(pause)
        return sp.next(results)
    return None

def _dedupe_tracks(rows: List[TrackMeta]) -> List[TrackMeta]:
    seen = set()
    out: List[TrackMeta] = []
    for r in rows:
        if r.track_id and r.track_id not in seen:
            out.append(r)
            seen.add(r.track_id)
    return out

# ---------- Collectors ----------
def collect_from_playlists(
    sp: spotipy.Spotify,
    playlist_ids: Iterable[str],
    seed_label: str = "rnb:playlist",
) -> pd.DataFrame:
    """
    Pull tracks from one or more playlists. Good for curated seeds.
    """
    rows: List[TrackMeta] = []
    for pid in playlist_ids:
        logger.info(f"Pulling playlist {pid}")
        results = sp.playlist_items(pid, additional_types=("track",))
        while results:
            for item in results["items"]:
                t = item.get("track") or {}
                if not t or t.get("id") is None:
                    continue
                rows.append(
                    TrackMeta(
                        track_id=t["id"],
                        name=t.get("name",""),
                        artist=", ".join([a["name"] for a in t.get("artists",[])]),
                        artist_id=(t.get("artists") or [{}])[0].get("id"),
                        album=(t.get("album") or {}).get("name"),
                        album_id=(t.get("album") or {}).get("id"),
                        isrc=(t.get("external_ids") or {}).get("isrc"),
                        seed_tag=seed_label
                    )
                )
            results = _safe_next(sp, results)
    rows = _dedupe_tracks(rows)
    df = pd.DataFrame([r.__dict__ for r in rows])
    return df

def collect_from_search(
    sp: spotipy.Spotify,
    queries: Iterable[str],
    limit_per_query: int = 150,
    market: str = DEFAULT_MARKET,
    seed_prefix: str = "all:search",
) -> pd.DataFrame:
    """
    Broad recall: use freeform queries like 'r-n-b', 'neo-soul', 'quiet-storm'.
    """
    rows: List[TrackMeta] = []
    for q in queries:
        label = f"{seed_prefix}:{q}"
        logger.info(f"Searching '{q}' (limit ~{limit_per_query})")
        got = 0
        results = sp.search(q=q, type="track", limit=50, market=market)
        while results and got < limit_per_query:
            for t in results["tracks"]["items"]:
                rows.append(
                    TrackMeta(
                        track_id=t["id"],
                        name=t.get("name",""),
                        artist=", ".join([a["name"] for a in t.get("artists",[])]),
                        artist_id=(t.get("artists") or [{}])[0].get("id"),
                        album=(t.get("album") or {}).get("name"),
                        album_id=(t.get("album") or {}).get("id"),
                        isrc=(t.get("external_ids") or {}).get("isrc"),
                        seed_tag=label
                    )
                )
                got += 1
                if got >= limit_per_query:
                    break
            if got >= limit_per_query:
                break
            results = _safe_next(sp, results)
    rows = _dedupe_tracks(rows)
    return pd.DataFrame([r.__dict__ for r in rows])

def collect_from_artists_top(
    sp: spotipy.Spotify,
    artist_ids: Iterable[str],
    market: str = DEFAULT_MARKET,
    seed_prefix: str = "all:artist-top",
) -> pd.DataFrame:
    """
    Pull each artist's top tracks in a market—useful beyond R&B later.
    """
    rows: List[TrackMeta] = []
    for aid in artist_ids:
        label = f"{seed_prefix}:{aid}"
        logger.info(f"Top tracks for artist {aid}")
        res = sp.artist_top_tracks(aid, country=market) or {}
        for t in res.get("tracks", []):
            rows.append(
                TrackMeta(
                    track_id=t["id"],
                    name=t.get("name",""),
                    artist=", ".join([a["name"] for a in t.get("artists",[])]),
                    artist_id=(t.get("artists") or [{}])[0].get("id"),
                    album=(t.get("album") or {}).get("name"),
                    album_id=(t.get("album") or {}).get("id"),
                    isrc=(t.get("external_ids") or {}).get("isrc"),
                    seed_tag=label
                )
            )
    rows = _dedupe_tracks(rows)
    return pd.DataFrame([r.__dict__ for r in rows])

# ---------- Audio features ----------
def fetch_audio_features(sp: spotipy.Spotify, track_ids: List[str], batch: int = 100) -> pd.DataFrame:
    """
    Get numeric audio features in batches; returns a DataFrame keyed by 'id'.
    """
    feats = []
    n = len(track_ids)
    if n == 0:
        return pd.DataFrame()
    logger.info(f"Fetching audio features for {n} tracks in {math.ceil(n/batch)} batches...")
    for i in range(0, n, batch):
        chunk = track_ids[i:i+batch]
        af = sp.audio_features(chunk)
        if not af:
            continue
        feats.extend([row for row in af if row])  # guard None rows
        sleep(0.2)
    df = pd.DataFrame(feats)
    return df

# ---------- Orchestration ----------
def build_dataset(
    playlists: Optional[List[str]] = None,
    queries: Optional[List[str]] = None,
    artists: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Compose seeds from any combination of playlists, queries, and artists,
    then join with audio features.
    """
    sp = spotify_client()

    frames: List[pd.DataFrame] = []
    if playlists:
        frames.append(collect_from_playlists(sp, playlists, seed_label="rnb:playlist"))
    if queries:
        frames.append(collect_from_search(sp, queries, limit_per_query=150, seed_prefix="all:search"))
    if artists:
        frames.append(collect_from_artists_top(sp, artists, seed_prefix="all:artist-top"))

    if not frames:
        logger.warning("No seeds provided; returning empty DataFrame.")
        return pd.DataFrame()

    meta = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["track_id"])
    logger.info(f"Got {len(meta)} unique seed tracks.")
    af = fetch_audio_features(sp, meta["track_id"].tolist())

    # Join on track ID
    df = meta.merge(af, left_on="track_id", right_on="id", how="inner")
    # Light cleaning: keep key columns and features
    keep = [
        "track_id","name","artist","artist_id","album","album_id","isrc","seed_tag",
        "danceability","energy","loudness","speechiness","acousticness",
        "instrumentalness","liveness","valence","tempo","duration_ms","key","mode","time_signature","id"
    ]
    df = df[[c for c in keep if c in df.columns]].copy()
    return df
