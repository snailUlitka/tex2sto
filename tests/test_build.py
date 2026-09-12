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
        assert "<w:t>?</w:t>" not in document
        assert "Определения, обозначения и сокращения" in document
        assert "<w:t>Введение</w:t>" in document
        assert "<w:t>Заключение</w:t>" in document
        assert "<w:t>Приложение А</w:t>" in document
        assert "Приложение А Пример программного кода" not in document
        assert "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" not in document
        assert "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" not in document
        assert "<w:bookmarkStart" in document
        assert "<m:oMath" in document
        assert "(1)" in document
        assert "Tex2StoEquation" in document
        assert 'w:val="Tex2StoFigureContent"' in document
        assert 'w:val="Tex2StoSymbols"' in document
        assert 'w:val="Tex2StoCode"' in document
        assert "где" in document
        assert "— доля пройденных проверок," in document
        assert "— общее число проверок." in document
        assert re.search(
            r"ПРИЛОЖЕНИЕ А</w:t>.*?<w:br/>.*?Пример программного кода</w:t>",
            document,
        )
        assert re.search(
            r"<w:t[^>]*>1</w:t></w:r><w:r>.*?<w:t[^>]*>\u00a0</w:t>",
            document,
        )
        assert "<w:tblHeader" in document
        assert "Продолжение таблицы 2" in document
        assert "TEX2STO_TABLE_BREAK" not in document
        assert " IF " not in document
        assert document.count("<w:tbl>") == 4
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        two_column_widths = [
            tuple(int(width) for width in re.findall(r'<w:gridCol w:w="(\d+)"', grid))
            for grid in grids
            if grid.count("<w:gridCol") == 2
        ]
        longtable_widths = two_column_widths[-2:]
        assert len(longtable_widths) == 2
        assert longtable_widths[0] == longtable_widths[1]
        assert longtable_widths[0][0] > longtable_widths[0][1]
        page_size = document.split("<w:pgSz", 1)[1].split("/>", 1)[0]
        assert 'w:w="11906"' in page_size
        assert 'w:h="16838"' in page_size
        assert "Tex2Sto Structural Heading" in styles
        assert 'w:val="russianLower"' in numbering
        assert 'w:val="-"' in numbering
        assert 'w:val="%2)"' in numbering
        assert 'w:suff w:val="nothing"' in numbering
        assert re.search(
            r"<w:numPr>.*?</w:numPr>.*?</w:pPr><w:r><w:t[^>]*>\u00a0</w:t>",
            document,
        )
        body_style = styles.split('w:styleId="Tex2StoBody"', 1)[1].split("</w:style>", 1)[0]
        assert 'w:firstLine="709"' in body_style
        structural_style = styles.split(
            'w:styleId="Tex2StoStructuralHeading"', 1
        )[1].split("</w:style>", 1)[0]
        assert '<w:jc w:val="center"' in structural_style
        assert '<w:b w:val="0"' in structural_style
        assert '<w:i w:val="0"' in structural_style
        continuation_style = styles.split(
            'w:styleId="Tex2StoTableContinuation"', 1
        )[1].split("</w:style>", 1)[0]
        assert '<w:jc w:val="left"' in continuation_style
        assert '<w:gridCol w:w="1701"/><w:gridCol w:w="5953"/><w:gridCol w:w="1701"/>' in document
        assert '<w:tblW w:type="dxa" w:w="9355"/>' in document
        assert re.search(r"<w:jc w:val=\"right\"/>.*?<w:t>\(1\)</w:t>", document)
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
