from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionState:
    """Simulation step snapshot shared across simulator and analysis modules."""

    step_index: int
    cycle_index: int
    stage: str
    action: str
    violations: list[str]
    risks: list[str]
