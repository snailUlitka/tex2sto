from __future__ import annotations

from pathlib import Path

import pytest

from tex2sto.dialect import load_project
from tex2sto.errors import SourceError


def test_loads_metadata_and_body(project_dir: Path) -> None:
    project = load_project(project_dir / "main.tex")

    assert project.metadata.author == "Иванов Иван Иванович"
    assert project.metadata.keywords[0] == "КОНТРОЛЬ"
    assert len(project.bibliography) == 1
    assert "\\section{Основная часть}" in project.body
    assert "\\source" not in project.body


def test_expands_inputs_inside_project(project_dir: Path) -> None:
    child = project_dir / "chapter.tex"
    child.write_text("Текст главы.", encoding="utf-8")
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    master.write_text(
        source.replace("Введение описывает задачу.", "\\input{chapter}"),
        encoding="utf-8",
    )

    project = load_project(master)

    assert "Текст главы." in project.body
    assert child in project.source_files


def test_rejects_input_escape(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    master.write_text(
        source.replace("Введение описывает задачу.", "\\input{../outside}"),
        encoding="utf-8",
    )

    with pytest.raises(SourceError, match="escapes the project root"):
        load_project(master)


def test_loads_named_structured_bibliography_fields(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    structured = r"""
\begin{bibsource}
\bibkey{site}
\bibkind{web}
\bibauthors{Организация}
\bibtitle{Официальный сайт}
\biburl{https://example.org}
\bibaccessdate{01.09.2026}
\end{bibsource}
"""
    master.write_text(
        source.replace("\\begin{document}", structured + "\n\\begin{document}"),
        encoding="utf-8",
    )

    project = load_project(master)

    assert project.bibliography[1].key == "site"
    assert project.bibliography[1].authors == "Организация"
    assert project.bibliography[1].access_date == "01.09.2026"
    assert "\\begin{bibsource}" not in project.body
