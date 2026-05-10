"""OPENAI_API_KEY·네트워크가 있을 때만 실행."""
from __future__ import annotations

import pytest

from tests.fixtures_patents import KR_INVENTION_SAMPLE, KR_PRIOR_SAMPLE

pytestmark = [
    pytest.mark.phase3,
    pytest.mark.skipif(
        not __import__("os").getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY 없음",
    ),
]


def test_index_build_invention_only_blocks_prior_compare(client):
    files = [
        ("invention", ("inv.txt", KR_INVENTION_SAMPLE, "text/plain")),
    ]
    r = client.post("/api/v1/index/build", files=files, data={"use_llm_refine": "false"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("has_prior_art") is False
    sid = body["session_id"]
    ra = client.post("/api/v1/analyze", json={"session_id": sid, "language": "ko"})
    assert ra.status_code == 422, ra.text


def test_analyze_invention_sync_after_invention_only_index(client):
    files = [
        ("invention", ("inv.txt", KR_INVENTION_SAMPLE, "text/plain")),
    ]
    r = client.post("/api/v1/index/build", files=files, data={"use_llm_refine": "false"})
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    ri = client.post("/api/v1/analyze/invention", json={"session_id": sid, "language": "ko"})
    assert ri.status_code == 200, ri.text
    out = ri.json()
    assert out.get("invention_summary_markdown")
    assert "claim_mapping_markdown" in out
    assert isinstance(out.get("claim_mapping_markdown"), str)


def test_index_build_analyze_stream_roundtrip(client):
    files = [
        ("invention", ("inv.txt", KR_INVENTION_SAMPLE, "text/plain")),
        ("prior", ("prior.txt", KR_PRIOR_SAMPLE, "text/plain")),
    ]
    r = client.post("/api/v1/index/build", files=files, data={"use_llm_refine": "false"})
    assert r.status_code == 200, r.text
    sid = r.json()["session_id"]
    assert sid

    ra = client.post("/api/v1/analyze", json={"session_id": sid, "language": "ko"})
    assert ra.status_code == 200, ra.text
    body = ra.json()
    assert body.get("analysis_markdown")
    assert body.get("comparison_table_markdown")

    rs = client.post("/api/v1/analyze/stream", json={"session_id": sid, "language": "ko"})
    assert rs.status_code == 200
    assert b"event: meta" in rs.content
    assert b"event: phase" in rs.content
    assert b'"phase"' in rs.content or b"reasoning" in rs.content
    assert b"event: done" in rs.content
