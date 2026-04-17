# tests/test_health_search.py
"""
Tests for GET /health and GET /search endpoints.
"""


def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert "tracks" in body
    assert isinstance(body["tracks"], int)


def test_health_reports_catalog_size(client):
    res = client.get("/health")
    # Our fake catalog has N=20 tracks
    assert res.json()["tracks"] == 20


class TestSearch:
    def test_returns_200_with_results(self, client):
        res = client.get("/search?q=Track")
        assert res.status_code == 200
        body = res.json()
        assert "query" in body
        assert "results" in body
        assert isinstance(body["results"], list)

    def test_each_result_has_required_fields(self, client):
        res = client.get("/search?q=Track 0")
        results = res.json()["results"]
        assert len(results) > 0
        for r in results:
            assert "row_index" in r
            assert "title" in r
            assert "artist" in r
            assert "score" in r
            assert "track_key" in r

    def test_empty_query_returns_empty_results(self, client):
        res = client.get("/search?q=   ")
        assert res.status_code == 200
        assert res.json()["results"] == []

    def test_limit_parameter_respected(self, client):
        res = client.get("/search?q=Track&limit=3")
        assert res.status_code == 200
        assert len(res.json()["results"]) <= 3

    def test_missing_q_returns_422(self, client):
        res = client.get("/search")
        assert res.status_code == 422
