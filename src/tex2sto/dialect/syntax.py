"""Small parsing helpers for the deliberately restricted tex2sto dialect.

This module recognizes only balanced command arguments and named environments.
It is intentionally not a general TeX parser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from tex2sto.errors import SourceError

CONTROL_WORD_RE = re.compile(r"\\([A-Za-z@]+\*?)")


@dataclass(frozen=True, slots=True)
class CommandCall:
    name: str
    args: tuple[str, ...]
    start: int
    end: int
    line: int


def line_number(source: str, position: int) -> int:
    return source.count("\n", 0, position) + 1


def mask_comments(source: str) -> str:
    """Replace comments with spaces while preserving newlines and offsets."""
    chars = list(source)
    index = 0
    while index < len(chars):
        if chars[index] == "%" and (index == 0 or chars[index - 1] != "\\"):
            while index < len(chars) and chars[index] != "\n":
                chars[index] = " "
                index += 1
        else:
            index += 1
    return "".join(chars)


def _skip_space(source: str, position: int) -> int:
    while position < len(source) and source[position].isspace():
        position += 1
    return position


def _read_group(source: str, position: int, opening: str, closing: str) -> tuple[str, int]:
    if position >= len(source) or source[position] != opening:
        raise SourceError(f"expected '{opening}' at source offset {position}")
    depth = 1
    cursor = position + 1
    while cursor < len(source):
        char = source[cursor]
        if char == "\\":
            cursor += 2
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return source[position + 1 : cursor], cursor + 1
        cursor += 1
    line = line_number(source, position)
    raise SourceError(f"unclosed '{opening}' group starting on line {line}")


def find_command_calls(source: str, name: str, arity: int) -> list[CommandCall]:
    masked = mask_comments(source)
    pattern = re.compile(rf"\\{re.escape(name)}(?![A-Za-z@])")
    calls: list[CommandCall] = []
    for match in pattern.finditer(masked):
        cursor = match.end()
        args: list[str] = []
        try:
            for _ in range(arity):
                cursor = _skip_space(masked, cursor)
                _, end = _read_group(masked, cursor, "{", "}")
                args.append(source[cursor + 1 : end - 1])
                cursor = end
        except SourceError as error:
            line = line_number(source, match.start())
            raise SourceError(f"invalid \\{name} command on line {line}: {error}") from error
        calls.append(
            CommandCall(
                name,
                tuple(args),
                match.start(),
                cursor,
                line_number(source, match.start()),
            )
        )
    return calls


def parse_named_arguments(source: str) -> dict[str, str]:
    """Read a comma-separated key={value} list with balanced value groups."""
    source = mask_comments(source)
    values: dict[str, str] = {}
    cursor = _skip_space(source, 0)
    while cursor < len(source):
        key = re.match(r"([a-z][a-z-]*)\s*=\s*", source[cursor:])
        if key is None:
            raise SourceError("expected a named argument in the form key={value}")
        name = key.group(1)
        if name in values:
            raise SourceError(f"duplicate named argument: {name}")
        value, cursor = _read_group(source, cursor + key.end(), "{", "}")
        values[name] = value
        cursor = _skip_space(source, cursor)
        if cursor < len(source):
            if source[cursor] != ",":
                raise SourceError(f"expected a comma after named argument: {name}")
            cursor = _skip_space(source, cursor + 1)
    return values


def find_environment(source: str, name: str) -> list[tuple[int, int, str]]:
    masked = mask_comments(source)
    begin_re = re.compile(rf"\\begin\s*\{{{re.escape(name)}\}}")
    end_re = re.compile(rf"\\end\s*\{{{re.escape(name)}\}}")
    results: list[tuple[int, int, str]] = []
    position = 0
    while begin := begin_re.search(masked, position):
        end = end_re.search(masked, begin.end())
        if end is None:
            line = line_number(source, begin.start())
            raise SourceError(f"environment '{name}' opened on line {line} is not closed")
        results.append((begin.start(), end.end(), source[begin.end() : end.start()]))
        position = end.end()
    return results


def replace_spans(source: str, replacements: list[tuple[int, int, str]]) -> str:
    result = source
    for start, end, value in sorted(replacements, reverse=True):
        result = result[:start] + value + result[end:]
    return result


def control_words(source: str) -> list[tuple[str, int]]:
    masked = mask_comments(source)
    return [
        (match.group(1), line_number(source, match.start()))
        for match in CONTROL_WORD_RE.finditer(masked)
    ]
