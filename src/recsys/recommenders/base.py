# src/recsys/recommenders/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict


class Recommender(ABC):
    """Abstract base class for recommendation backends."""

    @abstractmethod
    def similar_by_index(self, row_index: int, top_k: int = 10) -> List[Dict]:
        """
        Given a row index into the feature matrix, return a list of
        recommended items as dicts. Each dict should at least contain:
        - row_index (int)
        - name (str)
        - artist (str)
        - score (float)
        - preview_url (optional, str)
        - artwork_url (optional, str)
        """
        ...
