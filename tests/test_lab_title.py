from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn

from tex2sto.build import BuildOptions, build_project
from tex2sto.dialect import load_project
from tex2sto.errors import SourceError
from tex2sto.model import build_numbering
from tex2sto.renderers.pdf import _document_source
from tex2sto.validation import validate_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "lab-report" / "main.tex"


@pytest.fixture
def lab_source() -> str:
    return EXAMPLE.read_text(encoding="utf-8")


def _project(tmp_path: Path, source: str):
    master = tmp_path / "main.tex"
    master.write_text(source, encoding="utf-8")
    return load_project(master)


def test_lab_title_replaces_thesis_metadata(tmp_path: Path, lab_source: str) -> None:
    project = _project(tmp_path, lab_source)

    title = project.metadata.lab_title
    assert title is not None
    assert title.number == "3"
    assert title.variant == "17"
    assert title.group == "6402-090301D"
    assert title.author_label == "Выполнил"
    assert title.reviewer_label == "Проверила"
    assert title.city == "Самара"
    assert "\\labtitle" not in project.body
    assert not validate_project(project).items


def test_minimal_lab_title_and_plain_text(tmp_path: Path, lab_source: str) -> None:
    source = (
        lab_source.replace("  variant={17},\n", "")
        .replace("  reviewer-label={Проверила},\n", "")
        .replace(
            "course={Моделирование информационно-вычислительных систем}",
            r"course={Теория, практика \& анализ: 100\% \{данных\} A_B #1}",
        )
        .replace("author={Иванов И. И.}", "author={Иванов~И.~И.}")
    )
    source = source.replace("number={3},", "number={3}, % ignored } , \\unknown\n")
    project = _project(tmp_path, source)

    title = project.metadata.lab_title
    assert title is not None
    assert title.variant == ""
    assert title.reviewer_label == "Проверил"
    assert title.author == "Иванов\u00a0И.\u00a0И."
    assert title.course == "Теория, практика & анализ: 100% {данных} A_B #1"
    assert not validate_project(project).items
    preview = _document_source(project, build_numbering(project))
    assert r"100\% \{данных\} A\_B \#1" in preview
    assert r"\texabstract" not in preview
    assert r"\tableofcontents" not in preview
    assert "ВЫПУСКНАЯ" not in preview


@pytest.mark.parametrize(
    ("before", "after", "message"),
    [
        ("number={3},", "number={3}, typo={value},", "unknown labtitle fields: typo"),
        ("number={3},", "number={3}, number={4},", "duplicate named argument: number"),
        ("number={3},", "", "required labtitle fields are missing: number"),
        ("number={3},", "number={},", "must not be empty: number"),
        ("number={3},", "number={0},", "number must be a positive integer"),
        ("year={2026}", "year={26}", "year must contain four digits"),
        ("number={3},", "number=3,", "expected '\\{'"),
        ("number={3},", "number={3}", "expected a comma"),
        ("number={3},", "number={3},,", "expected a named argument"),
        ("variant={17}", "variant={}", "must not be empty: variant"),
        ("author={Иванов И. И.}", r"author={\textbf{Иванов}}", "plain text"),
        ("author={Иванов И. И.}", "author={{Иванов}}", "do not accept groups"),
        ("author={Иванов И. И.}", "author={$x$}", "mathematical markup"),
        ("number={3},", "number={3}, author-label={   },", "must not be empty: author-label"),
    ],
)
def test_rejects_invalid_lab_title_fields(
    tmp_path: Path, lab_source: str, before: str, after: str, message: str
) -> None:
    with pytest.raises(SourceError, match=message):
        _project(tmp_path, lab_source.replace(before, after))


@pytest.mark.parametrize(
    "declaration",
    [
        r"\title{Other}",
        r"\author{Name}",
        r"\year{2026}",
        r"\assignmentvariant{none}",
        r"\keywords{A;B;C;D;E}",
        r"\begin{abstract}Text\end{abstract}",
    ],
)
def test_rejects_mixed_front_matter(tmp_path: Path, lab_source: str, declaration: str) -> None:
    with pytest.raises(SourceError, match="cannot be combined"):
        _project(
            tmp_path, lab_source.replace(r"\begin{document}", declaration + r"\begin{document}")
        )


def test_rejects_duplicate_and_misplaced_lab_title(tmp_path: Path, lab_source: str) -> None:
    declaration = lab_source.split(r"\labtitle", 1)[1].split(r"\begin{document}", 1)[0]
    with pytest.raises(SourceError, match="may appear only once"):
        _project(tmp_path, lab_source + r"\labtitle" + declaration)
    with pytest.raises(SourceError, match="after documentclass and before document"):
        _project(
            tmp_path,
            lab_source.replace(r"\labtitle", r"\begin{document}\labtitle").replace(
                "\n\\begin{document}\n\\section", "\n\\section"
            ),
        )
    with pytest.raises(SourceError, match="after documentclass and before document"):
        _project(
            tmp_path,
            lab_source.replace(r"\documentclass{tex2sto}", "") + r"\documentclass{tex2sto}",
        )


def test_lab_structure_requires_section_and_orders_optional_elements(
    tmp_path: Path, lab_source: str
) -> None:
    missing = _project(tmp_path, lab_source.replace(r"\section{Задание}", ""))
    assert any(item.code == "T2S-E301" for item in validate_project(missing).items)
    for command in (r"\introduction", r"\conclusion"):
        source = lab_source.replace(
            r"\section{Задание}",
            r"\section{Задание}" + command
            if command == r"\introduction"
            else command + r"\section{Задание}",
        )
        assert any(
            item.code == "T2S-E302" for item in validate_project(_project(tmp_path, source)).items
        )
    valid = lab_source.replace(r"\section{Задание}", r"\introduction Text.\section{Задание}")
    valid = valid.replace(r"\end{document}", r"\conclusion Text.\end{document}")
    assert not validate_project(_project(tmp_path, valid)).items


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
@pytest.mark.parametrize("with_variant", [False, True])
def test_lab_docx_has_editable_cover_and_no_thesis_front_matter(
    tmp_path: Path, lab_source: str, with_variant: bool
) -> None:
    source = lab_source if with_variant else lab_source.replace("  variant={17},\n", "")
    project = _project(tmp_path, source)
    (output,) = build_project(project, BuildOptions(output_dir=tmp_path / "output"))
    document = Document(output)
    texts = [p.text for p in document.paragraphs]

    assert "Отчёт по лабораторной работе №\u00a03" in texts
    assert ("Вариант №\u00a017" in texts) is with_variant
    assert "Иванов И. И." in texts
    assert "гр. 6402-090301D" in texts
    assert "Петрова Е. В." in texts
    assert "Проверила:" in texts
    assert all(text not in texts for text in ("РЕФЕРАТ", "СОДЕРЖАНИЕ", "ЗАДАНИЕ"))
    assert "ВЫПУСКНАЯ КВАЛИФИКАЦИОННАЯ РАБОТА" not in texts
    first_body = next(p for p in document.paragraphs if p.style.name == "Tex2Sto Heading 1")
    assert first_body.paragraph_format.page_break_before
    cover = []
    for paragraph in document.paragraphs:
        if paragraph._p is first_body._p:
            break
        cover.append(paragraph)
    assert cover
    assert all(p.style.name.startswith("Tex2Sto Lab ") for p in cover)
    assert all(not p._p.xpath(".//w:br") for p in cover)
    assert all(not p._p.xpath(".//w:drawing | .//w:tbl") for p in cover)
    assert not document.element.body.xpath(".//w:instrText[contains(., 'PAGEREF')]")
    section = document.sections[0]
    assert section.different_first_page_header_footer
    footer = section.first_page_footer
    assert footer.paragraphs[0].text == "Самара 2026"
    assert not list(footer._element.iter(qn("w:instrText")))
    assert any("PAGE" in field.text for field in section.footer._element.iter(qn("w:instrText")))
    assert document.core_properties.author == "Иванов И. И."
