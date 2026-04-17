# tests/test_algorithmic_capture.py
"""
Tests for GET /algorithmic-capture — taste homogeneity scoring.
Includes unit tests for the pure-logic helpers.
"""
import pytest
import math
from collections import Counter


# ── Unit tests for pure-logic functions ──────────────────────────────────────

class TestShannonEntropy:
    def test_uniform_distribution_has_max_entropy(self):
        from src.recsys.service.features.algorithmic_capture import _shannon_entropy
        # 4 equally-likely tags → entropy = log2(4) = 2.0
        counts = Counter({"a": 10, "b": 10, "c": 10, "d": 10})
        entropy = _shannon_entropy(counts)
        assert abs(entropy - math.log2(4)) < 1e-9

    def test_single_tag_has_zero_entropy(self):
        from src.recsys.service.features.algorithmic_capture import _shannon_entropy
        counts = Counter({"only_tag": 100})
        assert _shannon_entropy(counts) == 0.0

    def test_empty_counter_returns_zero(self):
        from src.recsys.service.features.algorithmic_capture import _shannon_entropy
        assert _shannon_entropy(Counter()) == 0.0

    def test_two_equal_tags_entropy(self):
        from src.recsys.service.features.algorithmic_capture import _shannon_entropy
        counts = Counter({"a": 5, "b": 5})
        assert abs(_shannon_entropy(counts) - 1.0) < 1e-9


class TestCaptureScore:
    """Verify the capture score formula: 1 - (entropy / log2(n))."""

    def test_high_capture_when_one_dominant_tag(self):
        """One tag overwhelmingly dominant → high capture score."""
        from src.recsys.service.features.algorithmic_capture import _shannon_entropy
        counts = Counter({"pop": 100, "rock": 1})
        n = len(counts)
        entropy = _shannon_entropy(counts)
        score = 1.0 - (entropy / math.log2(n))
        assert score > 0.7

    def test_low_capture_when_uniform(self):
        """Perfectly uniform distribution → capture score near 0."""
        from src.recsys.service.features.algorithmic_capture import _shannon_entropy
        n = 8
        counts = Counter({f"tag{i}": 10 for i in range(n)})
        entropy = _shannon_entropy(counts)
        score = 1.0 - (entropy / math.log2(n))
        assert abs(score) < 1e-9


# ── API tests ─────────────────────────────────────────────────────────────────

class TestAlgorithmicCaptureAPI:
    def test_returns_200_with_history(self, client):
        # conftest provides 10 fake interactions → enough to compute score
        res = client.get("/algorithmic-capture?user_id=test-user-123")
        assert res.status_code == 200

    def test_response_shape_with_data(self, client):
        body = client.get("/algorithmic-capture?user_id=test-user-123").json()
        assert "capture_score" in body
        assert "dominant_tags" in body
        assert "underexplored_tags" in body
        assert "escape_tracks" in body
        assert "insufficient_data" in body

    def test_insufficient_data_flag_when_few_interactions(self, client):
        from unittest.mock import patch

        with patch(
            "src.recsys.service.db.get_interaction_history",
            return_value=[],  # zero history
        ):
            body = client.get("/algorithmic-capture?user_id=new-user").json()

        assert body["insufficient_data"] is True
        assert body["capture_score"] is None

    def test_interactions_needed_when_insufficient(self, client):
        from unittest.mock import patch

        with patch(
            "src.recsys.service.db.get_interaction_history",
            return_value=[],
        ):
            body = client.get("/algorithmic-capture?user_id=new-user").json()

        assert body["interactions_needed"] == 5  # MIN_INTERACTIONS = 5

    def test_capture_score_between_0_and_1(self, client):
        body = client.get("/algorithmic-capture?user_id=test-user-123").json()
        if body["capture_score"] is not None:
            assert 0.0 <= body["capture_score"] <= 1.0

    def test_missing_user_id_returns_422(self, client):
        res = client.get("/algorithmic-capture")
        assert res.status_code == 422

    def test_escape_tracks_are_list(self, client):
        body = client.get("/algorithmic-capture?user_id=test-user-123").json()
        assert isinstance(body["escape_tracks"], list)

    def test_x_user_id_header_takes_precedence(self, client):
        from unittest.mock import patch

        captured_uid = []

        def capture_history(user_id, types=None):
            captured_uid.append(user_id)
            return [
                {"track_id": str(i), "interaction_type": "heart", "feature": "explore"}
                for i in range(10)
            ]

        with patch(
            "src.recsys.service.db.get_interaction_history",
            side_effect=capture_history,
        ):
            client.get(
                "/algorithmic-capture?user_id=query-user",
                headers={"X-User-ID": "header-user"},
            )

        assert captured_uid[0] == "header-user"
