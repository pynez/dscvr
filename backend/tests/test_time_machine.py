# tests/test_time_machine.py
"""
Tests for POST /time-machine — era-filtered cosine recommendations.
"""
import pytest


VALID_PAYLOAD = {
    "seed_track": "Track 0",
    "seed_artist": "Artist 0",
    "era": "80s",
}


class TestTimeMachineAPI:
    def test_returns_200(self, client):
        res = client.post("/time-machine", json=VALID_PAYLOAD)
        assert res.status_code == 200

    def test_response_shape(self, client):
        body = client.post("/time-machine", json=VALID_PAYLOAD).json()
        assert "tracks" in body
        assert "era" in body
        assert "seed_track" in body
        assert "seed_artist" in body
        assert "summary" in body

    def test_era_echoed_in_response(self, client):
        body = client.post("/time-machine", json=VALID_PAYLOAD).json()
        assert body["era"] == "80s"

    def test_seed_echoed_in_response(self, client):
        body = client.post("/time-machine", json=VALID_PAYLOAD).json()
        assert body["seed_track"] == "Track 0"
        assert body["seed_artist"] == "Artist 0"

    def test_tracks_have_required_fields(self, client):
        body = client.post("/time-machine", json=VALID_PAYLOAD).json()
        for track in body["tracks"]:
            assert "name" in track
            assert "artist" in track

    @pytest.mark.parametrize("era", ["60s", "70s", "80s", "90s", "00s"])
    def test_all_valid_eras_accepted(self, client, era):
        payload = {**VALID_PAYLOAD, "era": era}
        res = client.post("/time-machine", json=payload)
        assert res.status_code == 200

    def test_invalid_era_returns_400(self, client):
        payload = {**VALID_PAYLOAD, "era": "10s"}
        res = client.post("/time-machine", json=payload)
        assert res.status_code == 400

    def test_missing_era_returns_422(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "era"}
        res = client.post("/time-machine", json=payload)
        assert res.status_code == 422

    def test_missing_seed_track_returns_422(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "seed_track"}
        res = client.post("/time-machine", json=payload)
        assert res.status_code == 422


class TestTimeMachineFeatureUnit:
    @pytest.mark.asyncio
    async def test_run_returns_correct_structure(self):
        from unittest.mock import MagicMock, patch, AsyncMock

        mock_rec = MagicMock()
        mock_rec.similar_by_index_era.return_value = [
            {
                "row_index": i,
                "name": f"Track {i}",
                "artist": f"Artist {i}",
                "score": 0.9,
                "preview_url": None,
                "artwork_url": None,
                "tags": ["80s", "rock"],
            }
            for i in range(5)
        ]

        mock_idx = MagicMock()
        mock_idx.match.return_value = (0, 90.0, [0])

        with patch(
            "src.recsys.service.preview_resolver.resolve_batch",
            new=AsyncMock(side_effect=lambda t: t),
        ):
            from src.recsys.service.features import time_machine

            result = await time_machine.run(
                seed_track="Track 0",
                seed_artist="Artist 0",
                era="80s",
                recommender=mock_rec,
                search_index=mock_idx,
            )

        assert result["era"] == "80s"
        assert result["seed_track"] == "Track 0"
        assert len(result["tracks"]) == 5

    @pytest.mark.asyncio
    async def test_run_returns_empty_when_seed_not_found(self):
        from unittest.mock import MagicMock

        mock_rec = MagicMock()
        mock_idx = MagicMock()
        mock_idx.match.return_value = (None, 0.0, [])  # nothing found

        from src.recsys.service.features import time_machine

        result = await time_machine.run(
            seed_track="Unknown",
            seed_artist="Unknown",
            era="80s",
            recommender=mock_rec,
            search_index=mock_idx,
        )
        assert result["tracks"] == []

    def test_era_tag_map_covers_all_eras(self):
        from src.recsys.service.features.time_machine import ERA_TAG_MAP

        for era in ("60s", "70s", "80s", "90s", "00s"):
            assert era in ERA_TAG_MAP
            assert len(ERA_TAG_MAP[era]) > 0
