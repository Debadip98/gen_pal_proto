"""Tests for dynamic complexity distribution calculations."""

from __future__ import annotations

import pytest

from backend.core.constants import (
    COMPLEXITY_LEVELS,
    calculate_complexity_distribution,
)


def test_legacy_40_exact():
    dist = calculate_complexity_distribution(40)
    assert dist == {"Basic": 5, "Intermediate": 6, "Advanced": 7, "Proficient": 11, "Expert": 11}


def test_sum_equals_input():
    for n in [5, 10, 20, 40, 50, 80, 100, 200]:
        dist = calculate_complexity_distribution(n)
        assert sum(dist.values()) == n, f"Sum mismatch for n={n}: {dist}"


def test_all_levels_present():
    dist = calculate_complexity_distribution(20)
    assert set(dist.keys()) == set(COMPLEXITY_LEVELS)


def test_zero_input():
    dist = calculate_complexity_distribution(0)
    assert all(v == 0 for v in dist.values())


def test_small_count_no_negatives():
    for n in range(1, 15):
        dist = calculate_complexity_distribution(n)
        assert all(v >= 0 for v in dist.values()), f"Negative value for n={n}: {dist}"
        assert sum(dist.values()) == n


def test_proficient_expert_priority():
    """Proficient and Expert should get remainder tokens first (per spec)."""
    dist = calculate_complexity_distribution(11)
    assert dist["Proficient"] >= dist["Basic"]
    assert dist["Expert"] >= dist["Basic"]


def test_distribution_non_decreasing_by_level():
    """Advanced >= Intermediate >= Basic (generally; weights enforce this)."""
    dist = calculate_complexity_distribution(40)
    assert dist["Advanced"] >= dist["Intermediate"]
    assert dist["Intermediate"] >= dist["Basic"]
