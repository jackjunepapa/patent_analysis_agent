"""Phase 2: 청구–명세 매핑 휴리스틱(임베딩·PDF 없음)."""
from __future__ import annotations

from langchain_core.documents import Document

from phase2_description_mapping import link_claim_segments_to_chunks


def test_link_claim_segments_finds_prior_chunk_with_shared_terms() -> None:
    claim = (
        "1. A device comprising: a compensation capacitor as reference numeral 200; "
        "wherein the capacitor 200 reduces image retention."
    )
    retrieved = [
        Document(
            page_content="noise unrelated text",
            metadata={"source_file": "noise.txt", "doc_type": "invention", "chunk_id": "n1"},
        ),
        Document(
            page_content="[0045] The prior art teaches PRIORUNIQUE998MARK and discusses capacitor 200 placement.",
            metadata={
                "source_file": "prior.pdf",
                "doc_type": "prior_art",
                "chunk_id": "p1",
                "paragraph_anchor": "[0045]",
            },
        ),
    ]
    hints = link_claim_segments_to_chunks(claim, "US", retrieved)
    assert hints
    flat = [h for row in hints for h in row.get("citation_hits") or []]
    assert any(h.get("source_file") == "prior.pdf" for h in flat)
    assert any(h.get("paragraph_anchor") == "[0045]" for h in flat)
