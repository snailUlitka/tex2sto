"""Load a master source and safely expand restricted input commands."""

from __future__ import annotations

from pathlib import Path

from tex2sto.dialect.metadata import parse_project_source
from tex2sto.dialect.syntax import find_command_calls, replace_spans
from tex2sto.errors import SourceError
from tex2sto.model import SourceProject


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_input(value: str, *, parent: Path, root: Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        raise SourceError(f"absolute input path is forbidden: {value}")
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".tex")
    resolved = (parent / candidate).resolve()
    if not _inside(resolved, root):
        raise SourceError(f"input path escapes the project root: {value}")
    if not resolved.is_file():
        raise SourceError(f"input file does not exist: {value}")
    return resolved


def _expand(path: Path, *, root: Path, stack: tuple[Path, ...], seen: list[Path]) -> str:
    if path in stack:
        cycle = " -> ".join(item.name for item in (*stack, path))
        raise SourceError(f"input cycle detected: {cycle}")
    source = path.read_text(encoding="utf-8")
    seen.append(path)
    replacements: list[tuple[int, int, str]] = []
    for call in find_command_calls(source, "input", 1):
        child = _resolve_input(call.args[0].strip(), parent=path.parent, root=root)
        expanded = _expand(child, root=root, stack=(*stack, path), seen=seen)
        replacement = f"\n% tex2sto input: {child.name}\n{expanded}\n"
        replacements.append((call.start, call.end, replacement))
    return replace_spans(source, replacements)


def load_project(master: Path) -> SourceProject:
    master = master.expanduser().resolve()
    if not master.is_file():
        raise SourceError(f"master source does not exist: {master}")
    if master.suffix.lower() != ".tex":
        raise SourceError("master source must use the .tex extension")
    root = master.parent
    seen: list[Path] = []
    expanded = _expand(master, root=root, stack=(), seen=seen)
    metadata, body, bibliography = parse_project_source(expanded)
    return SourceProject(
        master=master,
        root=root,
        expanded_source=expanded,
        body=body,
        metadata=metadata,
        bibliography=bibliography,
        source_files=tuple(dict.fromkeys(seen)),
    )
