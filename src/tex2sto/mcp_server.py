"""Local MCP interface for dialect guidance and DOCX builds."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from tex2sto.build import BuildOptions, build_project
from tex2sto.diagnostics import Diagnostic, Severity
from tex2sto.dialect import load_project
from tex2sto.errors import Tex2StoError
from tex2sto.validation import validate_project
from tex2sto.version import __version__

DIALECT_URI = "tex2sto://dialect/v1"
DIALECT_PATH = Path(__file__).resolve().parent / "resources" / "dialect.md"
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


class BuildDocxResult(TypedDict):
    docx_path: str
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
            "и окружение document. Обязательны введение, хотя бы один раздел и "
            "заключение. Поддерживаются структурные заголовки, списки, рисунки, "
            "таблицы, формулы, источники, приложения и локальные \\input. "
            "Неизвестные команды и окружения вызывают ошибку. Полный перечень "
            "команд и ограничений доступен в указанном файле или MCP-ресурсе."
        ),
        "documentation_path": str(DIALECT_PATH),
        "documentation_uri": DIALECT_URI,
    }


@server.resource(
    DIALECT_URI,
    name="tex2sto dialect v1",
    description="Complete documentation of the supported tex2sto v1 LaTeX dialect.",
    mime_type="text/markdown",
)
def dialect_documentation() -> str:
    """Read the complete supported-dialect documentation."""
    return DIALECT_PATH.read_text(encoding="utf-8")


@server.tool()
def build_docx(
    source: str,
    output_dir: str | None = None,
    strict: bool = False,
    numbering: NumberingMode = "auto",
    numbering_threshold: int = 10,
    figure_numbering: NumberingMode | None = None,
    table_numbering: NumberingMode | None = None,
    equation_numbering: NumberingMode | None = None,
) -> BuildDocxResult:
    """Validate a master .tex project and build its editable DOCX file."""
    try:
        project = load_project(Path(source))
    except (Tex2StoError, OSError) as error:
        raise ToolError(str(error)) from error
    bag = validate_project(project)
    diagnostics = bag.with_strict_warnings() if strict else bag.items
    errors = [item for item in diagnostics if item.severity is Severity.ERROR]
    if errors:
        raise ToolError("\n".join(item.format() for item in diagnostics))

    destination = (
        Path(output_dir).expanduser() if output_dir is not None else project.root / "build"
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
        (docx_path,) = build_project(project, options)
    except (Tex2StoError, OSError) as error:
        raise ToolError(str(error)) from error
    return {
        "docx_path": str(docx_path),
        "warnings": [_diagnostic_data(item) for item in diagnostics],
    }


def main() -> None:
    """Run the local MCP server over standard input and output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
