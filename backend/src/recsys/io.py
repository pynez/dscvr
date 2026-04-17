# src/recsys/io.py
from __future__ import annotations

import json
import re
import unicodedata
from difflib import SequenceMatcher

from .config import ART  # same ART as everywhere else

NORMALIZE_RE = re.compile(r"[^a-z0-9 ]+")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    s = s.lower()
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


def _token_set_similarity(a: str, b: str) -> float:
    """
    Order-insensitive similarity inspired by fuzzywuzzy's token_set_ratio.
    """
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0

    common = a_tokens & b_tokens
    only_a = a_tokens - b_tokens
    only_b = b_tokens - a_tokens

    common_str = " ".join(sorted(common))
    a_str = " ".join(sorted(common | only_a))
    b_str = " ".join(sorted(common | only_b))

    return max(
        _similarity(common_str, a_str),
        _similarity(common_str, b_str),
        _similarity(a_str, b_str),
    )


def _partial_similarity(a: str, b: str) -> float:
    """
    Partial ratio: best match for the shorter string anywhere inside the longer one.
    """
    if not a or not b:
        return 0.0

    short, long = (a, b) if len(a) <= len(b) else (b, a)
    matcher = SequenceMatcher(None, short, long)
    best = 0.0
    for block in matcher.get_matching_blocks():
        start = max(0, block[1] - block[0])
        window = long[start : start + len(short)]
        best = max(best, _similarity(short, window))
    return best


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
        score_artist = _similarity(q, entry["norm_artist"])
        score_token_title = _token_set_similarity(q, entry["norm_title"])
        score_token_both = _token_set_similarity(q, entry["norm_both"])
        score_partial_title = _partial_similarity(q, entry["norm_title"])
        score_partial_both = _partial_similarity(q, entry["norm_both"])
        score_partial_artist = _partial_similarity(q, entry["norm_artist"])

        # Weighted blend favors full title+artist match, with boosts for orderless/partial and artist matches.
        score = (
            0.35 * score_both
            + 0.2 * max(score_title, score_token_title, score_partial_title)
            + 0.2 * max(score_artist, score_partial_artist)
            + 0.15 * score_token_both
            + 0.1 * score_partial_both
        )

        if (
            entry["norm_title"].startswith(q)
            or entry["norm_both"].startswith(q)
            or entry["norm_artist"].startswith(q)
        ):
            score += 0.05  # small bonus for prefix matches

        score = min(score, 1.0)

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


def fuzzy_row_index(query: str, id_map=None, cutoff: float = 0.45):
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
