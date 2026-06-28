"""Domain constants for GenPal question-bank generation.

Defines the GenPal output contract (11 columns), career levels, complexity
levels, generation modes, and the dynamic complexity distribution calculator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- GenPal output contract ---------------------------------------------------

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

# --- Career levels & complexity -----------------------------------------------

CAREER_LEVELS = ("ASE", "SE", "SSE", "TL", "AM", "M", "SM")
COMPLEXITY_LEVELS = ("Basic", "Intermediate", "Advanced", "Proficient", "Expert")

VALID_CAREER_LEVELS = set(CAREER_LEVELS)
VALID_COMPLEXITIES = set(COMPLEXITY_LEVELS)

_CAREER_LEVEL_INDEX = {level: i for i, level in enumerate(CAREER_LEVELS)}
_COMPLEXITY_INDEX = {c: i for i, c in enumerate(COMPLEXITY_LEVELS)}

# Fixed distribution for the legacy 40-questions-per-level default.
PER_LEVEL = 40
COMPLEXITY_DISTRIBUTION = {
    "Basic": 5,
    "Intermediate": 6,
    "Advanced": 7,
    "Proficient": 11,
    "Expert": 11,
}

# Weighted distribution ratios for dynamic question counts.
COMPLEXITY_WEIGHTS = {
    "Basic": 0.125,
    "Intermediate": 0.150,
    "Advanced": 0.175,
    "Proficient": 0.275,
    "Expert": 0.275,
}

# --- Modes --------------------------------------------------------------------

PROTOTYPE_MODE = "Prototype Mode"
FULL_MODE = "Full GenPal Mode"
FIXED_GENPAL_MODE = "Fixed GenPal Count"
DYNAMIC_COUNT_MODE = "Dynamic Count"
GENERATION_MODES = (PROTOTYPE_MODE, FULL_MODE, FIXED_GENPAL_MODE, DYNAMIC_COUNT_MODE)

DEFAULT_PROTOTYPE_LEVELS = ("ASE", "SE")

# --- Dynamic count calculation ------------------------------------------------


def calculate_complexity_distribution(question_count: int) -> dict[str, int]:
    """Return per-complexity question counts that sum to ``question_count``.

    For exactly 40 questions the legacy fixed distribution is returned to
    preserve backward compatibility. For any other count, weighted ratios are
    used with remainders assigned to Proficient then Expert first.
    """
    if question_count == 40:
        return dict(COMPLEXITY_DISTRIBUTION)
    if question_count <= 0:
        return {c: 0 for c in COMPLEXITY_LEVELS}

    floored = {c: int(question_count * w) for c, w in COMPLEXITY_WEIGHTS.items()}
    remainder = question_count - sum(floored.values())
    priority = ["Proficient", "Expert", "Advanced", "Intermediate", "Basic"]
    for c in priority:
        if remainder <= 0:
            break
        floored[c] += 1
        remainder -= 1
    return floored


# --- Helpers ------------------------------------------------------------------


@dataclass
class GenerationPlan:
    mode: str
    levels: list[str]
    level_counts: dict[str, int]
    total_questions: int
    complexity: dict[str, int] = field(default_factory=dict)
    sheet_name: str = EXCEL_SHEET_NAME
    column_count: int = EXCEL_COLUMN_COUNT


def parse_lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def looks_like_url(value: str) -> bool:
    value = value.strip().lower()
    return value.startswith("http://") or value.startswith("https://")


def resolve_levels(mode: str, selected: list[str]) -> list[str]:
    if mode == FULL_MODE:
        return list(CAREER_LEVELS)
    chosen = {s for s in selected if s in VALID_CAREER_LEVELS}
    return [level for level in CAREER_LEVELS if level in chosen]


def level_sort_key(level: str) -> int:
    return _CAREER_LEVEL_INDEX.get(level, len(CAREER_LEVELS))


def complexity_sort_key(complexity: str) -> int:
    return _COMPLEXITY_INDEX.get(complexity, len(COMPLEXITY_LEVELS))


def build_filename(skill: str, ssid: str) -> str:
    skill = (skill or "").strip()
    ssid = (ssid or "").strip()
    raw = f"{skill}-{ssid}.xlsx"
    illegal = '\\/:*?"<>|'
    cleaned = "".join("_" if ch in illegal else ch for ch in raw)
    return cleaned.strip() or "genpal_question_bank.xlsx"


# Job status constants
class JobStatus:
    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    SENT_TO_SME = "SENT_TO_SME"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    EXCEL_READY = "EXCEL_READY"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"


# Question status constants
class QuestionStatus:
    DRAFT = "DRAFT"
    PENDING_SME_REVIEW = "PENDING_SME_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REGENERATED = "REGENERATED"
    PENDING_REVIEW = "PENDING_REVIEW"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


# Version change status constants
class VersionStatus:
    PENDING_SME_DECISION = "PENDING_SME_DECISION"
    ACCEPTED_BY_SME = "ACCEPTED_BY_SME"
    REJECTED_BY_SME = "REJECTED_BY_SME"
    SUPERSEDED = "SUPERSEDED"


# Review session status constants
class ReviewSessionStatus:
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    COMPLETED = "COMPLETED"


# Document source type constants
class SourceType:
    MANUAL_URL = "MANUAL_URL"
    DISCOVERED_URL = "DISCOVERED_URL"
    UPLOADED_DOC = "UPLOADED_DOC"


# Export type constants
class ExportType:
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"


# Duplicate repair terminal states
FINAL_DUPLICATE_CHECK_PASSED = "FINAL_DUPLICATE_CHECK_PASSED"
FINAL_MANUAL_REVIEW_REQUIRED = "FINAL_MANUAL_REVIEW_REQUIRED"
FINAL_REPAIR_FAILED = "FINAL_REPAIR_FAILED"

# Doc alignment status constants
class DocAlignmentStatus:
    ALIGNED = "ALIGNED"
    PARTIALLY_ALIGNED = "PARTIALLY_ALIGNED"
    NOT_ALIGNED = "NOT_ALIGNED"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
