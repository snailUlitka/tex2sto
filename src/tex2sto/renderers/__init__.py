"""DOCX and PDF renderer entry points."""

from tex2sto.renderers.docx import render_docx
from tex2sto.renderers.pdf import render_pdf

__all__ = ["render_docx", "render_pdf"]
