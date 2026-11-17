from __future__ import annotations

from pathlib import Path

import pytest

from tex2sto.cli import main
from tex2sto.diagnostics import Severity
from tex2sto.dialect import load_project
from tex2sto.validation import validate_project


def _project_with_content(project_dir: Path, content: str):
    master = project_dir / "main.tex"
    master.write_text(master.read_text().replace(r"\conclusion", content + "\n\\conclusion"))
    return load_project(master)


def test_valid_project_has_no_errors(project_dir: Path) -> None:
    diagnostics = validate_project(load_project(project_dir / "main.tex"))

    assert not diagnostics.has_errors


@pytest.mark.parametrize("operator", [r"\cdot", "·", "⋅", "∙", "*", "•"])
@pytest.mark.parametrize(
    "template",
    [
        "${expression}$",
        r"\[{expression}\]",
        r"\begin{{equation*}}{expression}\end{{equation*}}",
        r"\begin{{align*}}{expression}\end{{align*}}",
    ],
)
def test_dotted_multiplication_is_a_warning(
    project_dir: Path, operator: str, template: str
) -> None:
    project = _project_with_content(project_dir, template.format(expression=f"A = x {operator} B"))

    diagnostics = validate_project(project)
    warnings = [item for item in diagnostics.items if item.code == "T2S-W401"]

    assert not diagnostics.has_errors
    assert len(warnings) == 1
    assert warnings[0].severity is Severity.WARNING
    assert any(
        item.code == "T2S-W401" and item.severity is Severity.ERROR
        for item in diagnostics.with_strict_warnings()
    )


@pytest.mark.parametrize(
    "expression", ["A = xB", r"A = x \times B", "A = x × B", "A = 1.25B", r"A = x \ldots B"]
)
@pytest.mark.parametrize(
    "template",
    [
        "$\n{expression}\n$",
        r"\[{expression}\]",
        r"\begin{{equation*}}{expression}\end{{equation*}}",
        r"\begin{{align*}}{expression}\end{{align*}}",
    ],
)
def test_allowed_multiplication_has_no_warning(
    project_dir: Path, expression: str, template: str
) -> None:
    project = _project_with_content(project_dir, template.format(expression=expression))

    assert "T2S-W401" not in {item.code for item in validate_project(project).items}


def test_multiplication_warning_reports_operator_lines_and_honors_suppression(
    project_dir: Path,
) -> None:
    project = _project_with_content(
        project_dir,
        r"""
\[
\begin{aligned}
A &= x \cdot B + c \cdot D \\
% tex2sto: ignore=T2S-W401
E &= f \cdot G \\
H &= j \cdot K
\end{aligned}
\]
""",
    )

    warnings = [item for item in validate_project(project).items if item.code == "T2S-W401"]
    expected_lines = [
        number
        for number, line in enumerate(project.expanded_source.splitlines(), start=1)
        if line.startswith(("A &=", "H &="))
    ]
    assert [item.line for item in warnings] == expected_lines


def test_multiplication_warning_ignores_comments_and_escaped_dollars(project_dir: Path) -> None:
    project = _project_with_content(
        project_dir,
        r"""
% $A = x \cdot B$ · ⋅ ∙ * •
\begin{equation*}
A = xB % \cdot · ⋅ ∙ * •
\end{equation*}
\$ · ⋅ ∙ * • \$
""",
    )

    assert "T2S-W401" not in {item.code for item in validate_project(project).items}


def test_multiplication_warning_also_checks_abstract_math(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    master.write_text(
        master.read_text().replace("Рассмотрена система", r"$A = x \cdot B$. Рассмотрена система")
    )
    project = load_project(master)

    warnings = [item for item in validate_project(project).items if item.code == "T2S-W401"]
    assert len(warnings) == 1
    assert warnings[0].line == next(
        number
        for number, line in enumerate(project.expanded_source.splitlines(), start=1)
        if r"\cdot" in line
    )


def test_dotted_multiplication_fails_only_strict_check(project_dir: Path, capsys) -> None:
    master = project_dir / "main.tex"
    master.write_text(master.read_text().replace("x = y + 1", r"x = y \cdot 1"))

    assert main(["check", str(master)]) == 0
    assert "warning[T2S-W401]" in capsys.readouterr().err
    assert main(["check", str(master), "--strict"]) == 1
    assert "error[T2S-W401]" in capsys.readouterr().err


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


def test_longtable_requires_explicit_docx_break(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    table = r"""
Таблица~\ref{tab:long} содержит данные.
\begin{longtable}{ll}
\caption{Данные}
\label{tab:long}\\
\tablehead{Поле & Значение}
данные & результат \\
ещё данные & ещё результат \\
\end{longtable}
"""
    master.write_text(source.replace("\\conclusion", table + "\n\\conclusion"), encoding="utf-8")

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E420" for item in diagnostics.items)


def test_tablebreak_is_rejected_outside_longtable(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    master.write_text(
        source.replace("Получен результат.", "Получен результат.\n\\tablebreak"),
        encoding="utf-8",
    )

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E423" for item in diagnostics.items)


def test_rejects_unknown_bibliography_kind(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8").replace(
        "\\source{doe2025}{book}",
        "\\source{doe2025}{memo}",
    )
    master.write_text(source, encoding="utf-8")

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E504" for item in diagnostics.items)


def test_structured_bibliography_requires_kind_specific_fields(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    structured = r"""
\begin{bibsource}
\bibkey{article}
\bibkind{article}
\bibtitle{Статья}
\end{bibsource}
"""
    master.write_text(
        source.replace("\\begin{document}", structured + "\n\\begin{document}"),
        encoding="utf-8",
    )

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E506" for item in diagnostics.items)


def test_bibliography_fields_are_rejected_outside_source(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    master.write_text(
        source.replace("\\begin{document}", "\\bibtitle{Лишнее}\n\\begin{document}"),
        encoding="utf-8",
    )

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E104" for item in diagnostics.items)


def test_symbols_must_immediately_follow_numbered_equation(project_dir: Path) -> None:
    master = project_dir / "main.tex"
    source = master.read_text(encoding="utf-8")
    symbols = r"""
Промежуточный текст.
\begin{symbols}
\symbol{$x$}{значение}
\end{symbols}
"""
    master.write_text(
        source.replace("Источник~", symbols + "\nИсточник~"),
        encoding="utf-8",
    )

    diagnostics = validate_project(load_project(master))

    assert any(item.code == "T2S-E426" for item in diagnostics.items)


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
