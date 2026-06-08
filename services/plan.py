"""Domain rules for GenPal question-bank generation planning.

Defines career levels, generation modes, per-mode complexity distributions,
and helpers used by the landing page to validate input and preview the
expected output before any generation runs.
"""

from __future__ import annotations

from dataclasses import dataclass

CAREER_LEVELS = ("ASE", "SE", "SSE", "TL", "AM", "M", "SM")

PROTOTYPE_MODE = "Prototype Mode"
FULL_MODE = "Full GenPal Mode"
GENERATION_MODES = (PROTOTYPE_MODE, FULL_MODE)

MAX_PROTOTYPE_LEVELS = 3

DEFAULT_PROTOTYPE_LEVELS = ("ASE", "SE")

EXCEL_SHEET_NAME = "Sheet1"
EXCEL_COLUMN_COUNT = 11

# questions per career level, per mode
_PROTOTYPE_PER_LEVEL = 40
_FULL_PER_LEVEL = 36

# complexity distribution per career level, per mode (must sum to per-level count)
_PROTOTYPE_COMPLEXITY = {
    "Basic": 5,
    "Intermediate": 6,
    "Advanced": 7,
    "Proficient": 11,
    "Expert": 11,
}
_FULL_COMPLEXITY = {
    "Basic": 4,
    "Intermediate": 5,
    "Advanced": 5,
    "Proficient": 11,
    "Expert": 11,
}


@dataclass
class GenerationPlan:
    mode: str
    levels: list[str]
    per_level: int
    total_questions: int
    complexity: dict[str, int]
    sheet_name: str = EXCEL_SHEET_NAME
    column_count: int = EXCEL_COLUMN_COUNT


def parse_lines(text: str) -> list[str]:
    """Split text by newline, trim each line, drop empties, preserve content."""
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def looks_like_url(value: str) -> bool:
    value = value.strip().lower()
    return value.startswith("http://") or value.startswith("https://")


def per_level(mode: str) -> int:
    return _FULL_PER_LEVEL if mode == FULL_MODE else _PROTOTYPE_PER_LEVEL


def complexity_distribution(mode: str) -> dict[str, int]:
    return dict(_FULL_COMPLEXITY if mode == FULL_MODE else _PROTOTYPE_COMPLEXITY)


def resolve_levels(mode: str, selected: list[str]) -> list[str]:
    """Full mode always uses all 7 levels; prototype uses the user's selection."""
    if mode == FULL_MODE:
        return list(CAREER_LEVELS)
    return list(selected)


def build_plan(mode: str, selected_levels: list[str]) -> GenerationPlan:
    levels = resolve_levels(mode, selected_levels)
    count = per_level(mode)
    return GenerationPlan(
        mode=mode,
        levels=levels,
        per_level=count,
        total_questions=count * len(levels),
        complexity=complexity_distribution(mode),
    )
