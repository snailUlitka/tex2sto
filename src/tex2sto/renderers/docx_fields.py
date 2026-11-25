"""Focused WordprocessingML helpers kept outside document semantics."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def _field_char(paragraph: Paragraph, kind: str) -> None:
    node = OxmlElement("w:fldChar")
    node.set(qn("w:fldCharType"), kind)
    paragraph.add_run()._r.append(node)


def begin_field(paragraph: Paragraph, instruction: str) -> None:
    _field_char(paragraph, "begin")
    instruction_node = OxmlElement("w:instrText")
    instruction_node.set(qn("xml:space"), "preserve")
    instruction_node.text = f" {instruction} "
    paragraph.add_run()._r.append(instruction_node)
    _field_char(paragraph, "separate")


def end_field(paragraph: Paragraph) -> None:
    _field_char(paragraph, "end")


def add_field(paragraph: Paragraph, instruction: str, placeholder: str = "0") -> None:
    begin_field(paragraph, instruction)
    paragraph.add_run(placeholder)
    end_field(paragraph)


def set_update_fields(document, *, on_open: bool = True) -> None:
    settings = document.settings.element
    node = settings.find(qn("w:updateFields"))
    if node is None:
        node = OxmlElement("w:updateFields")
        settings.insert_element_before(
            node, "w:hdrShapeDefaults", "w:footnotePr", "w:endnotePr", "w:compat"
        )
    node.set(qn("w:val"), "true" if on_open else "false")


def repeat_table_row(row) -> None:
    properties = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    properties.append(marker)


def add_bookmark(paragraph: Paragraph, name: str, identifier: int) -> None:
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(identifier))
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), str(identifier))
    insertion = 1 if paragraph._p.pPr is not None else 0
    paragraph._p.insert(insertion, start)
    paragraph._p.append(end)
