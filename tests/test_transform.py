from __future__ import annotations

from pathlib import Path

from tex2sto.dialect import load_project
from tex2sto.model import BibliographyItem, build_numbering
from tex2sto.transform import TABLE_BREAK_MARKER, _format_source, renderer_body

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


def test_docx_combines_terminology_and_formats_symbols_and_appendix() -> None:
    project = load_project(EXAMPLE)
    source = renderer_body(project, build_numbering(project), target="docx")

    assert source.count("ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ") == 1
    assert "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" not in source
    assert "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" not in source
    assert "TEX2STO_SYMBOLS где $Q$ --- доля пройденных проверок," in source
    assert "$N_{passed}$ --- число успешных проверок," in source
    assert "$N_{total}$ --- общее число проверок." in source
    assert r"\section*{ПРИЛОЖЕНИЕ А\\Пример программного кода}" in source


def test_structured_bibliography_uses_normalized_compact_separators() -> None:
    item = BibliographyItem(
        key="article",
        kind="article",
        authors="Иванов И. И.; Петров П. П.",
        title='"Методы контроля"',
        contributors="И. И. Иванов, П. П. Петров",
        container='Журнал "Контроль"',
        year="2025",
        issue="4",
        pages="3-9",
    )

    assert _format_source(item) == (
        "Иванов И. И.; Петров П. П. «Методы контроля» [Текст]/"
        "И. И. Иванов, П. П. Петров//Журнал «Контроль» — 2025 — № 4 — С. 3–9."
    )


def test_structured_bibliography_supports_all_acceptance_kinds() -> None:
    fixtures = {
        "web": {"url": "https://example.org", "access_date": "01.09.2026"},
        "legal": {"url": "https://example.org/law", "access_date": "01.09.2026"},
        "book": {
            "place": "Самара",
            "publisher": "Университет",
            "year": "2025",
            "pages": "576",
        },
        "chapter": {
            "container": "Сборник",
            "publisher": "Университет",
            "year": "2025",
            "pages": "10-20",
        },
        "conference": {"container": "Труды конференции", "year": "2025", "pages": "1-8"},
        "dataset": {
            "publisher": "Репозиторий",
            "year": "2025",
            "url": "https://example.org/data",
            "access_date": "01.09.2026",
        },
        "preprint": {
            "container": "arXiv",
            "year": "2025",
            "url": "https://example.org/preprint",
            "access_date": "01.09.2026",
        },
    }

    for kind, fields in fixtures.items():
        rendered = _format_source(
            BibliographyItem(key=kind, kind=kind, title="Название", **fields)
        )
        assert rendered.endswith(".")
        assert " — " in rendered
    assert "— 576 с." in _format_source(
        BibliographyItem(
            key="book",
            kind="book",
            title="Книга",
            place="Самара",
            publisher="Университет",
            year="2025",
            pages="576",
        )
    )
