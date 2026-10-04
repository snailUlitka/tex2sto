"""SSAU laboratory cover based on the supplied report examples."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm, Pt

from tex2sto.model.document import LabTitle

INSTITUTION_LINES = (
    "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ",
    "ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ",
    "«САМАРСКИЙ НАЦИОНАЛЬНЫЙ ИССЛЕДОВАТЕЛЬСКИЙ",
    "УНИВЕРСИТЕТ ИМЕНИ АКАДЕМИКА С. П. КОРОЛЕВА»",
    "(САМАРСКИЙ УНИВЕРСИТЕТ)",
)


def report_name(title: LabTitle) -> str:
    return f"Отчёт по лабораторной работе №\u00a0{title.number}"


def _label(text: str) -> str:
    return text.rstrip(": ") + ":"


def docx_title_page(document, title: LabTitle) -> list:
    elements = []

    def paragraph(text: str, style: str = "Tex2Sto Lab Center", *, before: int = 0):
        item = document.add_paragraph(text, style)
        item.paragraph_format.space_before = Pt(before)
        elements.append(item._p)
        return item

    for text in INSTITUTION_LINES:
        paragraph(text, "Tex2Sto Lab Institution")
    paragraph(report_name(title), before=96)
    paragraph(f"по курсу «{title.course}»")
    if title.variant:
        paragraph(f"Вариант №\u00a0{title.variant}", before=24)
    paragraph(_label(title.author_label), "Tex2Sto Lab Signature", before=48)
    paragraph(title.author, "Tex2Sto Lab Signature")
    paragraph(f"гр. {title.group}", "Tex2Sto Lab Signature")
    paragraph(_label(title.reviewer_label), "Tex2Sto Lab Signature", before=24)
    last = paragraph(title.reviewer, "Tex2Sto Lab Signature")
    last.paragraph_format.keep_with_next = False

    # The first-page footer keeps the editable city/year at the page bottom,
    # independent of wrapping in the course and participant names.
    section = document.sections[0]
    section.different_first_page_header_footer = True
    footer = section.first_page_footer.paragraphs[0]
    footer.clear()
    footer.style = document.styles["Tex2Sto Lab City"]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.paragraph_format.space_after = max(Mm(0), Mm(20) - section.footer_distance)
    footer.add_run(f"{title.city} {title.year}")
    return elements


def _latex_text(value: str) -> str:
    escapes = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "_": r"\_",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "~": r"\textasciitilde{}",
        "\u00a0": "~",
    }
    return "".join(escapes.get(char, char) for char in value)


def latex_title_page(title: LabTitle) -> str:
    institution = "\n".join(_latex_text(text) + r"\par" for text in INSTITUTION_LINES)
    variant = (
        rf"\vspace{{24pt}} Вариант №~{_latex_text(title.variant)}\par" if title.variant else ""
    )
    return rf"""
\thispagestyle{{empty}}
\begingroup
\centering
{institution}
\vspace{{96pt}}
{_latex_text(report_name(title))}\par
по курсу «{_latex_text(title.course)}»\par
{variant}
\vspace{{48pt}}
\raggedleft
{_latex_text(_label(title.author_label))}\par
{_latex_text(title.author)}\par
гр. {_latex_text(title.group)}\par
\vspace{{24pt}}
{_latex_text(_label(title.reviewer_label))}\par
{_latex_text(title.reviewer)}\par
\vfill
\centering {_latex_text(title.city)} {_latex_text(title.year)}\par
\endgroup
\clearpage
"""
