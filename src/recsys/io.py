# src/recsys/io.py
from __future__ import annotations
import re
import json
from pathlib import Path
from difflib import get_close_matches, SequenceMatcher
from .config import ART  # same ART as everywhere else

NORMALIZE_RE = re.compile(r"[^a-z0-9 ]+")

def _norm(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("feat.", "").replace("ft.", "")
    s = s.replace(" by ", " ")
    s = NORMALIZE_RE.sub(" ", s)
    s = " ".join(s.split())
    return s

def load_id_map():
    """Load the list of track metadata dicts saved during preprocessing."""
    path = ART / "id_map.json"
    with path.open() as f:
        return json.load(f)
    
def build_search_index(id_map):
    """
    Returns a list of dicts:
      { 'index': i, 'title': ..., 'artist': ..., 'norm_title': ..., 'norm_artist': ..., 'norm_both': ... }
    """
    index = []
    for i, row in enumerate(id_map):
        title = row["title"]
        artist = row["artist"]
        norm_title = _norm(title)
        norm_artist = _norm(artist)
        norm_both = _norm(f"{title} {artist}")
        index.append({
            "index": i,
            "title": title,
            "artist": artist,
            "norm_title": norm_title,
            "norm_artist": norm_artist,
            "norm_both": norm_both,
        })
    return index

def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def search_tracks(query: str, search_index, limit: int = 5) -> list[dict]:
    """
    Return up to `limit` best matches, each:
      { 'row_index', 'title', 'artist', 'score' }
    """
    q = _norm(query)
    scores = []

    for entry in search_index:
        score_both = _similarity(q, entry["norm_both"])
        score_title = _similarity(q, entry["norm_title"])
        score = max(score_both, score_title)  # you could weight these differently

        scores.append((score, entry))

    scores.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, entry in scores[:limit]:
        out.append({
            "row_index": entry["index"],
            "title": entry["title"],
            "artist": entry["artist"],
            "score": float(score),
        })
    return out

def fuzzy_row_index(query: str, id_map=None, cutoff: float = 0.55):
    """
    Backwards-compatible helper: return best single match above cutoff,
    or (None, None) if nothing feels close enough.
    """
    if id_map is None:
        id_map = load_id_map()

    search_index = build_search_index(id_map)
    matches = search_tracks(query, search_index, limit=3)
    if not matches:
        return None, None

    best = matches[0]
    if best["score"] < cutoff:
        return None, None

    idx = best["row_index"]
    return idx, id_map[idx]