"""Phase 1: PDF 텍스트 추출 — 선택적 Unstructured 레이아웃 경로, PyPDF 폴백."""
from __future__ import annotations

from pathlib import Path


def load_pdf_text_from_bytes(data: bytes) -> tuple[str, str]:
    """
    Returns:
        (plain_text, extractor): extractor는 ``unstructured`` 또는 ``pypdf``.
    """
    import tempfile

    from langchain_community.document_loaders import PyPDFLoader

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(data)
        path = tmp.name
    try:
        try:
            from unstructured.partition.pdf import partition_pdf

            elements = partition_pdf(
                filename=path,
                strategy="fast",
                infer_table_structure=False,
            )
            parts: list[str] = []
            for el in elements:
                t = getattr(el, "text", None) or str(el)
                if t and str(t).strip():
                    parts.append(str(t).strip())
            blob = "\n\n".join(parts).strip()
            if len(blob) >= 40:
                return blob, "unstructured"
        except ImportError:
            pass
        except Exception:
            pass

        loader = PyPDFLoader(path)
        docs = loader.load()
        text = "\n\n".join(d.page_content for d in docs)
        return text, "pypdf"
    finally:
        Path(path).unlink(missing_ok=True)
