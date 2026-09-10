from __future__ import annotations

from pathlib import Path

from tex2sto.dialect import load_project
from tex2sto.model import build_numbering
from tex2sto.transform import renderer_body

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "master-thesis" / "main.tex"


def test_pdf_longtable_has_automatic_continuation_header() -> None:
    project = load_project(EXAMPLE)
    source = renderer_body(project, build_numbering(project), target="pdf")

    assert "\\endfirsthead" in source
    assert "\\endhead" in source
    assert "Продолжение таблицы 2" in source
