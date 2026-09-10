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


def test_math_command_is_rejected_in_prose(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    master.write_text(
        source.replace("Получен результат.", "Получен \\underline{результат}."),
        encoding="utf-8",
    )

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E103" for item in diagnostics.items)


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


def test_longtable_requires_semantic_header(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    table = r"""
Таблица~\ref{tab:long} содержит данные.
\begin{longtable}{ll}
\caption{Данные}
\label{tab:long}\\
Поле & Значение \\
данные & результат \\
\end{longtable}
"""
    master.write_text(source.replace("\\conclusion", table + "\n\\conclusion"), encoding="utf-8")

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E413" for item in diagnostics.items)


def test_rejects_unknown_bibliography_kind(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8").replace(
        "\\source{doe2025}{book}",
        "\\source{doe2025}{memo}",
    )
    master.write_text(source, encoding="utf-8")

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E504" for item in diagnostics.items)


def test_object_must_follow_its_first_reference(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    reference = "Как показано на рисунке~\\ref{fig:scheme}, результат подтверждает модель.\n"
    source = source.replace(reference, "")
    master.write_text(source.replace("Уравнение", reference + "Уравнение"), encoding="utf-8")

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E416" for item in diagnostics.items)


def test_section_title_must_be_uppercase_without_period(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8").replace(
        "\\section{Основная часть}",
        "\\section{основная часть.}",
    )
    master.write_text(source, encoding="utf-8")

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E308" for item in diagnostics.items)
    assert any(item.code == "T2S-E309" for item in diagnostics.items)
