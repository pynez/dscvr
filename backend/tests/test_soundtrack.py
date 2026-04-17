# tests/test_soundtrack.py
"""
Tests for POST /soundtrack — Soundtrack Your Life feature.
"""
import pytest


VALID_PAYLOAD = {"description": "driving home alone at 2am, windows down"}


class TestSoundtrackAPI:
    def test_returns_200(self, client):
        res = client.post("/soundtrack", json=VALID_PAYLOAD)
        assert res.status_code == 200

    def test_response_has_tracks_and_summary(self, client):
        res = client.post("/soundtrack", json=VALID_PAYLOAD)
        body = res.json()
        assert "tracks" in body
        assert "summary" in body
        assert isinstance(body["tracks"], list)

    def test_tracks_have_required_fields(self, client):
        res = client.post("/soundtrack", json=VALID_PAYLOAD)
        for track in res.json()["tracks"]:
            assert "name" in track
            assert "artist" in track

    def test_tracks_have_reasoning(self, client):
        res = client.post("/soundtrack", json=VALID_PAYLOAD)
        # All returned tracks should have a reasoning field
        for track in res.json()["tracks"]:
            assert "reasoning" in track

    def test_empty_description_returns_400(self, client):
        res = client.post("/soundtrack", json={"description": "   "})
        assert res.status_code == 400

    def test_missing_description_returns_422(self, client):
        res = client.post("/soundtrack", json={})
        assert res.status_code == 422

    def test_user_id_header_accepted(self, client):
        res = client.post(
            "/soundtrack",
            json=VALID_PAYLOAD,
            headers={"X-User-ID": "test-user-abc"},
        )
        assert res.status_code == 200

    def test_user_id_in_body_accepted(self, client):
        payload = {**VALID_PAYLOAD, "user_id": "test-user-abc"}
        res = client.post("/soundtrack", json=payload)
        assert res.status_code == 200


class TestSoundtrackGeminiGracefulFallback:
    """When Gemini fails the endpoint should still return tracks."""

    def test_gemini_error_returns_fallback(self, client):
        from unittest.mock import patch

        with patch(
            "src.recsys.service.gemini_client.generate_json",
            side_effect=RuntimeError("Gemini unavailable"),
        ):
            res = client.post("/soundtrack", json=VALID_PAYLOAD)
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body["tracks"], list)


class TestSoundtrackFeatureUnit:
    """Unit tests for the soundtrack feature module directly."""

    @pytest.mark.asyncio
    async def test_run_returns_correct_structure(self):
        from unittest.mock import MagicMock, patch, AsyncMock
        import numpy as np

        mock_rec = MagicMock()
        mock_rec.similar_by_text.return_value = [
            {
                "row_index": i,
                "name": f"Track {i}",
                "artist": f"Artist {i}",
                "preview_url": None,
                "artwork_url": None,
            }
            for i in range(10)
        ]

        fake_gemini = {
            "tracks": [
                {
                    "row_index": 0,
                    "track_name": "Track 0",
                    "artist": "Artist 0",
                    "reasoning": "Fits perfectly.",
                }
            ],
            "summary": "Great playlist.",
        }

        with (
            patch(
                "src.recsys.service.gemini_client.generate_json",
                return_value=fake_gemini,
            ),
            patch(
                "src.recsys.service.preview_resolver.resolve_batch",
                new=AsyncMock(side_effect=lambda t: t),
            ),
        ):
            from src.recsys.service.features import soundtrack

            result = await soundtrack.run(
                description="a rainy evening", recommender=mock_rec
            )

        assert "tracks" in result
        assert "summary" in result
        assert result["summary"] == "Great playlist."
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["name"] == "Track 0"

    @pytest.mark.asyncio
    async def test_run_returns_empty_when_no_candidates(self):
        from unittest.mock import MagicMock

        mock_rec = MagicMock()
        mock_rec.similar_by_text.return_value = []

        from src.recsys.service.features import soundtrack

        result = await soundtrack.run(description="xyz", recommender=mock_rec)
        assert result["tracks"] == []
