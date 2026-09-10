from __future__ import annotations

from pathlib import Path

from tex2sto.dialect import load_project
from tex2sto.model import build_numbering
from tex2sto.transform import TABLE_BREAK_MARKER, renderer_body

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "master-thesis" / "main.tex"


def test_pdf_longtable_has_automatic_continuation_header() -> None:
    project = load_project(EXAMPLE)
    source = renderer_body(project, build_numbering(project), target="pdf")

    assert "\\endfirsthead" in source
    assert "\\endhead" in source
    assert "Продолжение таблицы 2" in source
    assert "\\tablebreak" not in source


def test_docx_longtable_exposes_explicit_split_marker() -> None:
    project = load_project(EXAMPLE)
    source = renderer_body(project, build_numbering(project), target="docx")

    assert source.count(TABLE_BREAK_MARKER) == 2
    assert "\\tablebreak" not in source


def test_sections_start_new_pages_and_bibliography_has_no_number_period() -> None:
    project = load_project(EXAMPLE)
    source = renderer_body(project, build_numbering(project), target="pdf")

    assert "TEX2STO_PAGE_BREAK\n\n\\section{Анализ требований}" in source
    assert "\n\n1 СТО 02068410" in source
    assert "\n\n1. СТО 02068410" not in source
    assert "\\begin{figure}[H]" in source
