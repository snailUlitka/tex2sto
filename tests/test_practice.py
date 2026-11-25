from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile

import pytest
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

from tex2sto.build import BuildOptions, build_project
from tex2sto.dialect import load_project
from tex2sto.dialect.practice import parse_practice_assignment, parse_practice_title
from tex2sto.errors import SourceError
from tex2sto.profiles.ssau.practice import latex_front_matter, nir_master_abstract_counts
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


def test_practice_assignment_preserves_paragraphs_in_each_cell() -> None:
    assignment = parse_practice_assignment(
        (
            "Компетенция\n% comment\nи показатель\n \nСледующий показатель",
            "Знать~методы.\n\nУметь выбирать.\n\nВладеть навыками.",
            "Первое задание \\& результат.\n\n\nВторое задание.",
        )
    )

    assert assignment.competency == ("Компетенция и показатель", "Следующий показатель")
    assert assignment.outcomes == ("Знать\u00a0методы.", "Уметь выбирать.", "Владеть навыками.")
    assert assignment.task == ("Первое задание & результат.", "Второе задание.")


@pytest.mark.parametrize("outcomes", ("\n% comment\n", "Знать.\n\n\\textbf{Уметь}"))
def test_practice_assignment_rejects_empty_cells_or_markup(outcomes: str) -> None:
    with pytest.raises(SourceError):
        parse_practice_assignment(("Компетенция", outcomes, "Задание"))


def test_practice_preview_lowers_outcomes_as_paragraphs() -> None:
    source = latex_front_matter(load_project(EXAMPLE).metadata)
    assert r"Знать: методы исследования.\par Уметь: выбирать методы исследования." in source
    assert r"\par Владеть: навыками анализа." in source


@pytest.mark.parametrize(
    ("counts", "text"),
    [
        ((10, 4, 15, 1), "10 рисунков, 4 таблицы, 15 источников, 1 приложение."),
        ((21, 11, 3, 12), "21 рисунок, 11 таблиц, 3 источника, 12 приложений."),
        ((2, 1, 111, 24), "2 рисунка, 1 таблица, 111 источников, 24 приложения."),
    ],
)
def test_nir_master_abstract_uses_full_inflected_nouns(counts, text: str) -> None:
    assert nir_master_abstract_counts(*counts) == text


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
    assert "Работа: 0 с., 0 рис., 0 табл., 1 источник(ов), 0 прил." in texts
    assert document.settings.element.xpath("w:updateFields/@w:val") == ["true"]
    assert all("TEX2STO_" not in text for text in texts)
    assert len(document.element.xpath('.//w:br[@w:type="page"]')) >= 12
    assert texts.index("Заключение") < texts.index("Определения, обозначения и сокращения")
    fields = document.element.body.xpath('.//w:instrText[starts-with(normalize-space(.), "TOC ")]')
    assert len(fields) == 1
    assert len(document.tables[0].rows) == 7
    assert document.tables[0].rows[0]._tr.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None
    assert document.tables[0].cell(1, 1).paragraphs[0].paragraph_format.line_spacing == 1.0
    assert len(document.tables[0].cell(1, 1).paragraphs) == 3
    assert "Самара 2026" in document.sections[0].first_page_footer.paragraphs[0].text
    for style in ("Tex2Sto Heading 1", "Tex2Sto Heading 2", "Tex2Sto Abstract Keywords"):
        assert document.styles[style].paragraph_format.first_line_indent.twips == 709
    with ZipFile(output) as package:
        assert "PAGE" in package.read("word/footer1.xml").decode()


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_nir_master_docx_matches_forms(tmp_path: Path) -> None:
    config = tmp_path / "nir-master.toml"
    config.write_text(
        '[layout]\npractice_template = "nir-master"\n'
        '[structure]\nterminology_position = "after-conclusion"\n',
        encoding="utf-8",
    )
    project = load_project(EXAMPLE, config=config)
    details = "доцент кафедры информационных систем и технологий, кандидат технических наук"
    project.metadata.supervisor_details = details
    assert validate_project(project).items == ()

    (output,) = build_project(project, BuildOptions(output_dir=tmp_path))
    document = Document(output)
    paragraphs = document.paragraphs
    texts = [p.text for p in paragraphs]
    institution = paragraphs[texts.index("РОССИЙСКОЙ ФЕДЕРАЦИИ")]
    assert institution.style.base_style.font.size.pt == 14
    assert institution.style.paragraph_format.line_spacing == 1.0
    assert institution.style.base_style.paragraph_format.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert paragraphs[texts.index("ОТЧЕТ ПО ПРАКТИКЕ")].runs[0].bold is True
    for field, explainer in (
        ("Вид практики ", "(учебная, производственная)"),
        ("Тип практики ", "(в соответствии с ОПОП ВО)"),
    ):
        index = next(i for i, text in enumerate(texts) if text.startswith(field))
        assert paragraphs[index].runs[-1].underline is True
        assert texts[index + 1] == explainer
    assert "(в соответствии с календарным учебным графиком)" in texts
    assert "(уровень магистратуры)" in texts
    assert texts.index("Самара 2026") == texts.index("Оценка ____________") + 1
    assert not document.sections[0].first_page_footer.paragraphs[0].text

    assignment = next(p for p in paragraphs if p.text.startswith("Задание(я) для выполнения"))
    assert assignment.runs[0].bold is True
    assert assignment.text.endswith("проведение исследований)")
    assert "Студенту группы 6101-090401D" in texts
    assert "Иванову Ивану Ивановичу" in texts
    assert "от 30.09.2026 г. № 100-ПР" in texts
    assert texts.count("Руководитель практики,") == 2
    signatures = [text for text in texts if text.startswith(details)]
    assert len(signatures) == 2
    assert all("\t______________\u00a0Петров\u00a0П.\u00a0П." in text for text in signatures)
    assert texts.count("(подпись)") == 2
    abstract = texts.index("РЕФЕРАТ")
    assert paragraphs[abstract].paragraph_format.page_break_before is True
    stats = paragraphs[abstract + 1]
    assert stats.text == "Отчет … с., 0 рисунков, 0 таблиц, 1 источник, 0 приложений."
    assert stats._p.xpath("w:r/w:instrText/text()") == [" NUMPAGES "]
    assert stats._p.xpath("w:r/w:fldChar/@w:fldCharType") == ["begin", "separate", "end"]
    assert document.settings.element.xpath("w:updateFields/@w:val") == ["false"]

    table = document.tables[0]
    widths = [column.width.twips for column in table.columns]
    assert widths == [2374, 3630, 3351]
    assert not table.autofit
    assert table.cell(0, 0).text == (
        "Планируемые результаты освоения образовательной программы (компетенции)"
    )
    assert table.rows[0]._tr.xpath("w:trPr/w:tblHeader")
    assert all(c.paragraphs[0].alignment == WD_ALIGN_PARAGRAPH.CENTER for c in table.rows[0].cells)
    for row in table.rows:
        assert [cell.width.twips for cell in row.cells] == widths
    outcomes = table.cell(1, 1).paragraphs
    assert [p.text.split(":")[0] for p in outcomes] == ["Знать", "Уметь", "Владеть"]
    assert all(p.paragraph_format.line_spacing == 1.0 for p in outcomes)
    fields = document.element.body.xpath('.//w:instrText[starts-with(normalize-space(.), "TOC ")]')
    assert len(fields) == 1


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


@pytest.mark.parametrize("operator", ["*", r"\cdot", "·", "⋅", "∙"])
def test_multiplication_warning_ignores_verbatim(project_dir: Path, operator: str) -> None:
    project = load_project(project_dir / "main.tex")
    project.expanded_source += rf"\begin{{verbatim}}$a {operator} b$\end{{verbatim}}"
    assert "T2S-W401" not in {item.code for item in validate_project(project).items}
    project.expanded_source += rf"\begin{{equation*}}a {operator} b\end{{equation*}}"
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
