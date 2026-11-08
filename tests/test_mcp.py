from __future__ import annotations

import asyncio
import shutil
import sys
from pathlib import Path

import pytest
from docx import Document
from mcp import Client, StdioServerParameters

from tex2sto.errors import ToolError as RenderToolError
from tex2sto.mcp_server import CONFIG_PATH, CONFIG_URI, DIALECT_PATH, DIALECT_URI, server

ROOT = Path(__file__).resolve().parents[1]


def test_packaged_dialect_matches_user_documentation() -> None:
    assert DIALECT_PATH.read_bytes() == (ROOT / "docs" / "dialect.md").read_bytes()
    assert CONFIG_PATH.read_bytes() == (ROOT / "docs" / "configuration.md").read_bytes()


def test_mcp_exposes_two_tools_and_complete_dialect_resource() -> None:
    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "get_dialect_docs",
                "build_docx",
                "check_pages",
            }

            help_result = await client.call_tool("get_dialect_docs")
            assert not help_result.is_error
            assert help_result.structured_content is not None
            assert "ограниченный диалект" in help_result.structured_content["summary"]
            assert help_result.structured_content["documentation_path"] == str(DIALECT_PATH)
            assert help_result.structured_content["documentation_uri"] == DIALECT_URI

            resources = await client.list_resources()
            assert {(str(item.uri), item.mime_type) for item in resources.resources} == {
                (DIALECT_URI, "text/markdown"),
                (CONFIG_URI, "text/markdown"),
            }
            full_docs = await client.read_resource(DIALECT_URI)
            assert full_docs.contents[0].text == DIALECT_PATH.read_text(encoding="utf-8")

    asyncio.run(exercise())


def test_mcp_entry_point_works_over_stdio() -> None:
    command = Path(sys.executable).with_name("tex2sto-mcp")
    assert command.is_file()

    async def exercise() -> None:
        async with Client(StdioServerParameters(command=str(command))) as client:
            result = await client.call_tool("get_dialect_docs")
            assert not result.is_error
            assert result.structured_content is not None
            assert result.structured_content["documentation_uri"] == DIALECT_URI

    asyncio.run(exercise())


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_mcp_builds_docx_with_cli_numbering_options(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(project_dir)

    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool(
                "build_docx",
                {
                    "source": "main.tex",
                    "output_dir": "output",
                    "numbering": "global",
                    "numbering_threshold": 7,
                    "figure_numbering": "section",
                    "table_numbering": "global",
                    "equation_numbering": "section",
                },
            )
            assert not result.is_error
            assert result.structured_content is not None
            assert result.structured_content["warnings"] == []
            docx_path = Path(result.structured_content["docx_path"])
            assert docx_path == (project_dir / "output" / "main.docx").resolve()
            assert docx_path.read_bytes().startswith(b"PK")
            document = Document(docx_path)
            paragraphs = [paragraph.text for paragraph in document.paragraphs]
            assert any("Рисунок 1.1" in paragraph for paragraph in paragraphs)
            assert any(
                "(1.1)" in cell.text
                for table in document.tables
                for row in table.rows
                for cell in row.cells
            )

    asyncio.run(exercise())


def test_mcp_rejects_validation_error_without_creating_output(project_dir: Path) -> None:
    source = project_dir / "main.tex"
    source.write_text(
        source.read_text(encoding="utf-8").replace("Получен результат.", r"\textbf{Результат}."),
        encoding="utf-8",
    )

    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool("build_docx", {"source": str(source)})
            assert result.is_error
            assert "T2S-E101" in result.content[0].text
            assert not (project_dir / "build" / "main.docx").exists()

    asyncio.run(exercise())


def test_mcp_reports_missing_source_as_tool_error(tmp_path: Path) -> None:
    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool("build_docx", {"source": str(tmp_path / "missing.tex")})
            assert result.is_error
            assert "master source does not exist" in result.content[0].text

    asyncio.run(exercise())


def test_mcp_reports_external_tool_failure(
    project_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable_pandoc() -> str:
        raise RenderToolError("required external tool is not available: pandoc")

    monkeypatch.setattr("tex2sto.renderers.docx._pandoc", unavailable_pandoc)

    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            result = await client.call_tool("build_docx", {"source": str(project_dir / "main.tex")})
            assert result.is_error
            assert "required external tool is not available: pandoc" in result.content[0].text
            assert not (project_dir / "build" / "main.docx").exists()

    asyncio.run(exercise())


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_mcp_returns_warnings_and_strict_mode_blocks_build(project_dir: Path) -> None:
    source = project_dir / "main.tex"
    source.write_text(
        source.read_text(encoding="utf-8").replace("Получен результат.", "Получено 3 результата."),
        encoding="utf-8",
    )

    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            normal = await client.call_tool("build_docx", {"source": str(source)})
            assert not normal.is_error
            assert normal.structured_content is not None
            assert any(
                item["code"] == "T2S-W103" and item["severity"] == "warning"
                for item in normal.structured_content["warnings"]
            )
            assert Path(normal.structured_content["docx_path"]).is_file()

            strict_output = project_dir / "strict-output"
            strict = await client.call_tool(
                "build_docx",
                {"source": str(source), "output_dir": str(strict_output), "strict": True},
            )
            assert strict.is_error
            assert "T2S-W103" in strict.content[0].text
            assert not (strict_output / "main.docx").exists()

    asyncio.run(exercise())


def test_mcp_post_render_limits_use_project_config(project_dir: Path, monkeypatch) -> None:
    from types import SimpleNamespace

    pdf = project_dir / "rendered.pdf"
    pdf.touch()
    (project_dir / "tex2sto.toml").write_text("[pages]\nmaximum=10\n[build]\nstrict=true")
    monkeypatch.setattr("tex2sto.validation.pages.require_tool", lambda _: "pdfinfo")
    monkeypatch.setattr(
        "tex2sto.validation.pages.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="Pages: 14\n"),
    )

    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            params = {"source": str(project_dir / "main.tex"), "rendered_pdf": str(pdf)}
            strict = await client.call_tool("check_pages", params)
            assert strict.is_error
            assert "T2S-W602" in strict.content[0].text
            normal = await client.call_tool("check_pages", {**params, "strict": False})
            assert not normal.is_error
            assert normal.structured_content["pages"] == 14
            assert normal.structured_content["warnings"][0]["code"] == "T2S-W602"

    asyncio.run(exercise())


@pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc is not installed")
def test_mcp_build_applies_config_and_explicit_overrides(project_dir: Path) -> None:
    (project_dir / "tex2sto.toml").write_text(
        '[build]\noutput_dir="configured"\n[numbering]\nfigure="section"\n'
        '[punctuation]\nseparator="en-dash"\n'
    )

    async def exercise() -> None:
        async with Client(server, raise_exceptions=True) as client:
            params = {"source": str(project_dir / "main.tex")}
            configured = await client.call_tool("build_docx", params)
            assert not configured.is_error
            path = Path(configured.structured_content["docx_path"])
            assert path.parent == project_dir / "configured"
            assert any("Рисунок 1.1 – " in p.text for p in Document(path).paragraphs)
            overridden = await client.call_tool(
                "build_docx", {**params, "figure_numbering": "global"}
            )
            assert not overridden.is_error
            assert any("Рисунок 1 – " in p.text for p in Document(path).paragraphs)

    asyncio.run(exercise())
