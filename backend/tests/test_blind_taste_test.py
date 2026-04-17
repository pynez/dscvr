# tests/test_blind_taste_test.py
"""
Tests for GET /blind-taste-test and POST /blind-taste-test/reveal.
Also unit-tests for the feature module's pure functions.
"""
import pytest
from unittest.mock import MagicMock
import pandas as pd


class TestBlindTasteTestSession:
    def test_returns_200(self, client):
        res = client.get("/blind-taste-test")
        assert res.status_code == 200

    def test_response_has_tracks(self, client):
        body = res = client.get("/blind-taste-test").json()
        assert "tracks" in body
        assert isinstance(body["tracks"], list)

    def test_returns_up_to_10_tracks(self, client):
        body = client.get("/blind-taste-test").json()
        assert len(body["tracks"]) <= 10

    def test_tracks_only_expose_blind_fields(self, client):
        body = client.get("/blind-taste-test").json()
        for track in body["tracks"]:
            assert "row_index" in track
            # Metadata must NOT be present in the blind session
            assert "name" not in track
            assert "artist" not in track
            assert "artwork_url" not in track
            assert "tags" not in track

    def test_each_track_has_row_index(self, client):
        body = client.get("/blind-taste-test").json()
        for track in body["tracks"]:
            assert isinstance(track["row_index"], int)


class TestBlindReveal:
    def test_returns_200(self, client):
        res = client.post("/blind-taste-test/reveal", json={"track_indices": [0, 1, 2]})
        assert res.status_code == 200

    def test_response_has_tracks(self, client):
        body = client.post("/blind-taste-test/reveal", json={"track_indices": [0]}).json()
        assert "tracks" in body
        assert isinstance(body["tracks"], list)

    def test_revealed_tracks_have_full_metadata(self, client):
        body = client.post("/blind-taste-test/reveal", json={"track_indices": [0]}).json()
        for track in body["tracks"]:
            assert "row_index" in track
            assert "name" in track
            assert "artist" in track
            assert "tags" in track

    def test_revealed_count_matches_requested(self, client):
        indices = [0, 1, 2]
        body = client.post("/blind-taste-test/reveal", json={"track_indices": indices}).json()
        assert len(body["tracks"]) == len(indices)

    def test_out_of_range_indices_are_skipped(self, client):
        body = client.post(
            "/blind-taste-test/reveal", json={"track_indices": [0, 99999]}
        ).json()
        # Only valid index (0) is returned
        assert len(body["tracks"]) == 1

    def test_empty_indices_returns_empty_tracks(self, client):
        body = client.post("/blind-taste-test/reveal", json={"track_indices": []}).json()
        assert body["tracks"] == []

    def test_missing_track_indices_returns_422(self, client):
        res = client.post("/blind-taste-test/reveal", json={})
        assert res.status_code == 422


class TestBlindTasteTestUnit:
    """Unit tests for get_session and reveal directly."""

    def _make_recommender(self):
        rec = MagicMock()
        rec.id_map = [
            {"title": f"Track {i}", "artist": f"Artist {i}", "preview_url": f"https://preview/{i}", "artwork_url": None}
            for i in range(20)
        ]
        meta_rows = [
            {"title": f"Track {i}", "artist": f"Artist {i}", "preview_url": f"https://preview/{i}", "artwork_url": None, "tags": ["pop"]}
            for i in range(20)
        ]
        rec.meta_df = pd.DataFrame(meta_rows)
        return rec

    def test_get_session_returns_10_tracks(self):
        from src.recsys.service.features.blind_taste_test import get_session
        rec = self._make_recommender()
        result = get_session(rec)
        assert len(result["tracks"]) == 10

    def test_get_session_strips_metadata(self):
        from src.recsys.service.features.blind_taste_test import get_session
        rec = self._make_recommender()
        result = get_session(rec)
        for track in result["tracks"]:
            assert "name" not in track
            assert "artist" not in track

    def test_get_session_includes_row_index(self):
        from src.recsys.service.features.blind_taste_test import get_session
        rec = self._make_recommender()
        result = get_session(rec)
        for track in result["tracks"]:
            assert "row_index" in track

    def test_reveal_returns_name_and_artist(self):
        from src.recsys.service.features.blind_taste_test import reveal
        rec = self._make_recommender()
        result = reveal([0, 1], rec)
        assert len(result["tracks"]) == 2
        assert result["tracks"][0]["name"] == "Track 0"
        assert result["tracks"][0]["artist"] == "Artist 0"

    def test_reveal_skips_invalid_indices(self):
        from src.recsys.service.features.blind_taste_test import reveal
        rec = self._make_recommender()
        result = reveal([0, 999], rec)
        assert len(result["tracks"]) == 1

    def test_reveal_includes_tags(self):
        from src.recsys.service.features.blind_taste_test import reveal
        rec = self._make_recommender()
        result = reveal([0], rec)
        assert "tags" in result["tracks"][0]
        assert isinstance(result["tracks"][0]["tags"], list)
