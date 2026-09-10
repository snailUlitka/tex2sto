from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from tex2sto.build import BuildOptions, build_project
from tex2sto.dialect import load_project

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "master-thesis" / "main.tex"
PDF_CLASS = ROOT / "src" / "tex2sto" / "profiles" / "ssau" / "latex" / "tex2sto-ssau.cls"


def test_pdf_profile_has_cyrillic_capable_times_fallback() -> None:
    profile = PDF_CLASS.read_text(encoding="utf-8")

    assert r"\IfFontExistsTF{Times New Roman}" in profile
    assert r"\setmainfont{Liberation Serif}" in profile


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_docx_is_editable_and_profiled(tmp_path: Path) -> None:
    project = load_project(EXAMPLE)

    (docx_path,) = build_project(project, BuildOptions(output_dir=tmp_path))

    with ZipFile(docx_path) as package:
        document = package.read("word/document.xml").decode()
        numbering = package.read("word/numbering.xml").decode()
        styles = package.read("word/styles.xml").decode()
        assert "Tex2StoHeading1" in document
        assert "Tex2StoTable" in document
        assert "NUMPAGES" in document
        assert "PAGEREF tex2sto_toc_" in document
        assert "<w:bookmarkStart" in document
        assert "<m:oMath" in document
        assert "(1)" in document
        assert "Tex2StoEquation" in document
        assert "<w:tblHeader" in document
        assert "Продолжение таблицы 2" in document
        assert "TEX2STO_TABLE_BREAK" not in document
        assert " IF " not in document
        assert document.count("<w:tbl>") == 3
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        longtable_widths = [
            tuple(int(width) for width in re.findall(r'<w:gridCol w:w="(\d+)"', grid))
            for grid in grids[1:]
        ]
        assert len(longtable_widths) == 2
        assert longtable_widths[0] == longtable_widths[1]
        assert longtable_widths[0][0] > longtable_widths[0][1]
        page_size = document.split("<w:pgSz", 1)[1].split("/>", 1)[0]
        assert 'w:w="11906"' in page_size
        assert 'w:h="16838"' in page_size
        assert "Tex2Sto Structural Heading" in styles
        assert 'w:val="russianLower"' in numbering
        assert 'w:val="\u2014"' in numbering
        assert any(name.startswith("word/media/") for name in package.namelist())


@pytest.mark.skipif(
    shutil.which("pandoc") is None or shutil.which("lualatex") is None,
    reason="Pandoc or LuaLaTeX is not installed",
)
def test_pdf_is_independently_built_as_a4(tmp_path: Path) -> None:
    project = load_project(EXAMPLE)

    outputs = build_project(project, BuildOptions(output_dir=tmp_path, pdf=True))
    pdf_path = outputs[1]
    info = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    pdf_text = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout

    assert pdf_path.read_bytes().startswith(b"%PDF-")
    assert "Page size:       595.276 x 841.89 pts (A4)" in info
    assert "РЕФЕРАТ" in pdf_text
    assert "ПРИЛОЖЕНИЕ А" in pdf_text
    assert "Продолжение таблицы 2" in pdf_text
