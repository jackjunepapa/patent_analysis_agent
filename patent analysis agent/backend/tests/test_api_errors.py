from __future__ import annotations


def test_index_build_requires_files(client):
    r = client.post("/api/v1/index/build", files=[], data={})
    assert r.status_code == 400


def test_analyze_unknown_session(client):
    r = client.post(
        "/api/v1/analyze",
        json={"session_id": "deadbeefdeadbeefdeadbeefdeadbeef", "language": "ko"},
    )
    assert r.status_code == 404
