"""External tool discovery and execution."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tex2sto.errors import ToolError


def require_tool(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise ToolError(f"required external tool is not available: {name}")
    return executable


def run_tool(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stdout.strip()[-6000:]
        raise ToolError(f"external tool failed ({command[0]}):\n{detail}")


def require_version(command: list[str], expected: str, *, label: str) -> None:
    completed = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0 or expected not in completed.stdout:
        actual = completed.stdout.strip().splitlines()
        summary = actual[0] if actual else "unavailable"
        raise ToolError(f"{label} version mismatch: expected {expected!r}, got {summary!r}")
