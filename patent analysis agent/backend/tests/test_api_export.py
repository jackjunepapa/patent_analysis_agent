"""OPENAI 키 없이 DOCX 내보내기만 검증."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.phase3


def test_export_docx_combined_returns_octet_stream(client):
    r = client.post(
        "/api/v1/export/docx/combined",
        json={
            "analysis_markdown": "## 분석\n\n본문입니다.",
            "comparison_table_markdown": "| 항목 | 값 |\n| --- | --- |\n| A | B |",
            "language": "ko",
        },
    )
    assert r.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in (
        r.headers.get("content-type") or ""
    )
    assert len(r.content) > 800
