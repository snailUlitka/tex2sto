"""Editable SSAU practice cover and competency assignment front matter."""

from __future__ import annotations

from datetime import date

from docx.enum.text import WD_BREAK
from docx.shared import Mm, Pt

from tex2sto.model.document import DocumentMetadata
from tex2sto.renderers.docx_fields import repeat_table_row

INSTITUTION = (
    "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
    "федеральное государственное автономное образовательное учреждение",
    "высшего образования «Самарский национальный исследовательский",
    "университет имени академика С. П. Королева»",
    "(Самарский университет)",
)


def display_date(value: str) -> str:
    return date.fromisoformat(value).strftime("%d.%m.%Y") if value else "____________"


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

    table = document.add_table(rows=1, cols=3)
    table.style = "Tex2Sto Table"
    table.autofit = False
    widths = [Mm(55), Mm(55), Mm(55)]
    for column, width in zip(table.columns, widths, strict=True):
        column.width = width
    for cell, text in zip(
        table.rows[0].cells,
        (
            "Планируемые результаты освоения программы (компетенции)",
            "Планируемые результаты практики",
            "Содержание задания",
        ),
        strict=True,
    ):
        cell.text = text
    repeat_table_row(table.rows[0])
    for assignment in metadata.practice_assignments:
        for cell, text in zip(
            table.add_row().cells,
            (assignment.competency, assignment.outcomes, assignment.task),
            strict=True,
        ):
            cell.text = text
    for row in table.rows:
        for cell in row.cells:
            for item in cell.paragraphs:
                item.style = "Tex2Sto Table Text"
                item.paragraph_format.line_spacing = table_spacing
    elements.append(table._tbl)
    paragraph(f"Дата выдачи задания: {metadata.assignment_issued or display_date(title.start)}")
    paragraph(f"Срок представления отчёта: {metadata.assignment_due or display_date(title.end)}")
    paragraph(f"Руководитель практики: __________ {metadata.supervisor_name}")
    paragraph(f"Студент: __________ {metadata.author}").add_run().add_break(WD_BREAK.PAGE)
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
        " & ".join(_latex_text(value) for value in (row.competency, row.outcomes, row.task))
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
