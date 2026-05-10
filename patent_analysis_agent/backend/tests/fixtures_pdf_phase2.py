"""US 스타일 특허 텍스트를 담은 소형 PDF 바이트 (fpdf2)."""
from __future__ import annotations

import pytest

try:
    from fpdf import FPDF
except ImportError:  # pragma: no cover
    FPDF = None  # type: ignore[misc, assignment]


def fpdf_available() -> bool:
    return FPDF is not None


def _pdf_from_plaintext(body: str) -> bytes:
    if FPDF is None:
        raise RuntimeError("fpdf2 required: pip install fpdf2")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", size=8)
    pdf.multi_cell(0, 3.6, body)
    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    if isinstance(out, str):
        return out.encode("latin-1", errors="replace")
    return bytes(out)


def invention_us_patent_pdf_bytes() -> bytes:
    """본 발명: Claim 1 + [0045] 명세 + 고유 마커."""
    text = """TITLE OF INVENTION
Voltage Compensation Device

ABSTRACT
A display voltage compensation device.

CLAIMS
1. A voltage compensation device comprising:
a housing;
a compensation capacitor as reference numeral 200;
wherein the capacitor 200 reduces image retention on a display panel;
wherein the compensation comprises applying a bias voltage.

DETAILED DESCRIPTION OF THE INVENTION
[0045] In one embodiment, the capacitor 200 is coupled between the gate line and the reference voltage as shown in FIG. 2. The voltage compensation effects reduce afterimages on the panel. PHASE2INV99MARK
[0046] Further embodiments are described below.
"""
    return _pdf_from_plaintext(text)


def prior_us_patent_pdf_bytes() -> bytes:
    """선행: 동일 기술 용어·[0045]·고유 마커로 검색·매핑 정확도 검증용."""
    text = """TITLE OF INVENTION
Prior Display Module

ABSTRACT
Prior art display housing.

CLAIMS
1. A display module comprising:
a housing;
wherein the housing supports a bezel.

DETAILED DESCRIPTION OF THE INVENTION
[0045] The prior art teaches PRIORUNIQUE998MARK and discusses capacitor 200 placement in related embodiments for voltage compensation on a display panel.
[0046] Other variants are known.
"""
    return _pdf_from_plaintext(text)


def require_fpdf() -> None:
    if FPDF is None:
        pytest.skip("fpdf2 not installed (pip install fpdf2)")
