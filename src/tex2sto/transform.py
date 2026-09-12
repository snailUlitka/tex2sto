"""Normalize tex2sto semantics into conservative renderer input."""

from __future__ import annotations

import re
from collections.abc import Iterable

from tex2sto.dialect.syntax import find_command_calls, find_environment, replace_spans
from tex2sto.model import BibliographyItem, NumberingIndex, ObjectKind, SourceProject
from tex2sto.model.numbering import APPENDIX_LETTERS

PAGE_BREAK_MARKER = "TEX2STO_PAGE_BREAK"
TABLE_BREAK_MARKER = "TEX2STO_TABLE_BREAK"
SYMBOLS_MARKER = "TEX2STO_SYMBOLS"


def _object_number(index: NumberingIndex, label: str | None) -> str:
    return index.references.get(label or "", "?")


def _clean_commands(content: str, names: Iterable[tuple[str, int]]) -> str:
    replacements: list[tuple[int, int, str]] = []
    for name, arity in names:
        calls = find_command_calls(content, name, arity)
        replacements.extend((call.start, call.end, "") for call in calls)
    return replace_spans(content, replacements).strip()


def _label(content: str) -> str | None:
    calls = find_command_calls(content, "label", 1)
    return calls[0].args[0].strip() if calls else None


def _caption(content: str) -> str:
    calls = find_command_calls(content, "caption", 1)
    return calls[0].args[0].strip() if calls else ""


def _replace_objects(source: str, index: NumberingIndex, *, target: str) -> str:
    replacements: list[tuple[int, int, str]] = []
    specifications = (
        ("figure", ObjectKind.FIGURE, "Рисунок"),
        ("table", ObjectKind.TABLE, "Таблица"),
        ("longtable", ObjectKind.TABLE, "Таблица"),
    )
    for environment, _, prefix in specifications:
        for start, end, content in find_environment(source, environment):
            label = _label(content)
            number = _object_number(index, label)
            caption = _caption(content)
            command = "caption" if target == "docx" else "caption*"
            rendered_caption = f"{prefix} {number} --- {caption}"
            content_replacements = [
                (call.start, call.end, f"\\{command}{{{rendered_caption}}}")
                for call in find_command_calls(content, "caption", 1)
            ]
            content_replacements.extend(
                (call.start, call.end, "") for call in find_command_calls(content, "label", 1)
            )
            if environment == "longtable":
                table_heads = find_command_calls(content, "tablehead", 1)
                for call in table_heads:
                    cells = call.args[0].strip()
                    header = f"\\hline\n{cells} \\\\\n\\hline"
                    if target == "pdf":
                        header += (
                            "\n\\endfirsthead\n"
                            f"\\caption*{{Продолжение таблицы {number}}} \\\\\n"
                            f"\\hline\n{cells} \\\\\n\\hline\n\\endhead"
                        )
                    content_replacements.append((call.start, call.end, header))
                column_count = table_heads[0].args[0].count("&") + 1 if table_heads else 1
                for call in find_command_calls(content, "tablebreak", 0):
                    if target == "pdf":
                        replacement = ""
                    else:
                        replacement = " & ".join(
                            TABLE_BREAK_MARKER for _ in range(column_count)
                        ) + r" \\"
                    content_replacements.append((call.start, call.end, replacement))
            normalized = replace_spans(content, content_replacements)
            options = "[H]" if target == "pdf" and environment in {"figure", "table"} else ""
            rebuilt = (
                f"\\begin{{{environment}}}{options}{normalized}\\end{{{environment}}}"
            )
            replacements.append((start, end, rebuilt))

    for environment in ("equation", "align"):
        for start, end, content in find_environment(source, environment):
            label = _label(content)
            number = _object_number(index, label)
            cleaned = _clean_commands(content, (("label", 1),))
            rebuilt = (
                f"\\begin{{{environment}}}\n{cleaned}\n\\tag{{{number}}}\n\\end{{{environment}}}"
            )
            replacements.append((start, end, rebuilt))
    return replace_spans(source, replacements)


def _normalize_bibliography_text(value: str) -> str:
    normalized = value.strip()
    while '"' in normalized:
        normalized = normalized.replace('"', "«", 1)
        if '"' not in normalized:
            break
        normalized = normalized.replace('"', "»", 1)
    normalized = normalized.replace(" - ", " — ").replace(" – ", " — ")
    normalized = re.sub(r"(?<=\d)\s*[-—]\s*(?=\d)", "–", normalized)
    return normalized


def _source_medium(item: BibliographyItem) -> str:
    if item.medium:
        return item.medium.strip("[] ")
    if item.kind in {"dataset", "legal", "preprint", "web"}:
        return "Электронный ресурс"
    return "Текст"


def _format_structured_source(item: BibliographyItem) -> str:
    authors = _normalize_bibliography_text(item.authors).rstrip(". ")
    title = _normalize_bibliography_text(item.title).rstrip(". ")
    responsibility = _normalize_bibliography_text(item.contributors or item.authors).rstrip(". ")
    container = _normalize_bibliography_text(item.container).rstrip(". ")

    description = f"{title} [{_source_medium(item)}]"
    if responsibility:
        description += f"/{responsibility}"
    if container:
        description += f"//{container}"
    if authors:
        description = f"{authors}. {description}"

    publication = ""
    place = _normalize_bibliography_text(item.place).rstrip(". ")
    publisher = _normalize_bibliography_text(item.publisher).rstrip(". ")
    year = _normalize_bibliography_text(item.year).rstrip(". ")
    publication = f"{place}: {publisher}" if place and publisher else place or publisher
    if year:
        publication = f"{publication}, {year}" if publication else year

    parts = [description]
    if publication:
        parts.append(publication)
    if item.issue:
        issue = _normalize_bibliography_text(item.issue).strip()
        parts.append(issue if issue.startswith("№") else f"№ {issue}")
    if item.pages:
        pages = _normalize_bibliography_text(item.pages).strip().rstrip(".")
        if re.fullmatch(r"\d+–\d+", pages):
            pages = f"С. {pages}"
        elif pages.isdigit():
            pages = f"{pages} с."
        parts.append(pages)
    if item.url:
        parts.append(f"URL: {item.url.strip().rstrip('. ')}")
    if item.access_date:
        parts.append(f"(дата обращения: {item.access_date.strip()})")
    return " — ".join(parts).rstrip(". ") + "."


def _format_source(item: BibliographyItem) -> str:
    if not item.details:
        return _format_structured_source(item)
    title = _normalize_bibliography_text(item.title).rstrip(". ")
    if item.kind == "web" and "Электронный ресурс" not in title:
        title = f"{title} [Электронный ресурс]"
    parts = [
        _normalize_bibliography_text(part).rstrip(". ")
        for part in (item.authors, title, item.details)
        if part
    ]
    return ". ".join(parts) + "."


def _structural(title: str, *, target: str) -> str:
    if target == "pdf":
        return f"\\texstructural{{{title}}}"
    return f"\\section*{{{title}}}"


def _bibliography(project: SourceProject, index: NumberingIndex, *, target: str) -> str:
    by_key = {item.key: item for item in project.bibliography}
    ordered = sorted(index.citations, key=index.citations.get)
    ordered.extend(item.key for item in project.bibliography if item.key not in index.citations)
    lines = [
        f"{number} {_format_source(by_key[key])}" for number, key in enumerate(ordered, start=1)
    ]
    title = _structural("СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ", target=target)
    heading = f"{PAGE_BREAK_MARKER}\n\n{title}"
    return heading + "\n\n" + "\n\n".join(lines)


def _replace_semantic_commands(
    source: str,
    project: SourceProject,
    index: NumberingIndex,
    *,
    target: str,
) -> str:
    replacements: list[tuple[int, int, str]] = []
    headings = {
        "introduction": f"{PAGE_BREAK_MARKER}\n\n{_structural('ВВЕДЕНИЕ', target=target)}",
        "conclusion": f"{PAGE_BREAK_MARKER}\n\n{_structural('ЗАКЛЮЧЕНИЕ', target=target)}",
    }
    for command, replacement in headings.items():
        replacements.extend(
            (call.start, call.end, replacement) for call in find_command_calls(source, command, 0)
        )
    terminology_markers = sorted(
        (
            call.start,
            call.end,
        )
        for command in ("definitions", "abbreviations")
        for call in find_command_calls(source, command, 0)
    )
    for position, (start, end) in enumerate(terminology_markers):
        replacement = ""
        if position == 0:
            title = "ОПРЕДЕЛЕНИЯ, ОБОЗНАЧЕНИЯ И СОКРАЩЕНИЯ"
            replacement = f"{PAGE_BREAK_MARKER}\n\n{_structural(title, target=target)}"
        replacements.append((start, end, replacement))
    appendix_calls = find_command_calls(source, "appendix", 2)
    for appendix_number, call in enumerate(appendix_calls, start=1):
        label, title = (value.strip() for value in call.args)
        letter = index.references.get(label, APPENDIX_LETTERS[appendix_number - 1])
        if target == "pdf":
            appendix_heading = f"\\texappendix{{{letter}}}{{{title}}}"
        else:
            appendix_heading = f"\\section*{{ПРИЛОЖЕНИЕ {letter}\\\\{title}}}"
        replacement = f"{PAGE_BREAK_MARKER}\n\n{appendix_heading}"
        replacements.append((call.start, call.end, replacement))
    for call in find_command_calls(source, "definition", 2):
        term, description = call.args
        replacements.append((call.start, call.end, f"{term.strip()} --- {description.strip()}"))
    for start, end, content in find_environment(source, "symbols"):
        symbols = find_command_calls(content, "symbol", 2)
        lines = []
        for position, call in enumerate(symbols):
            symbol, explanation = (value.strip() for value in call.args)
            explanation = explanation.rstrip(" ,;.")
            prefix = "где " if position == 0 else ""
            ending = "." if position == len(symbols) - 1 else ","
            lines.append(f"{prefix}{symbol} --- {explanation}{ending}")
        separator = r"\\ " if target == "pdf" else r"\newline "
        rendered = separator.join(lines)
        rendered = (
            f"{SYMBOLS_MARKER} {rendered}" if target == "docx" else rf"\noindent {rendered}"
        )
        replacements.append((start, end, rendered))
    for call in find_command_calls(source, "printbibliography", 0):
        bibliography = _bibliography(project, index, target=target)
        replacements.append((call.start, call.end, bibliography))
    first_appendix = appendix_calls[0].start if appendix_calls else len(source)
    for call in find_command_calls(source, "section", 1):
        if call.start < first_appendix:
            replacement = f"{PAGE_BREAK_MARKER}\n\n\\section{{{call.args[0].strip()}}}"
            replacements.append((call.start, call.end, replacement))
    for appendix_number, appendix in enumerate(appendix_calls, start=1):
        start = appendix.end
        end = (
            appendix_calls[appendix_number].start
            if appendix_number < len(appendix_calls)
            else len(source)
        )
        letter = index.references.get(
            appendix.args[0].strip(), APPENDIX_LETTERS[appendix_number - 1]
        )
        section_number = 0
        subsection_number = 0
        subsubsection_number = 0
        heading_calls = sorted(
            (
                (call.start, command, call)
                for command in ("section", "subsection", "subsubsection")
                for call in find_command_calls(source, command, 1)
                if start <= call.start < end
            ),
            key=lambda item: item[0],
        )
        for _, command, call in heading_calls:
            if command == "section":
                section_number += 1
                subsection_number = 0
                subsubsection_number = 0
                display = f"{letter}.{section_number}"
            elif command == "subsection":
                subsection_number += 1
                subsubsection_number = 0
                display = f"{letter}.{section_number}.{subsection_number}"
            else:
                subsubsection_number += 1
                display = (
                    f"{letter}.{section_number}.{subsection_number}.{subsubsection_number}"
                )
            replacements.append(
                (call.start, call.end, f"\\{command}*{{{display}~{call.args[0].strip()}}}")
            )
    return replace_spans(source, replacements)


def _replace_references(source: str, index: NumberingIndex) -> str:
    replacements: list[tuple[int, int, str]] = []
    for call in find_command_calls(source, "ref", 1):
        label = call.args[0].strip()
        replacements.append((call.start, call.end, index.references.get(label, "?")))
    for call in find_command_calls(source, "cite", 1):
        numbers = [str(index.citations.get(key.strip(), "?")) for key in call.args[0].split(",")]
        replacements.append((call.start, call.end, f"[{', '.join(numbers)}]"))
    for call in find_command_calls(source, "label", 1):
        replacements.append((call.start, call.end, ""))
    return replace_spans(source, replacements)


def renderer_body(project: SourceProject, index: NumberingIndex, *, target: str) -> str:
    """Return validated LaTeX reduced to constructs accepted by a renderer."""
    source = _replace_objects(project.body, index, target=target)
    source = _replace_semantic_commands(source, project, index, target=target)
    return _replace_references(source, index).strip()
