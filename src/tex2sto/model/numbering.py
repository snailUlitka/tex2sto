"""Deterministic numbering for both renderers."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum

from tex2sto.dialect.syntax import find_command_calls, find_environment
from tex2sto.model.document import SourceProject

APPENDIX_LETTERS = tuple("АБВГДЕЖИКЛМНПРСТУФХЦШЩЭЮЯ")


class ObjectKind(StrEnum):
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"


class NumberingMode(StrEnum):
    AUTO = "auto"
    GLOBAL = "global"
    SECTION = "section"


@dataclass(frozen=True, slots=True)
class NumberedObject:
    kind: ObjectKind
    label: str
    position: int
    section: int | None
    appendix: int | None
    display: str


@dataclass(frozen=True, slots=True)
class NumberingIndex:
    objects: tuple[NumberedObject, ...]
    references: dict[str, str]
    modes: dict[ObjectKind, NumberingMode]
    citations: dict[str, int]


def _label(content: str) -> str | None:
    calls = find_command_calls(content, "label", 1)
    return calls[0].args[0].strip() if calls else None


def _context_at(
    position: int, sections: list[int], appendices: list[int]
) -> tuple[int | None, int | None]:
    appendix = sum(item < position for item in appendices)
    if appendix:
        return None, appendix
    section = sum(item < position for item in sections)
    return (section or None), None


def _appendix_letter(number: int) -> str:
    # V1 intentionally supports the normal single-letter appendix range.
    return APPENDIX_LETTERS[number - 1]


def _effective_mode(
    requested: NumberingMode,
    occurrences: list[tuple[int, str, int | None, int | None]],
    section_count: int,
    threshold: int,
) -> NumberingMode:
    if requested is not NumberingMode.AUTO:
        return requested
    sections = {section for _, _, section, appendix in occurrences if section and not appendix}
    main_count = sum(appendix is None for _, _, _, appendix in occurrences)
    if main_count >= threshold and section_count >= 2 and len(sections) >= 2:
        return NumberingMode.SECTION
    return NumberingMode.GLOBAL


def build_numbering(
    project: SourceProject,
    *,
    numbering: str = "auto",
    threshold: int = 10,
    overrides: dict[str, str | None] | None = None,
) -> NumberingIndex:
    """Build a shared numbering and citation index from source order."""
    source = project.body
    sections = [call.start for call in find_command_calls(source, "section", 1)]
    appendix_calls = find_command_calls(source, "appendix", 2)
    appendices = [call.start for call in appendix_calls]
    occurrences: dict[ObjectKind, list[tuple[int, str, int | None, int | None]]] = {
        kind: [] for kind in ObjectKind
    }
    environments = {
        ObjectKind.FIGURE: ("figure",),
        ObjectKind.TABLE: ("table", "longtable"),
        ObjectKind.EQUATION: ("equation", "align"),
    }
    for kind, names in environments.items():
        for name in names:
            for start, _, content in find_environment(source, name):
                label = _label(content)
                if label:
                    section, appendix = _context_at(start, sections, appendices)
                    occurrences[kind].append((start, label, section, appendix))
        occurrences[kind].sort()

    requested_default = NumberingMode(numbering)
    overrides = overrides or {}
    modes: dict[ObjectKind, NumberingMode] = {}
    for kind in ObjectKind:
        requested = NumberingMode(overrides.get(kind.value) or requested_default)
        modes[kind] = _effective_mode(requested, occurrences[kind], len(sections), threshold)

    objects: list[NumberedObject] = []
    references: dict[str, str] = {}
    for call_index, call in enumerate(appendix_calls, start=1):
        references[call.args[0].strip()] = _appendix_letter(call_index)

    for kind in ObjectKind:
        global_counter = 0
        section_counters: defaultdict[int, int] = defaultdict(int)
        appendix_counters: defaultdict[int, int] = defaultdict(int)
        for position, label, section, appendix in occurrences[kind]:
            if appendix is not None:
                appendix_counters[appendix] += 1
                display = f"{_appendix_letter(appendix)}.{appendix_counters[appendix]}"
            elif modes[kind] is NumberingMode.SECTION and section is not None:
                section_counters[section] += 1
                display = f"{section}.{section_counters[section]}"
            else:
                global_counter += 1
                display = str(global_counter)
            objects.append(NumberedObject(kind, label, position, section, appendix, display))
            references[label] = display

    citations: dict[str, int] = {}
    for call in find_command_calls(source, "cite", 1):
        for key in (part.strip() for part in call.args[0].split(",")):
            if key and key not in citations:
                citations[key] = len(citations) + 1
    ordered = tuple(sorted(objects, key=lambda item: item.position))
    return NumberingIndex(ordered, references, modes, citations)
