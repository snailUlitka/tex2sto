from __future__ import annotations

from pathlib import Path

from tex2sto.dialect import load_project
from tex2sto.model import BibliographyItem, build_numbering
from tex2sto.profiles.ssau.bibliography import format_source
from tex2sto.transform import (
    APPENDIX_TITLE_MARKER,
    STRUCTURAL_HEADING_MARKER,
    TABLE_BREAK_MARKER,
    renderer_body,
)

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

    assert source.count("Определения, обозначения и сокращения") == 1
    assert "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ" not in source
    assert "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ" not in source
    assert "TEX2STO_SYMBOLS где $Q$ - доля пройденных проверок;" in source
    assert "$N_{passed}$ - число успешных проверок;" in source
    assert "$N_{total}$ - общее число проверок." in source
    assert rf"\section*{{{STRUCTURAL_HEADING_MARKER} Приложение А}}" in source
    assert rf"\section*{{{APPENDIX_TITLE_MARKER} Пример программного кода}}" in source


def test_pdf_symbol_indentation_is_scoped_to_the_explanation() -> None:
    project = load_project(EXAMPLE)
    source = renderer_body(project, build_numbering(project), target="pdf")

    assert r"{\par\hangindent=12.5mm\hangafter=1\noindent где $Q$" in source
    assert r"$N_{total}$ - общее число проверок.\par}" in source


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

    assert format_source(item) == (
        "Иванов И. И.; Петров П. П. «Методы контроля» [Текст]/"
        "И. И. Иванов, П. П. Петров//Журнал «Контроль» - 2025 - № 4 - С. 3–9."
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
        rendered = format_source(BibliographyItem(key=kind, kind=kind, title="Название", **fields))
        assert rendered.endswith(".")
        assert " - " in rendered
    assert "- 576 с." in format_source(
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


def test_bibliography_preserves_standard_identifiers() -> None:
    item = BibliographyItem(
        key="sto",
        kind="standard",
        title="СТО 02068410-004-2018",
        details="Самара: Университет, 2019. 37 с.",
    )
    rendered = format_source(item)
    assert "СТО 02068410-004-2018" in rendered
    assert format_source(item, nir_master=True) == rendered


def test_nir_master_article_keeps_volume_article_number_and_online_details() -> None:
    article = BibliographyItem(
        key="article",
        kind="article",
        authors="Rakhshankhah N.; Abbaszadeh M.; Kazemi A. et al.",
        title="Назначение метода: сравнение подходов",
        container="BMC Musculoskeletal Disorders. Vol. 25",
        year="2024",
        pages="Article 547",
        url=r"https\://doi.org/10.1186/s12891-024-07669-7",
        access_date="11.11.2026",
    )
    assert format_source(article, nir_master=True) == (
        "Rakhshankhah, N. Назначение метода: сравнение подходов [Текст] / "
        "N. Rakhshankhah, M. Abbaszadeh, A. Kazemi et al. // "
        "BMC Musculoskeletal Disorders. - 2024. - Vol. 25. - Article 547. - "
        r"URL: \url{https://doi.org/10.1186/s12891-024-07669-7} (дата обращения: 11.11.2026)."
    )
