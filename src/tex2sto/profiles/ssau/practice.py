"""Editable SSAU practice cover and competency assignment front matter."""

from __future__ import annotations

from datetime import date

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.shared import Length, Mm, Pt, Twips

from tex2sto.model.document import DocumentMetadata, PracticeAssignment
from tex2sto.renderers.docx_fields import repeat_table_row

INSTITUTION = (
    "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
    "федеральное государственное автономное образовательное учреждение",
    "высшего образования «Самарский национальный исследовательский",
    "университет имени академика С. П. Королева»",
    "(Самарский университет)",
)

DEPARTMENT_INSTITUTION = (
    "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ",
    "РОССИЙСКОЙ ФЕДЕРАЦИИ",
    INSTITUTION[1],
    "высшего образования «Самарский национальный исследовательский университет "
    "имени академика С.П. Королева»",
    INSTITUTION[-1],
)


def display_date(value: str) -> str:
    return date.fromisoformat(value).strftime("%d.%m.%Y") if value else "____________"


def _cell_content(cell, paragraphs: tuple[str, ...], spacing: float) -> None:
    first = cell.paragraphs[0]
    first.text = paragraphs[0]
    for text in paragraphs[1:]:
        cell.add_paragraph(text)
    for item in cell.paragraphs:
        item.style = "Tex2Sto Table Text"
        item.paragraph_format.line_spacing = spacing


def _assignment_table(
    document,
    assignments: list[PracticeAssignment],
    widths: tuple[Length, ...],
    *,
    spacing: float,
    department_template: bool = False,
):
    table = document.add_table(rows=1, cols=3)
    table.style = "Tex2Sto Table"
    table.autofit = False
    if department_template:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
    preferred_width = table._tbl.tblPr.find(qn("w:tblW"))
    preferred_width.set(qn("w:type"), "dxa")
    preferred_width.set(qn("w:w"), str(sum(width.twips for width in widths)))
    for column, width in zip(table.columns, widths, strict=True):
        column.width = width

    header = table.rows[0]
    first_header = (
        "Планируемые результаты освоения образовательной программы (компетенции)"
        if department_template
        else "Планируемые результаты освоения программы (компетенции)"
    )
    headers = (first_header, "Планируемые результаты практики", "Содержание задания")
    for cell, text, width in zip(header.cells, headers, widths, strict=True):
        cell.width = width
        _cell_content(cell, (text,), spacing)
        if department_template:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    repeat_table_row(header)

    for assignment in assignments:
        columns = (assignment.competency, assignment.outcomes, assignment.task)
        for cell, paragraphs, width in zip(table.add_row().cells, columns, widths, strict=True):
            cell.width = width
            _cell_content(cell, paragraphs, spacing)
    return table


def docx_front_matter(document, metadata: DocumentMetadata, table_spacing: float) -> list:
    title = metadata.practice_title
    assert title is not None
    elements = []

    def paragraph(text: str, style="Tex2Sto Practice Details", before=0):
        item = document.add_paragraph(text, style)
        item.paragraph_format.space_before = Pt(before)
        elements.append(item._p)
        return item

    def institution():
        for line in (*INSTITUTION, metadata.institute, metadata.department):
            paragraph(line, "Tex2Sto Practice Institution")

    institution()
    paragraph("ОТЧЕТ ПО ПРАКТИКЕ", "Tex2Sto Practice Center", 18)
    paragraph(f"Вид практики: {title.kind}", before=12)
    paragraph(f"Тип практики: {title.type}")
    paragraph(
        f"Сроки прохождения практики: с {display_date(title.start)} по {display_date(title.end)}"
    )
    paragraph(f"По направлению подготовки {metadata.program_code} {metadata.program_name}")
    paragraph(f"Уровень {title.study_level}")
    paragraph(f"Направленность (профиль) «{metadata.study_profile}»")
    paragraph(f"Студент группы № {metadata.student_group} __________ {metadata.author}", before=18)
    paragraph(
        f"Руководитель практики: {metadata.supervisor_details} "
        f"__________ {metadata.supervisor_name}"
    )
    paragraph(f"Дата сдачи: {display_date(title.submitted)}", before=12)
    paragraph(f"Дата защиты: {display_date(title.defended)}")
    paragraph(f"Оценка: {title.grade or '____________'}").add_run().add_break(WD_BREAK.PAGE)

    section = document.sections[0]
    section.different_first_page_header_footer = True
    footer = section.first_page_footer.paragraphs[0]
    footer.clear()
    footer.style = "Tex2Sto Practice Center"
    footer.paragraph_format.space_after = max(Mm(0), Mm(20) - section.footer_distance)
    footer.add_run(f"{metadata.city} {metadata.year}")

    institution()
    paragraph("ЗАДАНИЕ ДЛЯ ВЫПОЛНЕНИЯ РАБОТ В ПЕРИОД ПРАКТИКИ", "Tex2Sto Practice Center", 12)
    paragraph(f"Студенту группы {metadata.student_group}: {title.author_dative}", before=12)
    paragraph(
        f"Направление на практику оформлено приказом по университету "
        f"от {display_date(title.order_date)} № {title.order_number}"
    )
    paragraph(f"Место практики: {title.organization}")
    paragraph(f"Тема НИР: «{metadata.title}»")

    table = _assignment_table(
        document, metadata.practice_assignments, (Mm(55),) * 3, spacing=table_spacing
    )
    elements.append(table._tbl)
    paragraph(f"Дата выдачи задания: {metadata.assignment_issued or display_date(title.start)}")
    paragraph(f"Срок представления отчёта: {metadata.assignment_due or display_date(title.end)}")
    paragraph(f"Руководитель практики: __________ {metadata.supervisor_name}")
    paragraph(f"Студент: __________ {metadata.author}").add_run().add_break(WD_BREAK.PAGE)
    return elements


def docx_department_front_matter(document, metadata: DocumentMetadata) -> list:
    title = metadata.practice_title
    assert title is not None
    elements = []
    center = "Tex2Sto Practice Center"
    details = "Tex2Sto Practice Details"
    field = "Tex2Sto Practice Form Field"
    note = "Tex2Sto Practice Form Note"

    def paragraph(text: str, style=details, *, before=0, keep_with_next=False):
        item = document.add_paragraph(text, style)
        item.paragraph_format.space_before = Pt(before)
        item.paragraph_format.keep_with_next = keep_with_next
        elements.append(item._p)
        return item

    def institution(*, start_page=False):
        for position, line in enumerate(DEPARTMENT_INSTITUTION):
            item = paragraph(line, field)
            if position == 0 and start_page:
                item.paragraph_format.page_break_before = True
        paragraph(metadata.institute, center, before=14)
        paragraph(metadata.department, center)

    def signature(label: str, name: str, *, before=0, caption=False):
        item = paragraph(label, before=before, keep_with_next=caption)
        item.paragraph_format.keep_together = True
        item.paragraph_format.tab_stops.add_tab_stop(Mm(145), WD_TAB_ALIGNMENT.RIGHT)
        signature_name = name.replace(" ", "\u00a0")
        item.add_run(f"\t______________\u00a0{signature_name}")
        if caption:
            paragraph("(подпись)", "Tex2Sto Practice Signature Note")

    section = document.sections[0]
    section.different_first_page_header_footer = True
    section.first_page_footer.paragraphs[0].clear()

    institution()
    paragraph("ОТЧЕТ ПО ПРАКТИКЕ", field, before=14).runs[0].bold = True
    for label, value, explanation in (
        ("Вид практики ", title.kind, "(учебная, производственная)"),
        ("Тип практики ", title.type, "(в соответствии с ОПОП ВО)"),
    ):
        item = paragraph(label, field, before=17, keep_with_next=True)
        item.add_run(value).underline = True
        paragraph(explanation, note)
    paragraph(
        f"Сроки прохождения практики: с {display_date(title.start)} по {display_date(title.end)}",
        field,
        before=17,
        keep_with_next=True,
    )
    paragraph("(в соответствии с календарным учебным графиком)", note)
    paragraph(
        f"по направлению подготовки {metadata.program_code} {metadata.program_name}",
        center,
        before=16,
    )
    paragraph(f"(уровень {title.study_level})", center)
    paragraph(f"направленность (профиль) «{metadata.study_profile}»", center)

    student = f"Студент группы № {metadata.student_group}"
    signature(student, metadata.author, before=16)
    paragraph("Руководитель практики,", keep_with_next=True)
    signature(metadata.supervisor_details, metadata.supervisor_name)
    paragraph(f"Дата сдачи {display_date(title.submitted)}", before=14)
    paragraph(f"Дата защиты {display_date(title.defended)}")
    grade = paragraph(
        f"Оценка {title.grade or '____________'}", field, before=12, keep_with_next=True
    )
    grade.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph(f"{metadata.city} {metadata.year}", field, before=16)

    institution(start_page=True)
    heading = paragraph(
        "Задание(я) для выполнения определенных видов работ, связанных с будущей "
        "профессиональной деятельностью (сбор и анализ данных и материалов, "
        "проведение исследований)",
        center,
        before=16,
    )
    heading.runs[0].bold = True
    paragraph(f"Студенту группы {metadata.student_group}", center, before=12)
    paragraph(title.author_dative, center)
    paragraph("Направление на практику оформлено приказом по университету", center)
    paragraph(f"от {display_date(title.order_date)} г. № {title.order_number}", center)
    paragraph(title.organization, center, keep_with_next=True)
    paragraph(
        "(наименование профильной организации или структурного подразделения университета)",
        note,
    )
    topic = paragraph(f"Тема НИР: «{metadata.title}»", keep_with_next=True)
    topic.paragraph_format.space_after = Pt(12)

    width = section.page_width.twips - section.left_margin.twips - section.right_margin.twips
    # Scale the department's column proportions to the SSAU page margins.
    first = round(width * 2410 / 9495)
    second = round(width * 3684 / 9495)
    table = _assignment_table(
        document,
        metadata.practice_assignments,
        (Twips(first), Twips(second), Twips(width - first - second)),
        spacing=1.0,
        department_template=True,
    )
    elements.append(table._tbl)

    issued = metadata.assignment_issued or display_date(title.start)
    due = metadata.assignment_due or display_date(title.end)
    paragraph(f"Дата выдачи задания {issued.rstrip('.')}.", before=12)
    paragraph(f"Срок представления на кафедру отчета о практике {due.rstrip('.')}.")
    paragraph("Руководитель практики,", before=6, keep_with_next=True)
    signature(metadata.supervisor_details, metadata.supervisor_name, caption=True)
    signature(student, metadata.author, before=10, caption=True)
    return elements


def latex_front_matter(metadata: DocumentMetadata) -> str:
    """Lower the same structured fields for the experimental PDF preview."""
    from tex2sto.profiles.ssau.lab_title import _latex_text

    title = metadata.practice_title
    assert title is not None

    def paragraphs(values):
        return "\n".join(_latex_text(value) + r"\par" for value in values)

    institution = paragraphs((*INSTITUTION, metadata.institute, metadata.department))
    cover = paragraphs(
        (
            "ОТЧЕТ ПО ПРАКТИКЕ",
            f"Вид практики: {title.kind}",
            f"Тип практики: {title.type}",
            f"Сроки прохождения: с {display_date(title.start)} по {display_date(title.end)}",
            f"Направление: {metadata.program_code} {metadata.program_name}",
            f"Уровень {title.study_level}; профиль «{metadata.study_profile}»",
            f"Студент группы {metadata.student_group}: {metadata.author}",
            f"Руководитель: {metadata.supervisor_details} {metadata.supervisor_name}",
            f"Дата сдачи: {display_date(title.submitted)}",
            f"Дата защиты: {display_date(title.defended)}",
            f"Оценка: {title.grade or '________'}",
        )
    )
    assignment = paragraphs(
        (
            "ЗАДАНИЕ ДЛЯ ВЫПОЛНЕНИЯ РАБОТ В ПЕРИОД ПРАКТИКИ",
            f"Студенту группы {metadata.student_group}: {title.author_dative}",
            f"Приказ от {display_date(title.order_date)} № {title.order_number}",
            f"Место практики: {title.organization}",
            f"Тема НИР: «{metadata.title}»",
        )
    )
    header = "Компетенции & Результаты практики & Содержание задания " + r"\\ \hline"
    rows = "\n".join(
        " & ".join(
            r"\par ".join(_latex_text(value) for value in cell)
            for cell in (row.competency, row.outcomes, row.task)
        )
        + r"\\ \hline"
        for row in metadata.practice_assignments
    )
    signatures = paragraphs(
        (
            f"Дата выдачи: {metadata.assignment_issued or display_date(title.start)}",
            f"Срок представления: {metadata.assignment_due or display_date(title.end)}",
            f"Руководитель: {metadata.supervisor_name}",
            f"Студент: {metadata.author}",
        )
    )
    return rf"""
\thispagestyle{{empty}}\begingroup\centering
{institution}
\vspace{{18pt}}
{cover}
\vfill {_latex_text(metadata.city)} {_latex_text(metadata.year)}\par
\endgroup\clearpage
\begingroup\centering {institution}\endgroup
{assignment}
\begin{{longtable}}{{|p{{0.3\linewidth}}|p{{0.3\linewidth}}|p{{0.3\linewidth}}|}}
\hline {header}\endfirsthead
\hline {header}\endhead
{rows}
\end{{longtable}}
{signatures}\clearpage
"""
