# tests/test_seance.py
"""
Tests for POST /seance — The Séance feature.
"""
import pytest


VALID_PAYLOAD = {"artist": "Kurt Cobain"}


class TestSeanceAPI:
    def test_returns_200(self, client):
        res = client.post("/seance", json=VALID_PAYLOAD)
        assert res.status_code == 200

    def test_response_shape(self, client):
        body = client.post("/seance", json=VALID_PAYLOAD).json()
        assert "original_artist" in body
        assert "tracks" in body
        assert "summary" in body

    def test_original_artist_echoed(self, client):
        body = client.post("/seance", json=VALID_PAYLOAD).json()
        assert body["original_artist"] == "Kurt Cobain"

    def test_tracks_have_required_fields(self, client):
        body = client.post("/seance", json=VALID_PAYLOAD).json()
        for track in body["tracks"]:
            assert "name" in track
            assert "artist" in track

    def test_tracks_have_connection_field(self, client):
        body = client.post("/seance", json=VALID_PAYLOAD).json()
        for track in body["tracks"]:
            assert "connection" in track

    def test_empty_artist_returns_400(self, client):
        res = client.post("/seance", json={"artist": "   "})
        assert res.status_code == 400

    def test_missing_artist_returns_422(self, client):
        res = client.post("/seance", json={})
        assert res.status_code == 422

    def test_no_similar_artists_returns_empty_tracks(self, client):
        from unittest.mock import patch

        with patch(
            "src.recsys.service.features.seance._lastfm_similar_artists",
            return_value=[],
        ):
            body = client.post("/seance", json=VALID_PAYLOAD).json()

        assert body["tracks"] == []

    def test_gemini_fallback_when_living_filter_fails(self, client):
        from unittest.mock import patch

        call_count = [0]

        def failing_living_filter(prompt):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Gemini unavailable")
            # Second call for reasoning
            return {
                "tracks": [
                    {"row_index": 0, "track_name": "Track 0", "artist": "Artist 0", "connection": "close"}
                ],
                "summary": "summary",
            }

        with patch(
            "src.recsys.service.gemini_client.generate_json",
            side_effect=failing_living_filter,
        ):
            res = client.post("/seance", json=VALID_PAYLOAD)

        # Should still succeed (uses all similar artists as fallback)
        assert res.status_code == 200


class TestSeanceFeatureUnit:
    @pytest.mark.asyncio
    async def test_run_returns_correct_structure(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        import numpy as np

        mock_rec = MagicMock()
        mock_rec.tracks_by_artist.return_value = [
            {"row_index": 0, "name": "Original Track", "artist": "Kurt Cobain", "score": 1.0}
        ]
        mock_rec.id_map = [
            {"title": f"Track {i}", "artist": f"Artist {i % 3}", "preview_url": None, "artwork_url": None}
            for i in range(10)
        ]
        mock_rec.X = np.eye(10, 50, dtype=np.float32)
        mock_rec.get_user_taste_vector.return_value = np.ones(50)
        mock_rec._row_to_dict.side_effect = lambda j, s, **kw: {
            "row_index": j,
            "name": f"Track {j}",
            "artist": f"Artist {j % 3}",
            "score": s,
            "preview_url": None,
            "artwork_url": None,
        }

        with (
            patch(
                "src.recsys.service.features.seance._lastfm_similar_artists",
                return_value=["Artist 0", "Artist 1"],
            ),
            patch(
                "src.recsys.service.gemini_client.generate_json",
                side_effect=lambda p: (
                    ["Artist 0", "Artist 1"]
                    if "LIVING" in p
                    else {
                        "tracks": [
                            {"row_index": 0, "track_name": "Track 0", "artist": "Artist 0", "connection": "soulful"}
                        ],
                        "summary": "Spiritual successors.",
                    }
                ),
            ),
            patch(
                "src.recsys.service.preview_resolver.resolve_batch",
                new=AsyncMock(side_effect=lambda t: t),
            ),
        ):
            from src.recsys.service.features import seance

            result = await seance.run(artist="Kurt Cobain", recommender=mock_rec)

        assert result["original_artist"] == "Kurt Cobain"
        assert isinstance(result["tracks"], list)
        assert "summary" in result
