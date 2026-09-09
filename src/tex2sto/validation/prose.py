"""Conservative mechanical prose checks derived from the SSAU profile."""

from __future__ import annotations

import re
from pathlib import Path

from tex2sto.diagnostics import DiagnosticBag

IGNORE_RE = re.compile(r"%\s*tex2sto:\s*ignore=([A-Za-z0-9_.,-]+)\s*$")
UNITS = "мм|см|м|км|мг|г|кг|с|мин|ч|Гц|кГц|МГц|В|А|Вт|Па|К|°C"


def _suppressed_lines(source: str) -> dict[int, set[str]]:
    suppressed: dict[int, set[str]] = {}
    pending: set[str] = set()
    for line_number, line in enumerate(source.splitlines(), start=1):
        match = IGNORE_RE.search(line)
        if match:
            pending.update(code.strip() for code in match.group(1).split(",") if code.strip())
            continue
        stripped = line.strip()
        if pending and stripped and not stripped.startswith("%"):
            suppressed[line_number] = pending
            pending = set()
    return suppressed


def _plain_text_line(line: str) -> str:
    line = re.sub(r"%.*$", "", line)
    line = re.sub(r"\$[^$]*\$", "", line)
    line = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^]]*\])?", "", line)
    line = line.replace("{", "").replace("}", "")
    return line


def check_prose(source: str, *, path: Path, diagnostics: DiagnosticBag) -> None:
    suppressed = _suppressed_lines(source)
    checks: tuple[tuple[str, re.Pattern[str], str], ...] = (
        (
            "T2S-W101",
            re.compile(r"(?<!\d)(?:%|№)|(?:[<>≈≠≤≥=])(?!\s*\d)"),
            "a mathematical sign, percent sign, or number sign may be detached from a value",
        ),
        (
            "T2S-W102",
            re.compile(r"(?<![\w])[-−]\s*\d"),
            "negative values in prose should normally use the word 'минус'",
        ),
        (
            "T2S-W103",
            re.compile(rf"\b[1-9]\b(?!\s*(?:{UNITS})\b)"),
            "numbers from one through nine without a unit should normally be written as words",
        ),
        (
            "T2S-W104",
            re.compile(rf"\d\s+(?:{UNITS})\b"),
            "a number and its unit should use a non-breaking space (~)",
        ),
        (
            "T2S-W105",
            re.compile(r"\b\d+\.\d+\b"),
            "Russian prose should normally use a decimal comma",
        ),
    )
    in_display_math = False
    in_verbatim = False
    for line_number, raw_line in enumerate(source.splitlines(), start=1):
        if "\\begin{verbatim}" in raw_line:
            in_verbatim = True
        if "\\[" in raw_line or "\\begin{equation}" in raw_line:
            in_display_math = True
        if not in_display_math and not in_verbatim:
            plain = _plain_text_line(raw_line)
            for code, pattern, message in checks:
                if code not in suppressed.get(line_number, set()) and pattern.search(plain):
                    diagnostics.warning(code, message, path=path, line=line_number)
        if "\\]" in raw_line or "\\end{equation}" in raw_line:
            in_display_math = False
        if "\\end{verbatim}" in raw_line:
            in_verbatim = False
