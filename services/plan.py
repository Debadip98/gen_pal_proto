"""Domain rules for GenPal question-bank generation planning.

Defines the GenPal output contract: the exact 11 lowercase columns, career
levels, generation modes, the fixed per-level complexity distribution, and
helpers used by the landing page and pipeline to validate input, order rows,
and build the output filename.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- GenPal output contract -------------------------------------------------

# The ONLY columns allowed in the exported workbook, in this exact order.
GENPAL_COLUMNS = [
    "title",
    "ssid",
    "skill",
    "topic",
    "question_type",
    "career_level",
    "complexity",
    "question",
    "answer",
    "options",
    "reference_url",
]

EXCEL_SHEET_NAME = "Sheet1"
EXCEL_COLUMN_COUNT = len(GENPAL_COLUMNS)
QUESTION_TYPE = "QnA"

# --- Career levels & complexity ---------------------------------------------

# Generation and export order.
CAREER_LEVELS = ("ASE", "SE", "SSE", "TL", "AM", "M", "SM")
COMPLEXITY_LEVELS = ("Basic", "Intermediate", "Advanced", "Proficient", "Expert")

VALID_CAREER_LEVELS = set(CAREER_LEVELS)
VALID_COMPLEXITIES = set(COMPLEXITY_LEVELS)

_CAREER_LEVEL_INDEX = {level: i for i, level in enumerate(CAREER_LEVELS)}
_COMPLEXITY_INDEX = {c: i for i, c in enumerate(COMPLEXITY_LEVELS)}

# Fixed for BOTH modes: 40 questions per career level.
PER_LEVEL = 40

# Fixed complexity distribution per career level (sums to PER_LEVEL = 40).
COMPLEXITY_DISTRIBUTION = {
    "Basic": 5,
    "Intermediate": 6,
    "Advanced": 7,
    "Proficient": 11,
    "Expert": 11,
}

# --- Modes ------------------------------------------------------------------

PROTOTYPE_MODE = "Prototype Mode"
FULL_MODE = "Full GenPal Mode"
GENERATION_MODES = (PROTOTYPE_MODE, FULL_MODE)

DEFAULT_PROTOTYPE_LEVELS = ("ASE", "SE")


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


def complexity_distribution() -> dict[str, int]:
    """Fixed 5/6/7/11/11 distribution, identical for both modes."""
    return dict(COMPLEXITY_DISTRIBUTION)


def resolve_levels(mode: str, selected: list[str]) -> list[str]:
    """Full mode always uses all 7 levels in canonical order; prototype uses
    the user's selection, reordered to canonical career-level order."""
    if mode == FULL_MODE:
        return list(CAREER_LEVELS)
    chosen = {s for s in selected if s in VALID_CAREER_LEVELS}
    return [level for level in CAREER_LEVELS if level in chosen]


def level_sort_key(level: str) -> int:
    return _CAREER_LEVEL_INDEX.get(level, len(CAREER_LEVELS))


def complexity_sort_key(complexity: str) -> int:
    return _COMPLEXITY_INDEX.get(complexity, len(COMPLEXITY_LEVELS))


def build_plan(mode: str, selected_levels: list[str]) -> GenerationPlan:
    levels = resolve_levels(mode, selected_levels)
    return GenerationPlan(
        mode=mode,
        levels=levels,
        per_level=PER_LEVEL,
        total_questions=PER_LEVEL * len(levels),
        complexity=complexity_distribution(),
    )


_ILLEGAL_FILENAME_CHARS = '\\/:*?"<>|'


def build_filename(skill: str, ssid: str) -> str:
    """Build the output filename: ``<Skill Name>-<SSID>.xlsx`` (sanitized)."""
    skill = (skill or "").strip()
    ssid = (ssid or "").strip()
    raw = f"{skill}-{ssid}.xlsx"
    cleaned = "".join("_" if ch in _ILLEGAL_FILENAME_CHARS else ch for ch in raw)
    return cleaned.strip() or "genpal_question_bank.xlsx"
