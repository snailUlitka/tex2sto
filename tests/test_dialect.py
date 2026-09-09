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
