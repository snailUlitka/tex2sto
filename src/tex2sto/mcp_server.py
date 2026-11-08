"""Local MCP interface for dialect guidance and DOCX builds."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from tex2sto.build import BuildOptions, build_project
from tex2sto.config import override_settings
from tex2sto.diagnostics import Diagnostic, Severity
from tex2sto.dialect import load_project
from tex2sto.errors import Tex2StoError
from tex2sto.validation import validate_project
from tex2sto.validation.pages import check_rendered_pages
from tex2sto.version import __version__

DIALECT_URI = "tex2sto://dialect/v2"
DIALECT_PATH = Path(__file__).resolve().parent / "resources" / "dialect.md"
CONFIG_URI = "tex2sto://configuration/v2"
CONFIG_PATH = Path(__file__).resolve().parent / "resources" / "configuration.md"
NumberingMode = Literal["auto", "global", "section"]


class DiagnosticInfo(TypedDict):
    code: str
    severity: str
    message: str
    path: str | None
    line: int | None


class DialectDocsResult(TypedDict):
    summary: str
    documentation_path: str
    documentation_uri: str
    configuration_uri: str


class BuildDocxResult(TypedDict):
    docx_path: str
    outputs: list[str]
    warnings: list[DiagnosticInfo]


class PageCheckResult(TypedDict):
    pages: int
    warnings: list[DiagnosticInfo]


server = MCPServer(
    "tex2sto",
    description="Build editable SSAU DOCX documents from the documented tex2sto LaTeX dialect.",
    version=__version__,
)


def _diagnostic_data(diagnostic: Diagnostic) -> DiagnosticInfo:
    return {
        "code": diagnostic.code,
        "severity": diagnostic.severity.value,
        "message": diagnostic.message,
        "path": str(diagnostic.path) if diagnostic.path is not None else None,
        "line": diagnostic.line,
    }


@server.tool()
def get_dialect_docs() -> DialectDocsResult:
    """Get a short guide to the supported LaTeX dialect and the full documentation location."""
    return {
        "summary": (
            "tex2sto принимает ограниченный диалект LaTeX для документов Самарского "
            "университета. Главный файл содержит \\documentclass{tex2sto}, метаданные "
            "и окружение document. Для лабораторной титульник задаётся одной "
            "командой \\labtitle{number={...}, course={...}, author={...}, group={...}, "
            "reviewer={...}, year={...}}; обязателен хотя бы один раздел. "
            "Для ВКР также обязательны введение, реферат и заключение. "
            "Для практики используйте \\practicetitle и строки \\practiceassignment. "
            "Настройки проекта задаются в tex2sto.toml рядом с главным исходником. "
            "Поддерживаются структурные заголовки, списки, рисунки, "
            "таблицы, формулы, источники, приложения и локальные \\input. "
            "Неизвестные команды и окружения вызывают ошибку. Полный перечень "
            "команд и ограничений доступен в указанном файле или MCP-ресурсе."
        ),
        "documentation_path": str(DIALECT_PATH),
        "documentation_uri": DIALECT_URI,
        "configuration_uri": CONFIG_URI,
    }


@server.resource(
    DIALECT_URI,
    name="tex2sto dialect v2",
    description="Complete documentation of the supported tex2sto 2.0 LaTeX dialect.",
    mime_type="text/markdown",
)
def dialect_documentation() -> str:
    """Read the complete supported-dialect documentation."""
    return DIALECT_PATH.read_text(encoding="utf-8")


@server.resource(
    CONFIG_URI,
    name="tex2sto configuration v2",
    description="Complete project configuration documentation and defaults.",
    mime_type="text/markdown",
)
def configuration_documentation() -> str:
    """Read the packaged project configuration reference."""
    return CONFIG_PATH.read_text(encoding="utf-8")


@server.tool()
def build_docx(
    source: str,
    output_dir: str | None = None,
    strict: bool | None = None,
    numbering: NumberingMode | None = None,
    numbering_threshold: int | None = None,
    figure_numbering: NumberingMode | None = None,
    table_numbering: NumberingMode | None = None,
    equation_numbering: NumberingMode | None = None,
    config: str | None = None,
) -> BuildDocxResult:
    """Validate a master .tex project and build its editable DOCX file."""
    try:
        project = load_project(Path(source), config=Path(config) if config else None)
        project.settings = override_settings(
            project.settings,
            strict=strict,
            numbering=numbering,
            numbering_threshold=numbering_threshold,
            figure_numbering=figure_numbering,
            table_numbering=table_numbering,
            equation_numbering=equation_numbering,
        )
    except (Tex2StoError, OSError) as error:
        raise ToolError(str(error)) from error
    bag = validate_project(project)
    diagnostics = bag.with_strict_warnings() if project.settings.strict else bag.items
    errors = [item for item in diagnostics if item.severity is Severity.ERROR]
    if errors:
        raise ToolError("\n".join(item.format() for item in diagnostics))

    destination = (
        Path(output_dir).expanduser()
        if output_dir is not None
        else project.root / project.settings.output_dir
    )
    options = BuildOptions(
        output_dir=destination,
        numbering=numbering,
        numbering_threshold=numbering_threshold,
        figure_numbering=figure_numbering,
        table_numbering=table_numbering,
        equation_numbering=equation_numbering,
    )
    try:
        outputs = build_project(project, options)
        docx_path = outputs[0]
    except (Tex2StoError, OSError) as error:
        raise ToolError(str(error)) from error
    return {
        "docx_path": str(docx_path),
        "outputs": [str(path) for path in outputs],
        "warnings": [_diagnostic_data(item) for item in diagnostics],
    }


@server.tool()
def check_pages(
    source: str, rendered_pdf: str, config: str | None = None, strict: bool | None = None
) -> PageCheckResult:
    """Check configured page bounds against an already rendered PDF; never render DOCX."""
    try:
        project = load_project(Path(source), config=Path(config) if config else None)
        settings = override_settings(project.settings, strict=strict)
        count, bag = check_rendered_pages(Path(rendered_pdf), settings)
        diagnostics = bag.with_strict_warnings() if settings.strict else bag.items
        if any(item.severity is Severity.ERROR for item in diagnostics):
            raise ToolError("\n".join(item.format() for item in diagnostics))
        return {"pages": count, "warnings": [_diagnostic_data(item) for item in diagnostics]}
    except (Tex2StoError, OSError) as error:
        raise ToolError(str(error)) from error


def main() -> None:
    """Run the local MCP server over standard input and output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
