"""Phase 1: 출원·공보 번호 추출."""
from __future__ import annotations

from patent_parse import extract_application_number, parse_patent_document


def test_extract_kr_dash_application_number() -> None:
    text = "출원번호 : 10-2023-0001234\n【발명의 명칭】 시험\n"
    assert extract_application_number(text, "KR") == "10-2023-0001234"


def test_extract_kr_publication_label() -> None:
    text = "공개번호：10-2022-0123456\n제1항. …"
    assert extract_application_number(text, "KR") == "10-2022-0123456"


def test_extract_us_publication_no() -> None:
    text = "Publication No. US 2022/0123456 A1\n\nAbstract\n"
    got = extract_application_number(text, "US")
    assert got is not None
    assert "2022" in got and "0123456" in got.replace(" ", "")


def test_parse_patent_document_sets_application_number() -> None:
    raw = (
        "출원번호: 10-2020-0099999\n"
        "【발명의 명칭】 예시\n"
        "【특허청구의 범위】\n"
        "제1항. 본 발명은 예시이다.\n"
    )
    p = parse_patent_document(raw, "KR", "x.txt")
    assert p.application_number == "10-2020-0099999"
