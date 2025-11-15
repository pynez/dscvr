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

    def similar_by_index(self, row_index: int, top_k: int = 10) -> List[Dict]:
        """Return top_k most similar tracks to the given row_index."""
        n = self.X.shape[0]
        if row_index < 0 or row_index >= n:
            raise IndexError(f"row_index {row_index} out of range [0, {n})")

        # 1 x d vector
        v = self.X[row_index : row_index + 1]
        sims = cosine_similarity(v, self.X)[0]  # shape: (n,)

        # Exclude the item itself
        sims[row_index] = -1.0

        # Get indices of the top_k highest similarity scores
        if top_k >= n:
            idxs = np.argsort(-sims)  # sort all
        else:
            # partial sort for speed, then order that subset
            idxs = np.argpartition(-sims, range(top_k))[:top_k]
            idxs = idxs[np.argsort(-sims[idxs])]

        recs: List[Dict] = []
        for j in idxs:
            row = self.id_map[j]
            recs.append(
                {
                    "row_index": int(j),
                    "name": row["title"],
                    "artist": row["artist"],
                    "score": float(sims[j]),
                    "preview_url": row.get("preview_url"),
                    "artwork_url": row.get("artwork_url"),
                }
            )
        return recs
