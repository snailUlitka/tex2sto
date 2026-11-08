from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tex2sto.cli import main
from tex2sto.config import ProjectSettings, load_settings, override_settings
from tex2sto.dialect import load_project
from tex2sto.errors import SourceError
from tex2sto.validation import validate_project
from tex2sto.validation.pages import check_rendered_pages


def test_empty_and_absent_configuration_have_identical_defaults(tmp_path: Path) -> None:
    assert load_settings(tmp_path) == ProjectSettings()
    (tmp_path / "tex2sto.toml").write_text("")
    assert load_settings(tmp_path) == ProjectSettings()


@pytest.mark.parametrize(
    "text",
    [
        "unexpected = 1",
        "[build]\nunknown = true",
        '[numbering]\nmode = "invalid"',
        "[numbering]\nthreshold = true",
        "[numbering]\nthreshold = 0",
        "[layout]\ntable_line_spacing = nan",
        "[layout]\ntable_line_spacing = 0.5",
        '[structure]\nterminology_position = "anywhere"',
        '[punctuation]\nseparator = "em-dash"',
        "[pages]\nminimum = 30\nmaximum = 20",
        "[pages]\nmaximum = false",
        "[build]\nstrict = 1",
        "[build]\noutput_dir = ''",
        "[broken",
    ],
)
def test_reject_invalid_configuration(tmp_path: Path, text: str) -> None:
    (tmp_path / "tex2sto.toml").write_text(text)
    with pytest.raises(SourceError):
        load_settings(tmp_path)


def test_explicit_config_and_override_precedence(project_dir: Path, tmp_path: Path) -> None:
    config = tmp_path / "other.toml"
    config.write_text('[numbering]\nmode="section"\n[build]\nstrict=true')
    project = load_project(project_dir / "main.tex", config=config)
    assert project.settings.numbering == "section"
    assert project.settings.strict
    assert override_settings(project.settings, strict=False).strict is False
    assert main(["check", str(project.master), "--config", str(config), "--no-strict"]) == 0


def test_terminology_position_controls_validation(project_dir: Path) -> None:
    project = load_project(project_dir / "main.tex")
    project.body = project.body.replace("Получен результат.", "Получен результат.\n\\definitions\n")
    assert "T2S-E307" in {d.code for d in validate_project(project).items}
    project.settings = replace(project.settings, terminology_position="after-conclusion")
    assert "T2S-E307" not in {d.code for d in validate_project(project).items}
    project.body = project.body.replace("\\definitions", "") + "\n\\definitions"
    assert "T2S-E307" in {d.code for d in validate_project(project).items}


def test_dash_policy_is_configurable(project_dir: Path) -> None:
    project = load_project(project_dir / "main.tex")
    project.body += "\nТекст — пояснение."
    assert "T2S-W106" in {d.code for d in validate_project(project).items}
    project.settings = replace(project.settings, allow_em_dash=True)
    assert "T2S-W106" not in {d.code for d in validate_project(project).items}


@pytest.mark.parametrize(
    "bounds,codes",
    [
        ({}, set()),
        ({"minimum_pages": 25}, {"T2S-W601"}),
        ({"maximum_pages": 10}, {"T2S-W602"}),
        ({"minimum_pages": 20, "maximum_pages": 20}, set()),
    ],
)
def test_rendered_page_bounds(tmp_path: Path, monkeypatch, bounds, codes) -> None:
    pdf = tmp_path / "rendered.pdf"
    pdf.touch()
    monkeypatch.setattr("tex2sto.validation.pages.require_tool", lambda _: "pdfinfo")
    monkeypatch.setattr(
        "tex2sto.validation.pages.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="Pages: 20\n"),
    )
    count, bag = check_rendered_pages(pdf, replace(ProjectSettings(), **bounds))
    assert count == 20
    assert {d.code for d in bag.items} == codes


def test_page_limit_cli_strict_mode(project_dir: Path, tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "rendered.pdf"
    pdf.touch()
    (project_dir / "tex2sto.toml").write_text("[pages]\nminimum=25")
    monkeypatch.setattr("tex2sto.validation.pages.require_tool", lambda _: "pdfinfo")
    monkeypatch.setattr(
        "tex2sto.validation.pages.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="Pages: 14\n"),
    )
    args = ["check-pages", str(project_dir / "main.tex"), str(pdf)]
    assert main(args) == 0
    assert main([*args, "--strict"]) == 1
    monkeypatch.setattr(
        "tex2sto.validation.pages.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout=""),
    )
    assert main(args) == 2


def test_missing_explicit_configuration_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(SourceError, match="cannot read configuration"):
        load_settings(tmp_path, tmp_path / "missing.toml")
