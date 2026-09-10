"""Pandoc-based editable DOCX renderer and narrow OOXML post-processing."""

from __future__ import annotations

import tempfile
import tomllib
from copy import deepcopy
from importlib.resources import files
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import RGBColor

from tex2sto.dialect.syntax import find_command_calls, find_environment
from tex2sto.model import NumberingIndex, ObjectKind, SourceProject
from tex2sto.renderers.docx_fields import (
    add_bookmark,
    add_field,
    repeat_table_row,
    set_update_fields,
)
from tex2sto.renderers.tools import require_tool, require_version, run_tool
from tex2sto.transform import PAGE_BREAK_MARKER, TABLE_BREAK_MARKER, renderer_body

PROFILE = files("tex2sto") / "profiles" / "ssau" / "pandoc"


def _pandoc() -> str:
    executable = require_tool("pandoc")
    configuration = tomllib.loads((PROFILE.parent / "toolchain.toml").read_text())
    require_version(
        [executable, "--version"],
        f"pandoc {configuration['pandoc']}",
        label="Pandoc",
    )
    return executable


def _move_before(element, anchor) -> None:
    anchor.addprevious(element)


def _front_paragraph(document, text: str = "", *, style: str = "Tex2Sto Body"):
    paragraph = document.add_paragraph(text, style=style)
    return paragraph


def _title_page(document, project: SourceProject) -> list:
    metadata = project.metadata
    elements = []
    for text in (
        "МИНОБРНАУКИ РОССИИ",
        "Федеральное государственное автономное образовательное учреждение",
        "высшего образования",
        "«Самарский национальный исследовательский университет",
        "имени академика С. П. Королева»",
        metadata.institute,
        metadata.faculty,
        metadata.department,
    ):
        if not text:
            continue
        paragraph = _front_paragraph(document, text, style="Tex2Sto Title Institution")
        elements.append(paragraph._p)
    title_kind = _front_paragraph(
        document,
        "ВЫПУСКНАЯ КВАЛИФИКАЦИОННАЯ РАБОТА",
        style="Tex2Sto Title Kind",
    )
    elements.append(title_kind._p)
    title = _front_paragraph(document, metadata.title.upper(), style="Tex2Sto Title Name")
    elements.append(title._p)
    details = (
        f"по направлению подготовки {metadata.program_code} {metadata.program_name}\n"
        f"профиль «{metadata.study_profile}»\n\n"
        f"Обучающийся: {metadata.author}, группа {metadata.student_group}\n"
        f"Руководитель: {metadata.supervisor_details} {metadata.supervisor_name}"
    )
    if metadata.norm_controller:
        details += f"\nНормоконтролер: {metadata.norm_controller}"
    paragraph = _front_paragraph(document, details, style="Tex2Sto Title Details")
    elements.append(paragraph._p)
    city = _front_paragraph(
        document,
        f"{metadata.city} {metadata.year}",
        style="Tex2Sto Title City",
    )
    city.add_run().add_break(WD_BREAK.PAGE)
    elements.append(city._p)
    return elements


def _assignment_pages(document, project: SourceProject) -> list:
    metadata = project.metadata
    if metadata.assignment_variant == "none":
        return []
    elements = []
    heading = _front_paragraph(document, "ЗАДАНИЕ", style="Tex2Sto Structural Heading")
    elements.append(heading._p)
    lines = (
        f"на выпускную квалификационную работу обучающемуся {metadata.author}\n"
        f"Тема: {metadata.title}\n"
        f"Утверждающий: {metadata.assignment_approver}\n"
        f"Цель работы: {metadata.assignment_goal or 'определяется содержанием работы'}\n"
        f"Вопросы, подлежащие разработке: {metadata.assignment_questions}\n"
        f"Дата выдачи: {metadata.assignment_issued}\n"
        f"Срок представления: {metadata.assignment_due}"
    )
    body = _front_paragraph(document, lines)
    body.add_run().add_break(WD_BREAK.PAGE)
    elements.append(body._p)
    if metadata.assignment_variant == "2":
        continuation = _front_paragraph(
            document,
            "ЗАДАНИЕ (ПРОДОЛЖЕНИЕ)",
            style="Tex2Sto Structural Heading",
        )
        elements.append(continuation._p)
        signatures = _front_paragraph(
            document,
            "Консультанты:\n"
            + "\n".join(f"{item.role}: {item.name}" for item in metadata.consultants)
            + f"\n\nРуководитель: {metadata.supervisor_name}\nОбучающийся: {metadata.author}",
        )
        signatures.add_run().add_break(WD_BREAK.PAGE)
        elements.append(signatures._p)
    return elements


def _abstract_and_toc(
    document,
    project: SourceProject,
    index: NumberingIndex,
    toc_entries: list[tuple[int, str, str]],
) -> list:
    counts = {kind: sum(item.kind is kind for item in index.objects) for kind in ObjectKind}
    appendices = len(find_command_calls(project.body, "appendix", 2))
    elements = []
    heading = _front_paragraph(document, "РЕФЕРАТ", style="Tex2Sto Structural Heading")
    elements.append(heading._p)
    stats = _front_paragraph(document)
    stats.add_run("Работа: ")
    add_field(stats, "NUMPAGES", "0")
    stats.add_run(
        f" с., {counts[ObjectKind.FIGURE]} рис., {counts[ObjectKind.TABLE]} табл., "
        f"{len(project.bibliography)} источник(ов), "
        f"{appendices} прил."
    )
    elements.append(stats._p)
    keywords = _front_paragraph(
        document,
        ", ".join(keyword.upper() for keyword in project.metadata.keywords),
        style="Tex2Sto Abstract Keywords",
    )
    elements.append(keywords._p)
    abstract = _front_paragraph(document, project.metadata.abstract)
    abstract.add_run().add_break(WD_BREAK.PAGE)
    elements.append(abstract._p)
    toc_heading = _front_paragraph(document, "СОДЕРЖАНИЕ", style="Tex2Sto Structural Heading")
    elements.append(toc_heading._p)
    for level, title, bookmark in toc_entries:
        entry = _front_paragraph(document, style=f"Tex2Sto TOC {level}")
        entry.add_run(title)
        entry.add_run("\t")
        add_field(entry, f"PAGEREF {bookmark} \\h", "?")
        elements.append(entry._p)
    return elements


def _apply_styles(document) -> None:
    document.styles["Tex2Sto Table Continuation"].font.color.rgb = RGBColor(0, 0, 0)
    appendix_title_pending = False
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text == PAGE_BREAK_MARKER:
            paragraph.clear()
            paragraph.add_run().add_break(WD_BREAK.PAGE)
            paragraph.style = "Tex2Sto Body"
        elif paragraph.style.name.startswith("Heading "):
            level = paragraph.style.name.rsplit(" ", 1)[-1]
            paragraph.style = f"Tex2Sto Heading {level}"
        elif text.startswith(("Рисунок ", "Таблица ")):
            paragraph.style = (
                "Tex2Sto Figure Caption" if text.startswith("Рисунок ") else "Tex2Sto Table Caption"
            )
        elif (
            text
            in {
                "ВВЕДЕНИЕ",
                "ЗАКЛЮЧЕНИЕ",
                "ТЕРМИНЫ И ОПРЕДЕЛЕНИЯ",
                "ПЕРЕЧЕНЬ СОКРАЩЕНИЙ И ОБОЗНАЧЕНИЙ",
                "СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ",
            }
            or text.startswith("ПРИЛОЖЕНИЕ ")
            or (appendix_title_pending and text)
        ):
            paragraph.style = "Tex2Sto Structural Heading"
        elif paragraph.style.name in {"Normal", "First Paragraph"}:
            paragraph.style = "Tex2Sto Body"
        if text.startswith("ПРИЛОЖЕНИЕ "):
            appendix_title_pending = True
        elif appendix_title_pending and text:
            appendix_title_pending = False
    for table in document.tables:
        table.style = "Tex2Sto Table"
        if table.rows:
            repeat_table_row(table.rows[0])
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.style = "Tex2Sto Table Text"


def _format_lists(document) -> None:
    numbering = document.part.numbering_part.element
    for abstract in numbering.findall(qn("w:abstractNum")):
        identifier = int(abstract.get(qn("w:abstractNumId"), "0"))
        if identifier < 991:
            continue
        for level in abstract.findall(qn("w:lvl")):
            number_format = level.find(qn("w:numFmt"))
            level_text = level.find(qn("w:lvlText"))
            if number_format is None or level_text is None:
                continue
            current_format = number_format.get(qn("w:val"))
            current_text = level_text.get(qn("w:val"), "")
            if current_format == "bullet":
                level_text.set(qn("w:val"), "\u2014")
                run_properties = level.find(qn("w:rPr"))
                if run_properties is not None:
                    level.remove(run_properties)
                continue
            if current_format == "lowerLetter":
                number_format.set(qn("w:val"), "russianLower")
            elif current_format == "lowerRoman":
                number_format.set(qn("w:val"), "decimal")
            level_text.set(qn("w:val"), current_text.rstrip(".") + ")")


def _toc_entries(document) -> list[tuple[int, str, str]]:
    headings: list[tuple[int, str, object]] = []
    for paragraph in document.paragraphs:
        text = " ".join(paragraph.text.split())
        style = paragraph.style.name
        if not text:
            continue
        if style == "Tex2Sto Structural Heading":
            headings.append((1, text, paragraph))
        elif style.startswith("Tex2Sto Heading "):
            headings.append((int(style.rsplit(" ", 1)[-1]), text, paragraph))

    entries: list[tuple[int, str, str]] = []
    skip_next = False
    for position, (level, title, paragraph) in enumerate(headings):
        if skip_next:
            skip_next = False
            continue
        if title.startswith("ПРИЛОЖЕНИЕ ") and position + 1 < len(headings):
            title = f"{title} {headings[position + 1][1]}"
            skip_next = True
        bookmark = f"tex2sto_toc_{position + 1}"
        add_bookmark(paragraph, bookmark, position + 100)
        entries.append((level, title, bookmark))
    return entries


def _format_equations(document, index: NumberingIndex) -> None:
    numbers = [item.display for item in index.objects if item.kind is ObjectKind.EQUATION]
    equation_index = 0
    for paragraph in document.paragraphs:
        math_paragraph = paragraph._p.find(qn("m:oMathPara"))
        if math_paragraph is None:
            continue
        math = math_paragraph.find(qn("m:oMath"))
        if math is None or equation_index >= len(numbers):
            continue
        math_paragraph.remove(math)
        paragraph._p.remove(math_paragraph)
        leading_run = OxmlElement("w:r")
        leading_run.append(OxmlElement("w:tab"))
        insertion = 1 if paragraph._p.pPr is not None else 0
        paragraph._p.insert(insertion, leading_run)
        paragraph._p.insert(insertion + 1, math)
        paragraph.add_run(f"\t({numbers[equation_index]})")
        paragraph.style = "Tex2Sto Equation"
        equation_index += 1


def _balance_table_columns(table) -> None:
    grid_columns = table._tbl.tblGrid.findall(qn("w:gridCol"))
    if len(grid_columns) < 2:
        return
    total_width = sum(int(column.get(qn("w:w"), "0")) for column in grid_columns)
    if total_width <= 0:
        return

    content_rows = [
        row
        for row in table.rows
        if not any(TABLE_BREAK_MARKER in cell.text for cell in row.cells)
    ]
    weights = [
        max((len(row.cells[position].text.strip()) for row in content_rows), default=0) + 8
        for position in range(len(grid_columns))
    ]
    allocated = 0
    for position, (column, weight) in enumerate(zip(grid_columns, weights, strict=True)):
        width = (
            total_width - allocated
            if position == len(grid_columns) - 1
            else round(total_width * weight / sum(weights))
        )
        column.set(qn("w:w"), str(width))
        allocated += width


def _table_segment(table, start: int, end: int):
    segment = deepcopy(table._tbl)
    for position, row in enumerate(segment.findall(qn("w:tr"))):
        if position != 0 and not start <= position < end:
            segment.remove(row)
    return segment


def _split_longtable(document, table, display: str) -> None:
    marker_rows = [
        position
        for position, row in enumerate(table.rows)
        if any(TABLE_BREAK_MARKER in cell.text for cell in row.cells)
    ]
    if not marker_rows:
        raise RuntimeError("validated longtable lost its table-break marker during DOCX rendering")

    starts = [1, *(position + 1 for position in marker_rows)]
    ends = [*marker_rows, len(table.rows)]
    elements = []
    for segment_number, (start, end) in enumerate(zip(starts, ends, strict=True)):
        if segment_number:
            continuation = _front_paragraph(document, style="Tex2Sto Table Continuation")
            continuation.add_run().add_break(WD_BREAK.PAGE)
            continuation.add_run(f"Продолжение таблицы {display}")
            elements.append(continuation._p)
        elements.append(_table_segment(table, start, end))

    parent = table._tbl.getparent()
    insertion = parent.index(table._tbl)
    parent.remove(table._tbl)
    for element in elements:
        parent.insert(insertion, element)
        insertion += 1


def _format_tables(document, project: SourceProject, index: NumberingIndex) -> None:
    table_objects = [item for item in index.objects if item.kind is ObjectKind.TABLE]
    longtable_positions = {start for start, _, _ in find_environment(project.body, "longtable")}
    captions = [
        paragraph
        for paragraph in document.paragraphs
        if paragraph.text.strip().startswith("Таблица ")
    ]
    tables = list(document.tables)
    for position, (table, numbered) in enumerate(zip(tables, table_objects, strict=False)):
        _balance_table_columns(table)
        bookmark = f"tex2sto_table_{position + 1}"
        if position < len(captions):
            add_bookmark(captions[position], bookmark, position + 1000)
        if numbered.position not in longtable_positions or not table.rows:
            continue
        _split_longtable(document, table, numbered.display)


def _postprocess(path: Path, project: SourceProject, index: NumberingIndex) -> None:
    document = Document(path)
    _apply_styles(document)
    _format_lists(document)
    _format_equations(document, index)
    _format_tables(document, project, index)
    toc_entries = _toc_entries(document)
    anchor = document.element.body[0]
    elements = [
        *_title_page(document, project),
        *_assignment_pages(document, project),
        *_abstract_and_toc(document, project, index, toc_entries),
    ]
    for element in elements:
        _move_before(element, anchor)
    set_update_fields(document)
    document.core_properties.title = project.metadata.title
    document.core_properties.author = project.metadata.author
    document.save(path)


def render_docx(project: SourceProject, index: NumberingIndex, output: Path) -> Path:
    pandoc = _pandoc()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tex2sto-docx-") as temporary:
        source = Path(temporary) / "document.tex"
        source.write_text(renderer_body(project, index, target="docx"), encoding="utf-8")
        command = [
            pandoc,
            str(source),
            "--from=latex",
            "--to=docx",
            "--standalone",
            "--number-sections",
            f"--reference-doc={PROFILE / 'reference.docx'}",
            f"--lua-filter={PROFILE / 'ssau.lua'}",
            f"--resource-path={project.root}",
            "--output",
            str(output),
        ]
        run_tool(command, cwd=project.root)
    _postprocess(output, project, index)
    return output
