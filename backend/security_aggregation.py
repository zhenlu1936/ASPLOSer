from __future__ import annotations

"""Shared helpers for level aggregation and security-grade projection."""

from typing import List

from .model import Level, SecurityGrade


def min_level(values: List[int], empty_default: int | None = None) -> int:
    """Return minimum level, optionally providing a default for empty lists."""
    if values:
        return min(values)
    if empty_default is None:
        raise ValueError("Level aggregation requires at least one level value")
    return empty_default


def grade_from_levels(levels: List[int]) -> SecurityGrade:
    """Map aggregated numeric levels to security grade labels."""
    level = min_level(levels, empty_default=Level.MIXED.value)
    return {2: SecurityGrade.HIGH, 1: SecurityGrade.MIXED}.get(level, SecurityGrade.LOW)
