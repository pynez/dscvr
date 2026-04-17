# tests/test_interactions.py
"""
Tests for POST /interactions — interaction logging, 204 no-content.
"""
import time
from unittest.mock import patch, call


VALID_PAYLOAD = {
    "user_id": "test-user-123",
    "track_id": "5",
    "interaction_type": "heart",
    "feature": "soundtrack",
    "tags": ["pop", "indie"],
}


def test_returns_204(client):
    res = client.post("/interactions", json=VALID_PAYLOAD)
    assert res.status_code == 204


def test_204_has_no_body(client):
    res = client.post("/interactions", json=VALID_PAYLOAD)
    assert res.content == b""


def test_skip_interaction(client):
    payload = {**VALID_PAYLOAD, "interaction_type": "skip"}
    res = client.post("/interactions", json=payload)
    assert res.status_code == 204


def test_complete_interaction(client):
    payload = {**VALID_PAYLOAD, "interaction_type": "complete"}
    res = client.post("/interactions", json=payload)
    assert res.status_code == 204


def test_missing_user_id_returns_422(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "user_id"}
    res = client.post("/interactions", json=payload)
    assert res.status_code == 422


def test_missing_track_id_returns_422(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "track_id"}
    res = client.post("/interactions", json=payload)
    assert res.status_code == 422


def test_missing_interaction_type_returns_422(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "interaction_type"}
    res = client.post("/interactions", json=payload)
    assert res.status_code == 422


def test_empty_body_returns_422(client):
    res = client.post("/interactions", json={})
    assert res.status_code == 422


def test_tags_are_optional(client):
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "tags"}
    res = client.post("/interactions", json=payload)
    assert res.status_code == 204


def test_db_log_interaction_is_called(client):
    """Verify the endpoint actually triggers db.log_interaction (fire-and-forget)."""
    with patch("src.recsys.service.db.log_interaction") as mock_log:
        res = client.post("/interactions", json=VALID_PAYLOAD)
        assert res.status_code == 204
        # Give the background task a moment to run
        time.sleep(0.05)
        mock_log.assert_called_once_with(
            "test-user-123", "5", "heart", "soundtrack"
        )


def test_db_update_taste_profile_called_when_tags_present(client):
    """Tags trigger a taste profile update."""
    with (
        patch("src.recsys.service.db.log_interaction"),
        patch("src.recsys.service.db.update_taste_profile") as mock_update,
    ):
        client.post("/interactions", json=VALID_PAYLOAD)
        time.sleep(0.05)
        mock_update.assert_called_once_with(
            "test-user-123", ["pop", "indie"], "heart"
        )


def test_no_taste_profile_update_when_no_tags(client):
    """Empty tags list should not trigger a taste profile update."""
    payload = {**VALID_PAYLOAD, "tags": []}
    with (
        patch("src.recsys.service.db.log_interaction"),
        patch("src.recsys.service.db.update_taste_profile") as mock_update,
    ):
        client.post("/interactions", json=payload)
        time.sleep(0.05)
        mock_update.assert_not_called()
