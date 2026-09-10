from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from tex2sto.build import BuildOptions, build_project
from tex2sto.dialect import load_project

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "master-thesis" / "main.tex"


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_docx_is_editable_and_profiled(tmp_path: Path) -> None:
    project = load_project(EXAMPLE)

    (docx_path,) = build_project(project, BuildOptions(output_dir=tmp_path))

    with ZipFile(docx_path) as package:
        document = package.read("word/document.xml").decode()
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
        page_size = document.split("<w:pgSz", 1)[1].split("/>", 1)[0]
        assert 'w:w="11906"' in page_size
        assert 'w:h="16838"' in page_size
        assert "Tex2Sto Structural Heading" in styles
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
