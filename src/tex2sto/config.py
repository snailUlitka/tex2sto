"""Strict project configuration shared by the CLI, MCP, and renderers."""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass, fields, replace
from pathlib import Path

from tex2sto.errors import SourceError


@dataclass(frozen=True, slots=True)
class ProjectSettings:
    output_dir: str = "build"
    pdf: bool = False
    strict: bool = False
    numbering: str = "auto"
    numbering_threshold: int = 10
    figure_numbering: str | None = None
    table_numbering: str | None = None
    equation_numbering: str | None = None
    table_line_spacing: float = 1.5
    terminology_position: str = "before-introduction"
    separator: str = "hyphen"
    allow_em_dash: bool = False
    list_marker: str = "hyphen"
    list_numbering: str = "hierarchical"
    minimum_pages: int | None = None
    maximum_pages: int | None = None

    @property
    def separator_text(self) -> str:
        return {"hyphen": "-", "en-dash": "–", "em-dash": "—"}[self.separator]


SCHEMA = {
    "build": {"output_dir": "output_dir", "pdf": "pdf", "strict": "strict"},
    "numbering": {
        "mode": "numbering",
        "threshold": "numbering_threshold",
        "figure": "figure_numbering",
        "table": "table_numbering",
        "equation": "equation_numbering",
    },
    "layout": {"table_line_spacing": "table_line_spacing"},
    "structure": {"terminology_position": "terminology_position"},
    "punctuation": {"separator": "separator", "allow_em_dash": "allow_em_dash"},
    "lists": {"marker": "list_marker", "numbering": "list_numbering"},
    "pages": {"minimum": "minimum_pages", "maximum": "maximum_pages"},
}


def validate_settings(settings: ProjectSettings) -> ProjectSettings:
    for name in ("pdf", "strict", "allow_em_dash"):
        if type(getattr(settings, name)) is not bool:
            raise SourceError(f"configuration {name} must be a boolean")
    if not isinstance(settings.output_dir, str) or not settings.output_dir.strip():
        raise SourceError("configuration output_dir must be a nonempty string")
    choices = {
        "numbering": {"auto", "global", "section"},
        "figure_numbering": {None, "auto", "global", "section"},
        "table_numbering": {None, "auto", "global", "section"},
        "equation_numbering": {None, "auto", "global", "section"},
        "terminology_position": {"before-introduction", "after-conclusion"},
        "separator": {"hyphen", "en-dash", "em-dash"},
        "list_marker": {"hyphen", "en-dash", "em-dash"},
        "list_numbering": {"hierarchical", "decimal"},
    }
    for name, allowed in choices.items():
        value = getattr(settings, name)
        if not isinstance(value, (str, type(None))) or value not in allowed:
            raise SourceError(f"invalid configuration {name}: {value!r}")
    for name in ("numbering_threshold", "minimum_pages", "maximum_pages"):
        value = getattr(settings, name)
        if value is None and name != "numbering_threshold":
            continue
        if type(value) is not int or value < 1:
            raise SourceError(f"configuration {name} must be a positive integer")
    spacing = settings.table_line_spacing
    if type(spacing) not in (int, float) or not math.isfinite(spacing) or not 1 <= spacing <= 3:
        raise SourceError("configuration table_line_spacing must be between 1 and 3")
    if (
        settings.minimum_pages is not None
        and settings.maximum_pages is not None
        and settings.minimum_pages > settings.maximum_pages
    ):
        raise SourceError("configuration minimum_pages must not exceed maximum_pages")
    if "em-dash" in (settings.separator, settings.list_marker) and not settings.allow_em_dash:
        raise SourceError("em-dash separators/markers require punctuation.allow_em_dash = true")
    return settings


def override_settings(settings: ProjectSettings, **values) -> ProjectSettings:
    known = {item.name for item in fields(ProjectSettings)}
    unknown = values.keys() - known
    if unknown:
        raise SourceError(f"unknown configuration overrides: {', '.join(sorted(unknown))}")
    return validate_settings(
        replace(settings, **{k: v for k, v in values.items() if v is not None})
    )


def load_settings(root: Path, config: Path | None = None) -> ProjectSettings:
    path = config.expanduser().resolve() if config is not None else root / "tex2sto.toml"
    if not path.exists() and config is None:
        return ProjectSettings()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SourceError(f"cannot read configuration {path}: {error}") from error
    values = {}
    for section, entries in data.items():
        if section not in SCHEMA or not isinstance(entries, dict):
            raise SourceError(f"unknown configuration section or invalid table: {section}")
        for key, value in entries.items():
            if key not in SCHEMA[section]:
                raise SourceError(f"unknown configuration key: {section}.{key}")
            values[SCHEMA[section][key]] = value
    return override_settings(ProjectSettings(), **values)
