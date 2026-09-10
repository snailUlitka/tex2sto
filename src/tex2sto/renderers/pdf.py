"""LuaLaTeX PDF renderer."""

from __future__ import annotations

import os
import shutil
import tempfile
import tomllib
from importlib.resources import files
from pathlib import Path

from tex2sto.dialect.syntax import find_command_calls
from tex2sto.model import NumberingIndex, ObjectKind, SourceProject
from tex2sto.renderers.tools import require_tool, require_version, run_tool
from tex2sto.transform import PAGE_BREAK_MARKER, renderer_body

CLASS_DIR = files("tex2sto") / "profiles" / "ssau" / "latex"


def _lualatex() -> str:
    executable = require_tool("lualatex")
    tlmgr = require_tool("tlmgr")
    configuration = tomllib.loads((CLASS_DIR.parent / "toolchain.toml").read_text())
    require_version(
        [tlmgr, "--version"],
        f"version {configuration['tex-live']}",
        label="TeX Live",
    )
    return executable


def _escape(value: str) -> str:
    return value.replace("&", r"\&").replace("#", r"\#").replace("_", r"\_")


def _front_matter(project: SourceProject, index: NumberingIndex) -> str:
    metadata = project.metadata
    counts = {kind: sum(item.kind is kind for item in index.objects) for kind in ObjectKind}
    appendices = len(find_command_calls(project.body, "appendix", 2))
    keywords = _escape(", ".join(keyword.upper() for keyword in metadata.keywords))
    title_commands = "\n".join(
        f"\\{command}{{{_escape(value)}}}"
        for command, value in (
            ("texinstitute", metadata.institute),
            ("texdepartment", metadata.department),
            ("textitle", metadata.title),
            ("texprogramcode", metadata.program_code),
            ("texprogramname", metadata.program_name),
            ("texstudyprofile", metadata.study_profile),
            ("texauthor", metadata.author),
            ("texstudentgroup", metadata.student_group),
            ("texsupervisordetails", metadata.supervisor_details),
            ("texsupervisor", metadata.supervisor_name),
            ("texcity", metadata.city),
            ("texyear", metadata.year),
        )
    )
    assignment = ""
    if metadata.assignment_variant != "none":
        assignment = rf"""
\texassignment{{{_escape(metadata.assignment_approver)}}}{{{_escape(metadata.assignment_goal)}}}{{{_escape(metadata.assignment_questions)}}}{{{_escape(metadata.assignment_issued)}}}{{{_escape(metadata.assignment_due)}}}
"""
        if metadata.assignment_variant == "2":
            assignment += r"\texassignmentcontinuation" + "\n"
    return rf"""
{title_commands}
\textitlepage
{assignment}
\texabstract{{{counts[ObjectKind.FIGURE]}}}{{{counts[ObjectKind.TABLE]}}}{{{len(project.bibliography)}}}{{{appendices}}}{{{keywords}}}{{{metadata.abstract}}}
\tableofcontents
"""


def _document_source(project: SourceProject, index: NumberingIndex) -> str:
    body = renderer_body(project, index, target="pdf").replace(PAGE_BREAK_MARKER, r"\clearpage")
    return (
        "\\documentclass{tex2sto-ssau}\n"
        "\\begin{document}\n"
        + _front_matter(project, index)
        + body
        + "\n\\label{LastPage}\n\\end{document}\n"
    )


def render_pdf(project: SourceProject, index: NumberingIndex, output: Path) -> Path:
    lualatex = _lualatex()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tex2sto-pdf-") as temporary:
        temporary_path = Path(temporary)
        source = temporary_path / "document.tex"
        source.write_text(_document_source(project, index), encoding="utf-8")
        environment = os.environ.copy()
        environment["TEXINPUTS"] = f"{CLASS_DIR}{os.pathsep}" + environment.get("TEXINPUTS", "")
        command = [
            lualatex,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={temporary_path}",
            str(source),
        ]
        for _ in range(3):
            run_tool(command, cwd=project.root, env=environment)
        shutil.copy2(temporary_path / "document.pdf", output)
    return output
