"""Focused WordprocessingML helpers kept outside document semantics."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def add_field(paragraph: Paragraph, instruction: str, placeholder: str = "0") -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction_node = OxmlElement("w:instrText")
    instruction_node.set(qn("xml:space"), "preserve")
    instruction_node.text = instruction
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction_node, separate, text, end))


def set_update_fields(document) -> None:
    settings = document.settings.element
    node = settings.find(qn("w:updateFields"))
    if node is None:
        node = OxmlElement("w:updateFields")
        settings.append(node)
    node.set(qn("w:val"), "true")


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


def _append_field_node(paragraph: Paragraph, node, *, visible: bool = False) -> None:
    run = paragraph.add_run()
    if visible:
        properties = OxmlElement("w:rPr")
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "000000")
        properties.append(color)
        run._r.append(properties)
    run._r.append(node)


def _field_char(kind: str):
    node = OxmlElement("w:fldChar")
    node.set(qn("w:fldCharType"), kind)
    return node


def _instruction(value: str):
    node = OxmlElement("w:instrText")
    node.set(qn("xml:space"), "preserve")
    node.text = value
    return node


def _result(value: str):
    node = OxmlElement("w:t")
    node.text = value
    return node


def add_table_continuation_field(paragraph: Paragraph, bookmark: str, text: str) -> None:
    """Add a Word IF field shown only after the table's first page."""
    nodes = (
        _field_char("begin"),
        _instruction(" IF "),
        _field_char("begin"),
        _instruction(" PAGE "),
        _field_char("separate"),
        _result("1"),
        _field_char("end"),
        _instruction(" = "),
        _field_char("begin"),
        _instruction(f" PAGEREF {bookmark} "),
        _field_char("separate"),
        _result("1"),
        _field_char("end"),
        _instruction(f' "" "{text}" '),
        _field_char("separate"),
        _result(""),
        _field_char("end"),
    )
    for position, node in enumerate(nodes):
        _append_field_node(paragraph, node, visible=position == len(nodes) - 2)


def remove_cell_borders(cell) -> None:
    properties = cell._tc.get_or_add_tcPr()
    existing = properties.find(qn("w:tcBorders"))
    if existing is not None:
        properties.remove(existing)
    borders = OxmlElement("w:tcBorders")
    for edge_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        edge = OxmlElement(f"w:{edge_name}")
        edge.set(qn("w:val"), "nil")
        borders.append(edge)
    properties.append(borders)
