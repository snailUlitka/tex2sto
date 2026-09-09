from __future__ import annotations

from pathlib import Path

from tex2sto.dialect import load_project
from tex2sto.model.numbering import NumberingMode, ObjectKind, build_numbering


def test_auto_numbering_uses_global_below_threshold(project_dir: Path) -> None:
    index = build_numbering(load_project(project_dir / "main.tex"), threshold=10)

    assert index.references["fig:scheme"] == "1"
    assert index.references["eq:model"] == "1"
    assert index.modes[ObjectKind.FIGURE] is NumberingMode.GLOBAL
    assert index.citations == {"doe2025": 1}


def test_override_uses_section_numbering(project_dir: Path) -> None:
    index = build_numbering(
        load_project(project_dir / "main.tex"),
        overrides={"figure": "section"},
    )

    assert index.references["fig:scheme"] == "1.1"
