"""Core data structures shared by validation and renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tex2sto.config import ProjectSettings


@dataclass(frozen=True, slots=True)
class Consultant:
    name: str
    role: str


@dataclass(frozen=True, slots=True)
class BibliographyItem:
    key: str
    kind: str
    title: str
    authors: str = ""
    medium: str = ""
    contributors: str = ""
    container: str = ""
    place: str = ""
    publisher: str = ""
    year: str = ""
    issue: str = ""
    pages: str = ""
    url: str = ""
    access_date: str = ""
    details: str = ""


@dataclass(slots=True)
class DocumentMetadata:
    lab_title: LabTitle | None = None
    practice_title: PracticeTitle | None = None
    practice_assignments: list[PracticeAssignment] = field(default_factory=list)
    title: str = ""
    author: str = ""
    student_group: str = ""
    institute: str = ""
    faculty: str = ""
    department: str = ""
    program_code: str = ""
    program_name: str = ""
    study_profile: str = ""
    supervisor_name: str = ""
    supervisor_details: str = ""
    consultants: list[Consultant] = field(default_factory=list)
    norm_controller: str = ""
    city: str = "Самара"
    year: str = ""
    keywords: tuple[str, ...] = ()
    abstract: str = ""
    assignment_variant: str = "none"
    assignment_approver: str = ""
    assignment_goal: str = ""
    assignment_questions: str = ""
    assignment_issued: str = ""
    assignment_due: str = ""


@dataclass(frozen=True, slots=True)
class LabTitle:
    number: str
    course: str
    author: str
    group: str
    reviewer: str
    year: str
    variant: str = ""
    city: str = "Самара"
    author_label: str = "Выполнил"
    reviewer_label: str = "Проверил"


@dataclass(frozen=True, slots=True)
class PracticeTitle:
    kind: str
    type: str
    start: str
    end: str
    order_date: str
    order_number: str
    organization: str
    author_dative: str
    study_level: str = "магистратуры"
    submitted: str = ""
    defended: str = ""
    grade: str = ""


@dataclass(frozen=True, slots=True)
class PracticeAssignment:
    competency: str
    outcomes: str
    task: str


@dataclass(slots=True)
class SourceProject:
    master: Path
    root: Path
    expanded_source: str
    body: str
    metadata: DocumentMetadata
    bibliography: list[BibliographyItem]
    source_files: tuple[Path, ...]
    settings: ProjectSettings = field(default_factory=ProjectSettings)
