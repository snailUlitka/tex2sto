"""High-level validated build orchestration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from tex2sto.model import SourceProject, build_numbering
from tex2sto.renderers import render_docx, render_pdf


@dataclass(frozen=True, slots=True)
class BuildOptions:
    output_dir: Path
    pdf: bool | None = None
    numbering: str | None = None
    numbering_threshold: int | None = None
    figure_numbering: str | None = None
    table_numbering: str | None = None
    equation_numbering: str | None = None


def build_project(project: SourceProject, options: BuildOptions) -> tuple[Path, ...]:
    output_dir = options.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    from tex2sto.config import override_settings

    settings = override_settings(
        project.settings,
        pdf=options.pdf,
        numbering=options.numbering,
        numbering_threshold=options.numbering_threshold,
        figure_numbering=options.figure_numbering,
        table_numbering=options.table_numbering,
        equation_numbering=options.equation_numbering,
    )
    project = replace(project, settings=settings)
    index = build_numbering(
        project,
        numbering=settings.numbering,
        threshold=settings.numbering_threshold,
        overrides={
            "figure": settings.figure_numbering,
            "table": settings.table_numbering,
            "equation": settings.equation_numbering,
        },
    )
    stem = project.master.stem
    outputs = [render_docx(project, index, output_dir / f"{stem}.docx")]
    if settings.pdf:
        outputs.append(render_pdf(project, index, output_dir / f"{stem}.pdf"))
    return tuple(outputs)
