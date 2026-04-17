from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from rapidfuzz import fuzz

from src.recsys.config import PROC, SEEDS

LASTFM = "https://ws.audioscrobbler.com/2.0/"
ITUNES = "https://itunes.apple.com/search"
DEEZER = "https://api.deezer.com/search"


# -----------------------------
# Data model
# -----------------------------
@dataclass
class TrackRow:
    title: str
    artist: str
    mbid: Optional[str]
    match_score: Optional[float]
    tags: list[str]
    preview_url: Optional[str]
    artwork_url: Optional[str]
    source: str
    seed_group: Optional[str] = None
    primary_genre: Optional[str] = None
    genre_confidence: Optional[float] = None


# -----------------------------
# Cache helpers
# -----------------------------
CACHE_DIR = PROC / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LASTFM_CACHE = CACHE_DIR / "lastfm"
ITUNES_CACHE = CACHE_DIR / "itunes"
LASTFM_CACHE.mkdir(parents=True, exist_ok=True)
ITUNES_CACHE.mkdir(parents=True, exist_ok=True)


def _safe_key(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.lower())[:180]


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _write_json(path: Path, data: dict) -> None:
    try:
        path.write_text(json.dumps(data))
    except Exception:
        pass


def _ascii_clean(text: str) -> str:
    text = (
        unicodedata.normalize("NFKD", text or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    text = text.replace("’", "'")
    text = re.sub(r"[^\w\s&:'-]+", " ", text)
    return " ".join(text.split())


def _strip_feat_remix(text: str) -> str:
    text = re.sub(
        r"\s*\([^)]*(feat\.?|ft\.?|with)[^)]*\)", "", text, flags=re.IGNORECASE
    )
    text = re.sub(
        r"\s*\[[^\]]*(feat\.?|ft\.?|with)[^\]]*\]", "", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\s*\b(feat\.?|ft\.?|with)\b.*", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\s*\([^)]*(remix|edit|version|live|acoustic|remaster)[^)]*\)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\s*\[[^\]]*(remix|edit|version|live|acoustic|remaster)[^\]]*\]",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\s*[-:]\s*(remix|edit|version|live|acoustic|remaster).*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return " ".join(text.split())


def _simplify_title(text: str) -> str:
    text = _ascii_clean(text)
    text = _strip_feat_remix(text)
    return text


# -----------------------------
# Last.fm low-level
# -----------------------------
def _lastfm(params: dict) -> dict:
    load_dotenv()
    k = os.getenv("LASTFM_API_KEY")
    if not k:
        raise RuntimeError("Missing LASTFM_API_KEY in .env")

    q = {"api_key": k, "format": "json", **params}
    headers = {"User-Agent": "dscvr/0.2 (contact: pynej001@umn.edu)"}

    r = requests.get(LASTFM, params=q, headers=headers, timeout=20)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"Last.fm HTTP {r.status_code}: {r.text[:300]}") from e

    ctype = r.headers.get("Content-Type", "")
    if "json" not in ctype.lower():
        snippet = (r.text or "")[:300]
        raise RuntimeError(
            f"Last.fm returned non-JSON (Content-Type={ctype}). First 300 chars:\n{snippet}"
        )

    if not r.text.strip():
        raise RuntimeError(
            f"Last.fm returned empty body for params={params}. Status={r.status_code}"
        )

    data = r.json()
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(f"Last.fm error {data['error']}: {data.get('message')}")
    return data


def _cached_lastfm(prefix: str, key: str, params: dict) -> dict:
    path = LASTFM_CACHE / f"{prefix}_{_safe_key(key)}.json"
    hit = _read_json(path)
    if hit is not None:
        return hit
    data = _lastfm(params)
    _write_json(path, data)
    return data


# -----------------------------
# iTunes preview cache
# -----------------------------
def _deezer_artwork(
    clean_title: str, clean_artist: str, query_key: str
) -> Optional[str]:
    """
    Deezer fallback used only for artwork: search and pick best fuzzy match, return artwork_url.
    """
    queries = []
    if clean_title and clean_artist:
        queries.append(f'artist:"{clean_artist}" track:"{clean_title}"')
        queries.append(f"{clean_title} {clean_artist}")
    if clean_title:
        queries.append(clean_title)
    if clean_artist:
        queries.append(clean_artist)

    all_items: list[dict] = []
    seen_ids: set = set()

    def _search(term: str, limit: int) -> list[dict]:
        r = requests.get(
            DEEZER,
            params={"q": term, "limit": limit},
            timeout=15,
        )
        if r.status_code != 200:
            return []
        try:
            return r.json().get("data", []) or []
        except Exception:
            return []

    for i, q in enumerate(queries):
        limit = 10 if i == 0 else 5
        for it in _search(q, limit=limit):
            tid = it.get("id") or id(it)
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            all_items.append(it)

    if not all_items:
        return None

    best = None
    best_score = -1
    for it in all_items:
        track = _ascii_clean(it.get("title") or "")
        artname = _ascii_clean((it.get("artist") or {}).get("name") or "")
        cand_key = f"{track} {artname}".strip()
        score = fuzz.WRatio(query_key, cand_key) if query_key else 0
        if score > best_score:
            best_score = score
            best = it

    if best is None:
        best = all_items[0]

    album = best.get("album") or {}
    artwork = album.get("cover_big") or album.get("cover_medium") or album.get("cover")
    return artwork


def _itunes_preview(title: str, artist: str) -> tuple[Optional[str], Optional[str]]:
    """
    Hit iTunes search with sanitized queries, broaden candidates, and pick the best fuzzy match.
    Falls back to Deezer when iTunes artwork is missing (preview stays iTunes-only).
    """

    clean_title = _simplify_title(title or "")
    clean_artist = _simplify_title(artist or "")
    query_key = (
        (clean_title + " " + clean_artist).strip() or clean_title or clean_artist
    )

    queries = []
    if clean_title and clean_artist:
        queries.append(clean_title + " " + clean_artist)
    if clean_title:
        queries.append(clean_title)
    if clean_artist:
        queries.append(clean_artist)
    if not queries:
        return None, None

    all_items: list[dict] = []
    seen_ids: set = set()

    def _search(term: str, limit: int) -> list[dict]:
        r = requests.get(
            ITUNES,
            params={
                "term": term,
                "media": "music",
                "entity": "musicTrack",
                "limit": limit,
                "country": "US",
            },
            timeout=15,
        )
        if r.status_code != 200:
            return []
        try:
            return r.json().get("results", []) or []
        except Exception:
            return []

    for i, q in enumerate(queries):
        limit = 10 if i == 0 else 5
        for it in _search(q, limit=limit):
            kind = (it.get("kind") or it.get("wrapperType") or "").lower()
            if kind and "song" not in kind and "track" not in kind:
                continue
            tid = it.get("trackId") or it.get("trackViewUrl") or id(it)
            if tid in seen_ids:
                continue
            seen_ids.add(tid)
            all_items.append(it)

    def _score_candidate(item: dict) -> tuple[float, float, float, bool]:
        cand_title = _simplify_title(item.get("trackName") or "")
        cand_artist = _simplify_title(item.get("artistName") or "")
        title_score = (
            fuzz.WRatio(clean_title, cand_title) if clean_title and cand_title else 0
        )
        artist_score = (
            fuzz.WRatio(clean_artist, cand_artist)
            if clean_artist and cand_artist
            else 0
        )
        combined = 0.6 * title_score + 0.4 * artist_score
        has_urls = bool(item.get("previewUrl") or item.get("artworkUrl100"))
        return combined, title_score, artist_score, has_urls

    best_prev = None
    best_art = None
    if all_items:
        scored = [(_score_candidate(it), it) for it in all_items]
        scored.sort(key=lambda x: (x[0][3], x[0][0]), reverse=True)

        best = None
        for (combined, t_score, a_score, has_urls), it in scored:
            if has_urls and t_score >= 80 and a_score >= 70:
                best = it
                break

        if best is None:
            best = scored[0][1]
        best_prev = best.get("previewUrl")
        best_art = best.get("artworkUrl100")

    # Deezer fallback for artwork only (preview remains iTunes-only)
    if not best_art:
        best_art = _deezer_artwork(clean_title, clean_artist, query_key)

    return best_prev, best_art


def _cached_itunes_preview(
    title: str,
    artist: str,
    refresh_if_empty: bool = False,
) -> tuple[Optional[str], Optional[str]]:
    key = f"{artist}:{title}"
    path = ITUNES_CACHE / f"itunes_{_safe_key(key)}.json"
    hit = _read_json(path)
    if hit is not None:
        prev = hit.get("preview_url")
        art = hit.get("artwork_url")
        if not refresh_if_empty or (prev or art):
            return prev, art

    prev, art = _itunes_preview(title, artist)
    _write_json(path, {"preview_url": prev, "artwork_url": art})
    return prev, art


# -----------------------------
# Last.fm domain helpers
# -----------------------------
def load_seed_groups(seed_dir: Path | None = None) -> dict[str, list[tuple[str, str]]]:
    seed_dir = seed_dir or SEEDS
    groups: dict[str, list[tuple[str, str]]] = {}

    if not seed_dir.exists():
        return groups

    for path in sorted(seed_dir.glob("*.json")):
        group_name = path.stem
        try:
            raw = json.loads(path.read_text())
        except Exception as e:
            print(f"[load_seed_groups] ERROR reading {path}: {e}")
            continue

        seeds: list[tuple[str, str]] = []
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
            print(f"[load_seed_groups] {group_name}: loaded {len(seeds)} seeds")
    return groups


def chart_get_top_tracks(page: int = 1, limit: int = 50) -> list[dict]:
    res = _cached_lastfm(
        "chart_top_tracks",
        f"p{page}_l{limit}",
        {"method": "chart.getTopTracks", "page": page, "limit": limit},
    )
    tracks = ((res.get("tracks") or {}).get("track")) or []
    if isinstance(tracks, dict):
        tracks = [tracks]

    out: list[dict] = []
    for t in tracks:
        title = t.get("name") or ""
        artist = (t.get("artist") or {}).get("name") or ""
        if title and artist:
            out.append({"title": title, "artist": artist, "source": f"chart:p{page}"})
    return out


def geo_get_top_tracks(country: str, page: int = 1, limit: int = 50) -> list[dict]:
    res = _cached_lastfm(
        "geo_top_tracks",
        f"{country}_p{page}_l{limit}",
        {
            "method": "geo.getTopTracks",
            "country": country,
            "page": page,
            "limit": limit,
        },
    )
    tracks = ((res.get("tracks") or {}).get("track")) or []
    if isinstance(tracks, dict):
        tracks = [tracks]

    out: list[dict] = []
    for t in tracks:
        title = t.get("name") or ""
        artist = (t.get("artist") or {}).get("name") or ""
        if title and artist:
            out.append(
                {"title": title, "artist": artist, "source": f"geo:{country}:p{page}"}
            )
    return out


def track_get_similar(title: str, artist: str, limit: int = 20) -> list[dict]:
    """
    Best-effort similar lookup.
    Returns [] if Last.fm can't resolve the track (error 6) or other transient issues.
    """
    try:
        res = _cached_lastfm(
            "track_similar",
            f"{artist}:{title}:l{limit}",
            {
                "method": "track.getSimilar",
                "track": title,
                "artist": artist,
                "limit": limit,
                "autocorrect": 1,  # IMPORTANT
            },
        )
    except RuntimeError as e:
        msg = str(e).lower()
        # Last.fm error 6: Track not found
        if "error 6" in msg or "track not found" in msg:
            return []
        # Any other Last.fm error: treat as empty for ETL robustness
        print(f"[track_get_similar] WARNING: {artist} — {title}: {e}")
        return []
    except Exception as e:
        print(f"[track_get_similar] WARNING: {artist} — {title}: {e}")
        return []

    tracks = (res.get("similartracks") or {}).get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]

    out: list[dict] = []
    for t in tracks:
        if not isinstance(t, dict):
            continue
        name = t.get("name") or ""
        aobj = t.get("artist") or {}
        aname = aobj.get("name") if isinstance(aobj, dict) else str(aobj or "")
        if name and aname:
            out.append({"title": name, "artist": aname})
    return out


def track_get_tags_cached(
    title: str, artist: str, kind: str = "track", limit: int = 30
) -> list[str]:
    if kind == "track":
        method = "track.getTopTags"
        params = {"track": title, "artist": artist}
        key = f"track:{artist}:{title}"
    else:
        method = "artist.getTopTags"
        params = {"artist": artist}
        key = f"artist:{artist}"

    try:
        res = _cached_lastfm(f"{kind}_tags", key, {"method": method, **params})
        taglist = (res.get("toptags") or {}).get("tag", [])
        if isinstance(taglist, dict):
            taglist = [taglist]
        tags = [t.get("name", "") for t in taglist[:limit] if isinstance(t, dict)]
        return [t for t in tags if t]
    except Exception:
        return []


# -----------------------------
# Genre labeling (multi-genre)
# -----------------------------
GENRE_MAP: dict[str, set[str]] = {
    "rnb": {
        "rnb",
        "r&b",
        "neo-soul",
        "neo soul",
        "alternative rnb",
        "alt rnb",
        "quiet storm",
        "soul",
    },
    "hiphop": {"hip hop", "hip-hop", "rap", "trap"},
    "pop": {"pop", "dance pop", "electropop"},
    "indie": {"indie", "alternative", "indie rock"},
    "rock": {"rock", "alternative rock", "alt rock", "hard rock"},
    "electronic": {"electronic", "edm", "house", "techno", "dance"},
    "country": {"country"},
    "jazz": {"jazz"},
    "classical": {"classical"},
    "metal": {"metal"},
}


def _norm_tag(t: str) -> str:
    return (t or "").strip().lower()


def label_primary_genre(tags: list[str]) -> tuple[str, float]:
    tagset = {_norm_tag(t) for t in (tags or []) if t}
    best_genre = "other"
    best_score = 0
    for genre, keys in GENRE_MAP.items():
        score = len(tagset.intersection(keys))
        if score > best_score:
            best_genre = genre
            best_score = score
    conf = 0.0 if best_score == 0 else min(1.0, best_score / 3.0)
    return best_genre, conf


# -----------------------------
# ETL phases
# -----------------------------
def collect_candidates(
    chart_pages: int = 50,
    chart_limit: int = 50,
    countries: list[str] | None = None,
    geo_pages: int = 5,
    seed_dir: Path | None = None,
    sleep_s: float = 0.05,
) -> pd.DataFrame:
    rows: list[dict] = []

    # charts
    for p in range(1, chart_pages + 1):
        rows.extend(chart_get_top_tracks(page=p, limit=chart_limit))
        time.sleep(sleep_s)

    # geo
    countries = countries or ["United States", "United Kingdom", "Canada", "Australia"]
    for c in countries:
        for p in range(1, geo_pages + 1):
            rows.extend(geo_get_top_tracks(country=c, page=p, limit=chart_limit))
            time.sleep(sleep_s)

    # seeds (optional)
    if seed_dir is not None:
        groups = load_seed_groups(seed_dir)
        for g, seeds in groups.items():
            for title, artist in seeds:
                rows.append(
                    {
                        "title": title,
                        "artist": artist,
                        "source": f"seed:{g}",
                        "seed_group": g,
                    }
                )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # ensure columns exist
    if "seed_group" not in df.columns:
        df["seed_group"] = None

    df = df.drop_duplicates(subset=["title", "artist"]).reset_index(drop=True)
    print(f"[collect_candidates] candidates: {len(df)}")
    return df


def expand_via_similar(
    df: pd.DataFrame,
    per_track: int = 5,
    max_new: int = 5000,
    sleep_s: float = 0.05,
) -> pd.DataFrame:
    """
    Optional expansion: add similar tracks for breadth.
    Uses caching, so reruns are cheap.
    """
    seen = {(r["title"], r["artist"]) for _, r in df.iterrows()}
    new_rows: list[dict] = []

    for _, r in df.iterrows():
        if len(new_rows) >= max_new:
            break
        title, artist = r["title"], r["artist"]
        source = r.get("source", "unknown")
        sims = track_get_similar(title, artist, limit=per_track)
        for s in sims:
            key = (s["title"], s["artist"])
            if key in seen:
                continue
            seen.add(key)
            new_rows.append(
                {
                    "title": s["title"],
                    "artist": s["artist"],
                    "source": f"similar:{source}",
                    "seed_group": None,
                }
            )
            if len(new_rows) >= max_new:
                break
        time.sleep(sleep_s)

    if not new_rows:
        return df

    df2 = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df2 = df2.drop_duplicates(subset=["title", "artist"]).reset_index(drop=True)
    print(f"[expand_via_similar] added {len(new_rows)} tracks, total now {len(df2)}")
    return df2


def enrich_candidates(
    df: pd.DataFrame,
    sleep_s: float = 0.05,
    itunes: bool = True,
) -> pd.DataFrame:
    rows: list[TrackRow] = []
    for _, r in df.iterrows():
        title = str(r["title"])
        artist = str(r["artist"])
        source = str(r.get("source", "unknown"))
        seed_group = r.get("seed_group")
        if pd.isna(seed_group):
            seed_group = None

        tags = list(
            dict.fromkeys(
                track_get_tags_cached(title, artist, "track")
                + track_get_tags_cached(title, artist, "artist")
            )
        )

        prev, art = (None, None)
        if itunes:
            prev, art = _cached_itunes_preview(title, artist)

        genre, conf = label_primary_genre(tags)

        rows.append(
            TrackRow(
                title=title,
                artist=artist,
                mbid=None,
                match_score=None,
                tags=tags,
                preview_url=prev,
                artwork_url=art,
                source=source,
                seed_group=seed_group,
                primary_genre=genre,
                genre_confidence=conf,
            )
        )
        time.sleep(sleep_s)

    out = pd.DataFrame([x.__dict__ for x in rows])
    out = out.drop_duplicates(subset=["title", "artist"]).reset_index(drop=True)
    return out


def build_lastfm_dataset(
    out_path: str | Path = PROC / "tracks_lastfm2.parquet",
    chart_pages: int = 50,
    geo_pages: int = 5,
    countries: list[str] | None = None,
    seed_dir: Path | None = SEEDS,
    expand_similar: bool = True,
    similar_per_track: int = 3,
    similar_max_new: int = 3000,
    sleep_s: float = 0.05,
    itunes: bool = True,
) -> str:
    """
    Scalable catalog builder:
      1) Collect candidates from chart + geo (+ optional seeds)
      2) Optional: expand via track.getSimilar
      3) Enrich with cached tags + cached iTunes preview/artwork
      4) Label primary_genre via tags
      5) Write parquet
    """
    candidates = collect_candidates(
        chart_pages=chart_pages,
        geo_pages=geo_pages,
        countries=countries,
        seed_dir=seed_dir,
        sleep_s=sleep_s,
    )
    if candidates.empty:
        raise RuntimeError("No candidates collected. Check API key or endpoints.")

    if expand_similar:
        candidates = expand_via_similar(
            candidates,
            per_track=similar_per_track,
            max_new=similar_max_new,
            sleep_s=sleep_s,
        )

    df = enrich_candidates(candidates, sleep_s=sleep_s, itunes=itunes)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)

    print(f"✅ Wrote {len(df)} rows → {out_path}")
    print(
        "[genre breakdown]\n" + df["primary_genre"].value_counts().head(12).to_string()
    )
    return str(out_path)
