"""High-level validated build orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tex2sto.model import SourceProject, build_numbering
from tex2sto.renderers import render_docx, render_pdf


@dataclass(frozen=True, slots=True)
class BuildOptions:
    output_dir: Path
    pdf: bool = False
    numbering: str = "auto"
    numbering_threshold: int = 10
    figure_numbering: str | None = None
    table_numbering: str | None = None
    equation_numbering: str | None = None


def build_project(project: SourceProject, options: BuildOptions) -> tuple[Path, ...]:
    output_dir = options.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    index = build_numbering(
        project,
        numbering=options.numbering,
        threshold=options.numbering_threshold,
        overrides={
            "figure": options.figure_numbering,
            "table": options.table_numbering,
            "equation": options.equation_numbering,
        },
    )
    stem = project.master.stem
    outputs = [render_docx(project, index, output_dir / f"{stem}.docx")]
    if options.pdf:
        outputs.append(render_pdf(project, index, output_dir / f"{stem}.pdf"))
    return tuple(outputs)
