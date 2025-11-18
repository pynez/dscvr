# src/recsys/recommenders/cosine.py
from __future__ import annotations
from typing import List, Dict
import json

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..config import ART        # uses data/artifacts from your existing config
from .base import Recommender


class CosineRecommender(Recommender):
    """Cosine similarity over the text-based feature matrix."""

    def __init__(self) -> None:
        features_path = ART / "features.npy"
        id_map_path = ART / "id_map.json"

        if not features_path.exists() or not id_map_path.exists():
            raise RuntimeError(
                "Missing artifacts. Did you run `python -m src.cli.train_text`?"
            )

        self.X = np.load(features_path)
        with id_map_path.open() as f:
            self.id_map = json.load(f)

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
            cnt = artist_counts.get(artist, 0)
            if cnt >= max_per_artist:
                continue

            recs.append(
                {
                    "row_index": int(j),
                    "name": row["title"],
                    "artist": artist,
                    "score": float(sims[j]),
                    "preview_url": row.get("preview_url"),
                    "artwork_url": row.get("artwork_url"),
                }
            )
            artist_counts[artist] = cnt + 1

            if len(recs) >= top_k:
                break

        return recs