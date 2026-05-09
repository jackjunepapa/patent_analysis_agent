"""Phase 1: PDF 로더 (PyPDF 필수 경로, Unstructured 선택)."""
from __future__ import annotations

from io import BytesIO

from pypdf import PdfWriter

from patent_pdf_load import load_pdf_text_from_bytes


def _minimal_pdf_bytes() -> bytes:
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    buf = BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_load_pdf_text_from_bytes_uses_pypdf_or_unstructured() -> None:
    data = _minimal_pdf_bytes()
    text, label = load_pdf_text_from_bytes(data)
    assert label in ("pypdf", "unstructured")
    assert isinstance(text, str)
