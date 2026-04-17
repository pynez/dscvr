# tests/conftest.py
"""
Shared test configuration and fixtures for all DSCVR API tests.

Module-level patches run at import time (before api.py is first loaded),
so the heavy artifact-loading in CosineRecommender and SearchIndex never
touches the filesystem during tests.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

# ── Constants ────────────────────────────────────────────────────────────────

N = 20  # number of fake catalog tracks
ERAS = ["60s", "70s", "80s", "90s", "00s"]
GENRES = ["pop", "rock", "indie", "jazz", "soul"]


# ── Fake catalog data ────────────────────────────────────────────────────────

def _fake_id_map(n: int = N) -> list[dict]:
    return [
        {
            "title": f"Track {i}",
            "artist": f"Artist {i % 5}",
            "preview_url": None,
            "artwork_url": None,
        }
        for i in range(n)
    ]


def _fake_meta_df(n: int = N) -> pd.DataFrame:
    rows = [
        {
            "title": f"Track {i}",
            "artist": f"Artist {i % 5}",
            "preview_url": None,
            "artwork_url": None,
            # Each track gets a genre tag + an era tag for era-filter tests
            "tags": [GENRES[i % 5], ERAS[i % 5]],
        }
        for i in range(n)
    ]
    return pd.DataFrame(rows)


class _FakePipeline:
    """Drop-in for the TF-IDF+SVD pipeline used by similar_by_text."""
    def transform(self, texts):
        return np.ones((len(texts), 50), dtype=np.float32)


def _fake_cosine_init(self) -> None:
    """Replacement __init__ — uses in-memory data, no disk reads."""
    # Use positive random values (fixed seed) so cosine similarities are
    # all non-zero — identity matrix makes tracks orthogonal which causes
    # similar_by_index to return no results (it stops at cos_sim <= 0).
    rng = np.random.default_rng(42)
    self.X = rng.random((N, 50)).astype(np.float32)
    self.id_map = _fake_id_map()
    self.meta_df = _fake_meta_df()
    self._pipeline = _FakePipeline()  # prevents joblib.load call


# ── Apply module-level patches before api.py is ever imported ────────────────
# These run at conftest-import time (pytest loads conftest before test files).

import src.recsys.recommenders.cosine as _cosine_mod  # noqa: E402
_cosine_mod.CosineRecommender.__init__ = _fake_cosine_init

import src.recsys.search as _search_mod  # noqa: E402

_orig_search_init = _search_mod.SearchIndex.__init__


def _fake_search_init(self, df: pd.DataFrame) -> None:
    from src.recsys.search import norm, EM_DASH
    self.exact_index = {
        norm(f"Track {i} {EM_DASH} Artist {i % 5}"): i for i in range(N)
    }
    self._df = df


def _fake_search_match(self, query: str, limit: int = 8):
    return (0, 95.0, [0, 1, 2])


def _fake_search_top_matches(self, query: str, limit: int = 8) -> list[dict]:
    return [
        {
            "row_index": i,
            "title": f"Track {i}",
            "artist": f"Artist {i % 5}",
            "score": float(95 - i),
            "artwork_url": None,
            "preview_url": None,
        }
        for i in range(min(limit, N))
    ]


_search_mod.SearchIndex.__init__ = _fake_search_init
_search_mod.SearchIndex.match = _fake_search_match
_search_mod.SearchIndex.top_matches = _fake_search_top_matches


# ── Canned Gemini responses ──────────────────────────────────────────────────

def _gemini_response(prompt: str):
    """
    Returns appropriate fake JSON depending on context.
    - If the prompt looks like a 'filter living artists' prompt → list of names
    - Otherwise → tracks+summary dict (soundtrack / séance / time machine)
    """
    if "LIVING (not deceased)" in prompt:
        return ["Artist 0", "Artist 1", "Artist 2"]

    return {
        "tracks": [
            {
                "row_index": i,
                "track_name": f"Track {i}",
                "artist": f"Artist {i % 5}",
                "reasoning": "Fits the moment.",
                "connection": "Spiritual successor.",
            }
            for i in range(5)
        ],
        "summary": "A curated selection for the moment.",
    }


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """
    FastAPI TestClient with ALL external dependencies mocked:
      - Gemini (generate_json)
      - Preview resolver (resolve_batch)
      - Supabase DB helpers
      - Last.fm (seance._lastfm_similar_artists)
    """
    fake_history = [
        {"track_id": str(i), "interaction_type": "heart", "feature": "explore"}
        for i in range(10)
    ]

    with (
        patch(
            "src.recsys.service.gemini_client.generate_json",
            side_effect=_gemini_response,
        ),
        patch(
            "src.recsys.service.preview_resolver.resolve_batch",
            new=AsyncMock(side_effect=lambda tracks: tracks),
        ),
        patch("src.recsys.service.db.log_interaction"),
        patch("src.recsys.service.db.update_taste_profile"),
        patch("src.recsys.service.db.register_user"),
        patch(
            "src.recsys.service.db.get_interaction_history",
            return_value=fake_history,
        ),
        patch(
            "src.recsys.service.features.seance._lastfm_similar_artists",
            return_value=["Artist 0", "Artist 1", "Artist 2", "Artist 3"],
        ),
    ):
        from src.recsys.service.api import app
        from fastapi.testclient import TestClient

        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
