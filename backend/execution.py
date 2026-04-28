from __future__ import annotations

"""Execution state snapshots for Model 2.0 stage-cycle traces."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionState:
    """Simulation step snapshot shared across simulator and analysis modules.

    ``risks`` contains only the delta risks introduced by this specific
    transition firing (not cumulative across all steps).

    ``marking_snapshot`` is a shallow copy of the CPN marking at this step,
    keyed by node name → TokenColor. It is ``None`` when a caller records an
    execution state without requesting snapshots.
    Since dict is unhashable, instances with a non-None snapshot cannot be
    used as dict keys / set members — which is never required in practice.
    """

    step_index: int
    cycle_index: int
    stage: str
    action: str
    violations: list[str]
    risks: list[str]
    marking_snapshot: dict | None = field(default=None, compare=False, hash=False)
