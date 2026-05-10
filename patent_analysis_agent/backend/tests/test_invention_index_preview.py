from __future__ import annotations

from langchain_core.documents import Document

from phase2_analysis import invention_index_preview


def test_invention_index_preview_claim_chunks_and_body_count():
    meta = [
        {
            "source_file": "inv.txt",
            "jurisdiction": "KR",
            "claim1_full": "제1항. 본 발명은 예시이다.",
        }
    ]
    merged = [
        Document(
            page_content="TITLE: T\nREF_TERMS:\nchunk body",
            metadata={
                "doc_type": "invention",
                "source_file": "inv.txt",
                "chunk_id": "b1",
            },
        ),
        Document(
            page_content="lim text here",
            metadata={
                "doc_type": "invention_claims",
                "source_file": "inv.txt",
                "chunk_id": "c1",
                "limitation_id": "L1",
                "limitation_role": "element",
                "limitation_order": 0,
                "metadata_schema_version": "v2_phase2",
            },
        ),
    ]
    out = invention_index_preview(merged, meta)
    assert out["claim_parsing"][0]["source_file"] == "inv.txt"
    assert out["claim_parsing"][0]["jurisdiction"] == "KR"
    assert "예시" in out["claim_parsing"][0]["claim1_excerpt"]
    assert out["invention_body_chunk_count"] == 1
    assert len(out["invention_claim_chunks"]) == 1
    assert out["invention_claim_chunks"][0]["chunk_id"] == "c1"
    assert out["invention_claim_chunks"][0]["limitation_id"] == "L1"
    assert "lim text" in out["invention_claim_chunks"][0]["content_preview"]


def test_invention_index_preview_empty_merged_still_shows_parsing():
    meta = [{"source_file": "x.pdf", "jurisdiction": "US", "claim1_full": "Claim 1. A widget."}]
    out = invention_index_preview([], meta)
    assert len(out["claim_parsing"]) == 1
    assert out["invention_claim_chunks"] == []
    assert out["invention_body_chunk_count"] == 0
