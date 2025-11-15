# src/recsys/io.py
from __future__ import annotations
import json
from pathlib import Path
from difflib import get_close_matches

from .config import ART  # same ART as everywhere else


def load_id_map():
    """Load the list of track metadata dicts saved during preprocessing."""
    path = ART / "id_map.json"
    with path.open() as f:
        return json.load(f)


def fuzzy_row_index(query: str, id_map=None, cutoff: float = 0.6):
    """
    Fuzzy-match a 'title — artist' string to the closest row in id_map.

    Returns:
      (row_index, row_dict) or (None, None) if nothing meets cutoff.
    """
    if id_map is None:
        id_map = load_id_map()

    labels = [f'{row["title"]} — {row["artist"]}' for row in id_map]

    match = get_close_matches(query, labels, n=1, cutoff=cutoff)
    if not match:
        return None, None

    idx = labels.index(match[0])
    return idx, id_map[idx]
