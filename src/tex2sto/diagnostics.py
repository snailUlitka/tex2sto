"""Structured diagnostics emitted by dialect validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    message: str
    severity: Severity
    path: Path | None = None
    line: int | None = None

    def format(self) -> str:
        location = ""
        if self.path is not None:
            location = str(self.path)
            if self.line is not None:
                location += f":{self.line}"
            location += ": "
        return f"{location}{self.severity.value}[{self.code}]: {self.message}"


class DiagnosticBag:
    def __init__(self) -> None:
        self._items: list[Diagnostic] = []

    @property
    def items(self) -> tuple[Diagnostic, ...]:
        return tuple(self._items)

    @property
    def has_errors(self) -> bool:
        return any(item.severity is Severity.ERROR for item in self._items)

    def error(
        self,
        code: str,
        message: str,
        *,
        path: Path | None = None,
        line: int | None = None,
    ) -> None:
        self._items.append(Diagnostic(code, message, Severity.ERROR, path, line))

    def warning(
        self,
        code: str,
        message: str,
        *,
        path: Path | None = None,
        line: int | None = None,
    ) -> None:
        self._items.append(Diagnostic(code, message, Severity.WARNING, path, line))

    def with_strict_warnings(self) -> tuple[Diagnostic, ...]:
        return tuple(
            Diagnostic(item.code, item.message, Severity.ERROR, item.path, item.line)
            if item.severity is Severity.WARNING
            else item
            for item in self._items
        )
