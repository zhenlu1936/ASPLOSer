from __future__ import annotations

"""Execution state snapshots for Model 2.0 stage-cycle traces."""

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
