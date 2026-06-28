"""Tests for duplicate detection and cluster logic."""

from __future__ import annotations


from backend.services.duplicate_detector import find_duplicates
from backend.services.rework import build_duplicate_clusters


def _q(question: str, career_level: str = "ASE") -> dict:
    return {
        "title": 0,
        "ssid": "TEST01",
        "skill": "Test Skill",
        "topic": "Testing",
        "question_type": "QnA",
        "career_level": career_level,
        "complexity": "Basic",
        "question": question,
        "answer": "The answer.",
        "options": "",
        "reference_url": "https://example.com",
    }


# ── find_duplicates ────────────────────────────────────────────────────────────

def test_no_duplicates_with_dissimilar_questions():
    rows = [
        _q("What is Python?"),
        _q("Explain SQL joins."),
        _q("How does DNS work?"),
    ]
    pairs = find_duplicates(rows, threshold=0.85)
    assert pairs == []


def test_exact_duplicate_detected():
    q = "What is the primary component of a SharePoint farm?"
    rows = [_q(q), _q(q)]
    pairs = find_duplicates(rows, threshold=0.85)
    assert len(pairs) >= 1


def test_threshold_controls_sensitivity():
    rows = [
        _q("What is a SharePoint farm?"),
        _q("What are the components of a SharePoint farm?"),
    ]
    high = find_duplicates(rows, threshold=0.99)
    low = find_duplicates(rows, threshold=0.50)
    assert len(low) >= len(high)


def test_find_duplicates_returns_row1_row2_keys():
    rows = [_q("Same question?"), _q("Same question?"), _q("Different topic entirely.")]
    pairs = find_duplicates(rows, threshold=0.85)
    for pair in pairs:
        assert "row1" in pair
        assert "row2" in pair


# ── build_duplicate_clusters ──────────────────────────────────────────────────

def test_cluster_groups_connected_pairs():
    findings = [{"row1": 1, "row2": 2}, {"row1": 2, "row2": 3}]
    clusters = build_duplicate_clusters(findings)
    all_nodes = {n for c in clusters for n in c}
    assert {1, 2, 3}.issubset(all_nodes)
    flat = [set(c) for c in clusters if len(c) > 1]
    assert any({1, 2, 3}.issubset(c) for c in flat)


def test_cluster_empty_findings():
    clusters = build_duplicate_clusters([])
    assert clusters == []


def test_cluster_disjoint_pairs():
    findings = [{"row1": 1, "row2": 2}, {"row1": 4, "row2": 5}]
    clusters = build_duplicate_clusters(findings)
    assert len(clusters) == 2


def test_cluster_single_pair():
    findings = [{"row1": 2, "row2": 5}]
    clusters = build_duplicate_clusters(findings)
    assert len(clusters) == 1
    assert set(clusters[0]) == {2, 5}
