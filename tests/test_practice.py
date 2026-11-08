from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document
from docx.oxml.ns import qn

from tex2sto.build import BuildOptions, build_project
from tex2sto.dialect import load_project
from tex2sto.dialect.practice import parse_practice_title
from tex2sto.errors import SourceError
from tex2sto.validation import validate_project

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/practice-report/main.tex"
FIELDS = (
    "kind={учебная},type={технологическая},start={2026-10-01},end={2026-11-30},"
    "order-date={2026-09-30},order-number={100},organization={Кафедра},"
    "author-dative={Иванову И. И.}"
)


def test_practice_example_passes_strict_validation() -> None:
    assert validate_project(load_project(EXAMPLE)).items == ()


@pytest.mark.parametrize(
    "fields",
    [
        FIELDS.replace("kind={учебная},", ""),
        FIELDS + ",unknown={x}",
        FIELDS + ",kind={x}",
        FIELDS.replace("end={2026-11-30}", "end={2026-09-30}"),
        FIELDS.replace("2026-10-01", "01.10.2026"),
        FIELDS.replace("2026-10-01", "2026-02-30"),
        FIELDS.replace("Кафедра", r"\textbf{Кафедра}"),
        FIELDS + ",grade={}",
    ],
)
def test_reject_invalid_practice_fields(fields: str) -> None:
    with pytest.raises(SourceError):
        parse_practice_title(fields)


def test_practice_placement_and_multiplicity(project_dir: Path) -> None:
    source = (project_dir / "main.tex").read_text()
    declaration = "\\practicetitle{" + FIELDS + "}\n"
    for invalid in [
        source.replace("\\conclusion", declaration + "\\conclusion"),
        declaration + source,
        source.replace("\\begin{document}", declaration * 2 + "\\begin{document}"),
        source.replace("\\begin{document}", "\\practiceassignment{a}{b}{c}\\begin{document}"),
    ]:
        (project_dir / "main.tex").write_text(invalid)
        with pytest.raises(SourceError):
            load_project(project_dir / "main.tex")


def test_practice_requires_assignment_rows() -> None:
    project = load_project(EXAMPLE)
    project.metadata.practice_assignments.clear()
    assert "T2S-E206" in {item.code for item in validate_project(project).items}


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_practice_docx_front_matter_and_configured_styles(tmp_path: Path) -> None:
    project = load_project(EXAMPLE)
    (output,) = build_project(project, BuildOptions(output_dir=tmp_path))
    document = Document(output)
    texts = [p.text for p in document.paragraphs]
    assert "ОТЧЕТ ПО ПРАКТИКЕ" in texts
    assert not any("ВЫПУСКНАЯ" in text or "Нормоконтролер" in text for text in texts)
    assert any("Иванову Ивану Ивановичу" in text for text in texts)
    assert any("30.09.2026 № 100-ПР" in text for text in texts)
    assert any("01.10.2026 по 30.11.2026" in text for text in texts)
    assert "РЕФЕРАТ" in texts and "СОДЕРЖАНИЕ" in texts
    assert all("TEX2STO_" not in text for text in texts)
    assert len(document.element.xpath('.//w:br[@w:type="page"]')) >= 12
    assert texts.index("ЗАКЛЮЧЕНИЕ") < texts.index("ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ")
    assert len(document.tables[0].rows) == 7
    assert document.tables[0].rows[0]._tr.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None
    assert document.tables[0].cell(1, 1).paragraphs[0].paragraph_format.line_spacing == 1.0
    assert "Самара 2026" in document.sections[0].first_page_footer.paragraphs[0].text
    for style in ("Tex2Sto Heading 1", "Tex2Sto Heading 2", "Tex2Sto Abstract Keywords"):
        assert document.styles[style].paragraph_format.first_line_indent.twips == 709
    with ZipFile(output) as package:
        assert "PAGE" in package.read("word/footer1.xml").decode()


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_unnumbered_equations_do_not_consume_numbers(project_dir: Path, tmp_path: Path) -> None:
    project = load_project(project_dir / "main.tex")
    project.body = project.body.replace(
        "Уравнение",
        r"""
\begin{equation*}a=b\end{equation*}
\begin{symbols}\symbol{$a$}{показатель}\end{symbols}
Уравнение""",
    )
    assert not validate_project(project).has_errors
    (output,) = build_project(project, BuildOptions(output_dir=tmp_path / "equations"))
    with ZipFile(output) as package:
        xml = package.read("word/document.xml").decode()
        assert xml.count("<m:oMath>") >= 2
        assert xml.count("<w:t>(1)</w:t>") == 1
        assert "TEX2STO_EQ_NUMBER" not in xml
    project.body = project.body.replace("Уравнение~\\ref{eq:model} задаёт модель.", "")
    project.body += r"\ref{eq:model}"
    assert "T2S-E428" in {item.code for item in validate_project(project).items}


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_configurable_separators_and_table_spacing(tmp_path: Path) -> None:
    project = load_project(ROOT / "examples/master-thesis/main.tex")
    project.settings = replace(
        project.settings,
        separator="em-dash",
        allow_em_dash=True,
        table_line_spacing=1.0,
        list_numbering="decimal",
    )
    (output,) = build_project(project, BuildOptions(output_dir=tmp_path))
    document = Document(output)
    assert document.styles["Tex2Sto Table Text"].paragraph_format.line_spacing == 1.0
    assert any("Рисунок 1 — " in p.text for p in document.paragraphs)
    with ZipFile(output) as package:
        xml = package.read("word/numbering.xml").decode()
        assert 'w:val="russianLower"' not in xml
        body = package.read("word/document.xml").decode()
        assert 'w:bottom w:val="nil"' in body


def test_unnumbered_equations_cannot_be_referenced(project_dir: Path) -> None:
    project = load_project(project_dir / "main.tex")
    project.body = project.body.replace(r"\begin{equation}", r"\begin{equation*}").replace(
        r"\end{equation}", r"\end{equation*}"
    )
    assert "T2S-E429" in {item.code for item in validate_project(project).items}


def test_multiplication_warning_ignores_verbatim(project_dir: Path) -> None:
    project = load_project(project_dir / "main.tex")
    project.body += r"\begin{verbatim}$a*b$\end{verbatim}"
    assert "T2S-W401" not in {item.code for item in validate_project(project).items}
    project.body += r"\begin{equation*}a*b\end{equation*}"
    assert "T2S-W401" in {item.code for item in validate_project(project).items}


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_multiline_equation_preserves_all_rows(project_dir: Path, tmp_path: Path) -> None:
    project = load_project(project_dir / "main.tex")
    project.body = project.body.replace(
        "\\begin{equation}\nx = y + 1\n\\label{eq:model}\n\\end{equation}",
        "\\begin{align}\nx &= y + 1 \\\\\nz &= x + 2\n\\label{eq:model}\n\\end{align}",
    )
    assert not validate_project(project).has_errors
    (output,) = build_project(project, BuildOptions(output_dir=tmp_path / "multiline"))
    with ZipFile(output) as package:
        xml = package.read("word/document.xml").decode()
        assert "<m:eqArr>" in xml
        assert ">z<" in xml
        assert xml.count("<w:t>(1)</w:t>") == 1
        assert "TEX2STO_" not in xml
