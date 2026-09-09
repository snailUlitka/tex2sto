from __future__ import annotations

from pathlib import Path

from tex2sto.diagnostics import Severity
from tex2sto.dialect import load_project
from tex2sto.validation import validate_project


def test_valid_project_has_no_errors(project_dir: Path) -> None:
    diagnostics = validate_project(load_project(project_dir / "main.tex"))

    assert not diagnostics.has_errors


def test_unknown_command_is_an_error(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    master.write_text(
        source.replace("Получен результат.", "\\textbf{Результат}."),
        encoding="utf-8",
    )

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E101" for item in diagnostics.items)


def test_warning_can_be_promoted_or_suppressed(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    original = master.read_text(encoding="utf-8")
    master.write_text(
        original.replace("Получен результат.", "Получено 3 результата."),
        encoding="utf-8",
    )
    diagnostics = validate_project(load_project(master))
    assert any(item.code == "T2S-W103" for item in diagnostics.items)
    assert any(item.severity is Severity.ERROR for item in diagnostics.with_strict_warnings())

    master.write_text(
        original.replace(
            "Получен результат.",
            "% tex2sto: ignore=T2S-W103\nПолучено 3 результата.",
        ),
        encoding="utf-8",
    )
    suppressed = validate_project(load_project(master))
    assert all(item.code != "T2S-W103" for item in suppressed.items)
