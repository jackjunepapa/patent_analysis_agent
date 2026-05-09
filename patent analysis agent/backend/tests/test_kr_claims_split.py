from __future__ import annotations

from patent_parse import (
    _extract_claim_one_kr,
    _kr_claims_section_loose,
    parse_patent_document,
    split_claims_and_body,
)


def test_kr_claims_section_tokhye_scope_bracket():
    raw = (
        "【 발명의 명칭 】액정 패널\n\n"
        "【 특허청구의 범위 】\n"
        "제1항  액정 패널에 있어서, 게이트 라인과 데이터 라인을 포함하는 것을 특징으로 하는 액정 패널.\n"
        "제2항  제1항에 있어서, 상기 보상 드레인 전극은 금속인 것을 특징으로 하는 액정 패널.\n"
        "【 요약 】요약 본문.\n"
    )
    claims, _ = split_claims_and_body(raw, "KR")
    assert "제1항" in claims
    assert "게이트 라인" in claims
    c1 = _extract_claim_one_kr(claims)
    assert c1
    assert "게이트 라인" in c1
    assert "제1항에 있어서" not in c1[:40]


def test_kr_skips_deleted_claim_one_picks_next_independent():
    claims = (
        "제1항  (삭제)\n"
        "제2항  액정 패널에 있어서, 서브픽셀을 포함하는 것을 특징으로 하는 액정 패널.\n"
        "제3항  제2항에 있어서, 상기 서브픽셀은 발광 소자를 포함하는 것을 특징으로 하는 액정 패널.\n"
    )
    out = _extract_claim_one_kr(claims)
    assert out
    assert "제2항" in out or "서브픽셀" in out
    assert "(삭제)" not in out


def test_kr_loose_section_without_corner_brackets():
    raw = (
        "명세서 본문\n" * 30
        + "\n특허청구의 범위\n"
        "제1항  제조 방법에 있어서, 기판 위에 게이트 전극을 형성하는 단계를 포함하는 것을 특징으로 하는 제조 방법.\n"
        "제2항  제1항에 있어서, 상기 게이트 전극은 Mo로 형성되는 것을 특징으로 하는 제조 방법.\n"
    )
    sec = _kr_claims_section_loose(raw)
    assert len(sec) > 60
    assert "게이트 전극" in sec


def test_parse_kr_document_extracts_claim_one():
    raw = (
        "【 도면의 간단한 설명 】\nFIG.1\n\n"
        "【 특허청구의 범위 】\n"
        "제1항  액정 표시 장치에 있어서, 액정층을 포함하는 것을 특징으로 하는 액정 표시 장치.\n"
        "제2항  제1항에 있어서, 상기 액정층은 VA 모드인 것을 특징으로 하는 액정 표시 장치.\n"
    )
    p = parse_patent_document(raw, "KR", "KR10-test.pdf")
    assert p.invention_claim_one
    assert "액정층" in p.invention_claim_one
