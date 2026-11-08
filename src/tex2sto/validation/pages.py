"""Check page limits against an already paginated, externally rendered PDF."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from tex2sto.config import ProjectSettings
from tex2sto.diagnostics import DiagnosticBag
from tex2sto.errors import ToolError
from tex2sto.renderers.tools import require_tool


def check_rendered_pages(pdf: Path, settings: ProjectSettings) -> tuple[int, DiagnosticBag]:
    pdf = pdf.expanduser().resolve()
    if not pdf.is_file():
        raise ToolError(f"rendered PDF does not exist: {pdf}")
    completed = subprocess.run(
        [require_tool("pdfinfo"), str(pdf)],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if completed.returncode or match is None:
        raise ToolError(f"cannot read rendered PDF page count: {pdf}")
    count = int(match.group(1))
    bag = DiagnosticBag()
    if settings.minimum_pages is not None and count < settings.minimum_pages:
        bag.warning(
            "T2S-W601",
            f"rendered document has {count} pages; minimum is {settings.minimum_pages}",
            path=pdf,
        )
    if settings.maximum_pages is not None and count > settings.maximum_pages:
        bag.warning(
            "T2S-W602",
            f"rendered document has {count} pages; maximum is {settings.maximum_pages}",
            path=pdf,
        )
    return count, bag
