# src/recsys/recommenders/cosine.py
from __future__ import annotations
from typing import List, Dict, Optional
import json
import logging
from pathlib import Path

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..config import ART, PROC        # uses data/artifacts from your existing config
from .base import Recommender

log = logging.getLogger(__name__)


class CosineRecommender(Recommender):
    """Cosine similarity over the text-based feature matrix."""

    def __init__(self) -> None:
        features_path = ART / "features.npy"
        id_map_path = ART / "id_map.json"
        parquet_path = PROC / "tracks_lastfm.parquet"

        if not features_path.exists() or not id_map_path.exists():
            raise RuntimeError(
                "Missing artifacts. Did you run `python -m src.cli.train_text`?"
            )

        self.X = np.load(features_path)
        with id_map_path.open() as f:
            self.id_map = json.load(f)

        # Optional: richer metadata from processed parquet (artwork/preview)
        self.meta_df = None
        try:
            if parquet_path.exists():
                import pandas as pd

                df = pd.read_parquet(parquet_path)
                if len(df) == len(self.id_map):
                    self.meta_df = df.reset_index(drop=True)
        except Exception:
            self.meta_df = None

        # Lazy-loaded TF-IDF+SVD pipeline (for text-based queries)
        self._pipeline = None

    def similar_by_index(
        self,
        row_index: int,
        top_k: int = 10,
        max_per_artist: int = 2,
    ) -> List[Dict]:
        """
        Return up to top_k most similar tracks, with simple artist diversity:
        no more than max_per_artist tracks per artist.
        """
        n = self.X.shape[0]
        if row_index < 0 or row_index >= n:
            raise IndexError(f"row_index {row_index} out of range [0, {n})")

        v = self.X[row_index : row_index + 1]
        sims = cosine_similarity(v, self.X)[0]

        # Exclude self
        sims[row_index] = -1.0

        # Sort all indices by similarity (descending)
        order = np.argsort(-sims)

        recs: List[Dict] = []
        artist_counts: dict[str, int] = {}

        for j in order:
            if sims[j] <= 0:
                # stop early if we hit non-positive similarity; optional
                break

            row = self.id_map[j]
            artist = row["artist"]
            meta = self.meta_df.iloc[j] if self.meta_df is not None else None
            cnt = artist_counts.get(artist, 0)
            if cnt >= max_per_artist:
                continue

            preview = row.get("preview_url")
            artwork = row.get("artwork_url")
            if meta is not None:
                preview = meta.get("preview_url") or preview
                artwork = meta.get("artwork_url") or artwork

            recs.append(
                {
                    "row_index": int(j),
                    "name": meta.get("title") if meta is not None else row["title"],
                    "artist": artist,
                    "score": float(sims[j]),
                    "preview_url": preview,
                    "artwork_url": artwork,
                }
            )
            artist_counts[artist] = cnt + 1

            if len(recs) >= top_k:
                break

        return recs

    # ── helpers shared by feature modules ─────────────────────────────────────

    def _row_to_dict(self, j: int, sim_score: float, include_tags: bool = False) -> dict:
        """Serialize catalog row j to a result dict."""
        row = self.id_map[j]
        artist = row["artist"]
        meta = self.meta_df.iloc[j] if self.meta_df is not None else None

        preview = row.get("preview_url")
        artwork = row.get("artwork_url")
        title = row["title"]
        if meta is not None:
            preview = meta.get("preview_url") or preview
            artwork = meta.get("artwork_url") or artwork
            title = meta.get("title") or title

        out = {
            "row_index": int(j),
            "name": title,
            "artist": artist,
            "score": float(sim_score),
            "preview_url": preview,
            "artwork_url": artwork,
        }
        if include_tags and meta is not None:
            raw_tags = meta.get("tags") if hasattr(meta, "get") else None
            if raw_tags is None:
                raw_tags = []
            if hasattr(raw_tags, "tolist"):
                raw_tags = raw_tags.tolist()
            out["tags"] = [str(t) for t in raw_tags if t] if raw_tags else []
        return out

    def _load_pipeline(self):
        if self._pipeline is None:
            import joblib
            pipe_path = ART / "text_svd.pkl"
            if not pipe_path.exists():
                raise RuntimeError("text_svd.pkl not found — run train_text first.")
            self._pipeline = joblib.load(pipe_path)
        return self._pipeline

    def similar_by_text(
        self,
        text: str,
        top_k: int = 40,
        max_per_artist: int = 3,
        include_tags: bool = False,
    ) -> List[Dict]:
        """
        Vectorize arbitrary text through the TF-IDF+SVD pipeline and return
        the top_k most similar catalog tracks.
        """
        pipe = self._load_pipeline()
        v = pipe.transform([text.lower()])
        sims = cosine_similarity(v, self.X)[0]
        order = np.argsort(-sims)

        recs: List[Dict] = []
        artist_counts: dict[str, int] = {}

        for j in order:
            if sims[j] <= 0:
                break
            artist = self.id_map[j]["artist"]
            if artist_counts.get(artist, 0) >= max_per_artist:
                continue
            recs.append(self._row_to_dict(j, sims[j], include_tags=include_tags))
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            if len(recs) >= top_k:
                break

        return recs

    def similar_by_index_era(
        self,
        row_index: int,
        era_tags: list[str],
        top_k: int = 15,
        max_per_artist: int = 2,
    ) -> List[Dict]:
        """
        Like similar_by_index but restricts candidates to tracks whose tags
        contain at least one of era_tags (e.g. ['80s', '1980s', 'eighties']).
        """
        if self.meta_df is None:
            return self.similar_by_index(row_index, top_k, max_per_artist)

        era_tags_lower = {t.lower() for t in era_tags}
        n = self.X.shape[0]
        v = self.X[row_index : row_index + 1]
        sims = cosine_similarity(v, self.X)[0]
        sims[row_index] = -1.0
        order = np.argsort(-sims)

        recs: List[Dict] = []
        artist_counts: dict[str, int] = {}

        for j in order:
            if sims[j] <= 0:
                break
            meta = self.meta_df.iloc[j]
            raw_tags = meta.get("tags") if hasattr(meta, "get") else None
            if raw_tags is None:
                continue
            if hasattr(raw_tags, "tolist"):
                raw_tags = raw_tags.tolist()
            track_tags_lower = {str(t).lower() for t in raw_tags if t}
            if not track_tags_lower.intersection(era_tags_lower):
                continue

            artist = self.id_map[j]["artist"]
            if artist_counts.get(artist, 0) >= max_per_artist:
                continue

            recs.append(self._row_to_dict(j, sims[j], include_tags=True))
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            if len(recs) >= top_k:
                break

        return recs

    def escape_route_tracks(
        self,
        dominant_tags: list[str],
        secondary_tags: list[str],
        user_vector: Optional[np.ndarray] = None,
        top_k: int = 15,
        max_per_artist: int = 2,
    ) -> List[Dict]:
        """
        Find tracks that DON'T contain dominant tags but DO contain at least
        one secondary tag — ranked by similarity to user_vector (or random if None).
        Used by the Algorithmic Capture feature.
        """
        if self.meta_df is None:
            return []

        dom_lower = {t.lower() for t in dominant_tags}
        sec_lower = {t.lower() for t in secondary_tags}

        if user_vector is not None:
            v = user_vector.reshape(1, -1)
            sims = cosine_similarity(v, self.X)[0]
            order = np.argsort(-sims)
        else:
            order = np.random.permutation(self.X.shape[0])

        recs: List[Dict] = []
        artist_counts: dict[str, int] = {}

        for j in order:
            sim = float(sims[j]) if user_vector is not None else 0.0
            meta = self.meta_df.iloc[j]
            raw_tags = meta.get("tags") if hasattr(meta, "get") else None
            if raw_tags is None:
                continue
            if hasattr(raw_tags, "tolist"):
                raw_tags = raw_tags.tolist()
            track_tags_lower = {str(t).lower() for t in raw_tags if t}

            # Must not overlap with dominant tags
            if track_tags_lower.intersection(dom_lower):
                continue
            # Must overlap with at least one secondary tag
            if not track_tags_lower.intersection(sec_lower):
                continue

            artist = self.id_map[j]["artist"]
            if artist_counts.get(artist, 0) >= max_per_artist:
                continue

            d = self._row_to_dict(j, sim, include_tags=True)
            # Surface the matched escape tag
            matched = track_tags_lower.intersection(sec_lower)
            d["escape_tag"] = next(iter(matched), None)
            recs.append(d)
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
            if len(recs) >= top_k:
                break

        return recs

    def get_user_taste_vector(self, track_indices: list[int]) -> Optional[np.ndarray]:
        """Centroid of feature vectors for a set of tracks (used by Algorithmic Capture)."""
        valid = [i for i in track_indices if 0 <= i < self.X.shape[0]]
        if not valid:
            return None
        return self.X[valid].mean(axis=0)

    def tracks_by_artist(self, artist_name: str, top_k: int = 20) -> List[Dict]:
        """
        Return tracks by a given artist (fuzzy match) with their feature vectors.
        Used by the Séance feature.
        """
        from rapidfuzz import fuzz
        artist_lower = artist_name.lower()
        matches = []
        for j, row in enumerate(self.id_map):
            score = fuzz.token_set_ratio(row["artist"].lower(), artist_lower)
            if score >= 70:
                matches.append((j, score))
        matches.sort(key=lambda x: -x[1])
        return [self._row_to_dict(j, s / 100, include_tags=True) for j, s in matches[:top_k]]
