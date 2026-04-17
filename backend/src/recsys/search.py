from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

EM_DASH = chr(0x2014)
SEPARATOR_RE = re.compile(rf"\s*[-{EM_DASH}]\s*")
PUNCT_RE = re.compile(r"[^\w\s]+")


def norm(text: str) -> str:
    """
    Normalize free text for lexical search:
    - lowercase
    - strip punctuation
    - collapse whitespace
    - remove accents
    """
    if text is None:
        return ""

    normalized = unicodedata.normalize("NFKD", str(text))
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = PUNCT_RE.sub(" ", normalized)
    normalized = " ".join(normalized.split())
    return normalized


@dataclass
class MatchResult:
    row_index: int
    score: float


class SearchIndex:
    """
    Lightweight lexical/fuzzy search over a track catalog.
    Stores normalized keys for fuzzy match, plus an exact lookup for fast resolution.
    """

    def __init__(self, df: pd.DataFrame):
        if not {"title", "artist"}.issubset(df.columns):
            raise ValueError("DataFrame must include 'title' and 'artist' columns")

        self.df = df.reset_index(drop=True).copy()
        self.df["title_norm"] = self.df["title"].map(norm)
        self.df["artist_norm"] = self.df["artist"].map(norm)
        self.df["key_norm"] = (
            self.df["title_norm"].str.strip() + " " + self.df["artist_norm"].str.strip()
        ).str.strip()

        self.keys: List[str] = self.df["key_norm"].tolist()
        self.exact_index: dict[str, int] = {}
        for idx, key in enumerate(self.keys):
            # Keep first occurrence in case of duplicates
            self.exact_index.setdefault(key, idx)

    def _split_title_artist(self, query: str) -> Tuple[str, str] | None:
        parts = SEPARATOR_RE.split(query, maxsplit=1)
        if len(parts) == 2:
            title, artist = parts[0].strip(), parts[1].strip()
            if title and artist:
                return title, artist
        return None

    def _lookup_exact(self, key: str) -> MatchResult | None:
        idx = self.exact_index.get(key)
        if idx is None:
            return None
        return MatchResult(row_index=idx, score=100.0)

    def top_matches(self, query: str, limit: int = 9) -> List[dict]:
        """
        Return top matches with metadata and fuzzy score.
        Score is 0-100 from rapidfuzz, higher is better.
        """
        q_norm = norm(query)
        if not q_norm:
            return []

        parsed = self._split_title_artist(query)
        seed_query = norm(f"{parsed[0]} {parsed[1]}") if parsed else q_norm

        results = process.extract(
            seed_query,
            self.keys,
            scorer=fuzz.WRatio,
            limit=limit,
        )

        output: List[dict] = []
        for _, score, idx in results:
            row = self.df.iloc[idx]
            output.append(
                {
                    "row_index": int(idx),
                    "title": row["title"],
                    "artist": row["artist"],
                    "preview_url": row.get("preview_url"),
                    "artwork_url": row.get("artwork_url"),
                    "score": float(score),
                }
            )
        return output

    def match(self, query: str, limit: int = 8) -> tuple[int | None, float, list[int]]:
        """
        Resolve a user query to the best matching row index.
        Returns (best_idx, best_score, candidate_idxs).
        """
        query = query or ""
        parsed = self._split_title_artist(query)

        # Try exact resolution using parsed title+artist or full query
        if parsed:
            exact_key = norm(f"{parsed[0]} {parsed[1]}")
            exact = self._lookup_exact(exact_key)
            if exact:
                return exact.row_index, exact.score, [exact.row_index]

        query_norm = norm(query)
        exact = self._lookup_exact(query_norm)
        if exact:
            return exact.row_index, exact.score, [exact.row_index]

        # Fallback to fuzzy search
        seed_query = norm(f"{parsed[0]} {parsed[1]}") if parsed else query_norm
        matches = self.top_matches(seed_query, limit=limit)
        if not matches:
            return None, 0.0, []

        candidate_idxs = [m["row_index"] for m in matches]
        best = matches[0]
        return best["row_index"], float(best["score"]), candidate_idxs


def debug_cli(search_index: SearchIndex, queries: Iterable[str], limit: int = 5) -> None:
    """
    Quick sanity print helper for manual runs.
    """
    for q in queries:
        idx, score, _ = search_index.match(q, limit=limit)
        top = search_index.top_matches(q, limit=limit)
        best = top[0] if top else None
        print(f"Query: {q}")
        if best:
            print(f"  Best: {best['title']} - {best['artist']} (score={score:.1f})")
        else:
            print("  No matches")
        for cand in top:
            print(f"    {cand['score']:.1f} -> {cand['title']} - {cand['artist']}")
        print("-" * 40)
