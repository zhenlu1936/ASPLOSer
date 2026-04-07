from __future__ import annotations

"""Structural and propagation analysis for Model 2.0 execution runs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, TypeVar

from .execution import ExecutionState
from .model import (
    Confidentiality,
    Credibility,
    EdgeType,
    SecurityGrade,
    SecurityObjectives,
    System,
)


@dataclass(frozen=True)
class StructuralViolation:
    rule: str
    detail: str


@dataclass(frozen=True)
class PropagationRisk:
    dimension: str
    detail: str


@dataclass(frozen=True)
class PropagationEvent:
    step_index: int
    cycle_index: int
    stage: str
    action: str
    dimension: str
    detail: str


T = TypeVar("T")


def _bucket_by(items: Iterable[T], key_fn: Callable[[T], Any]) -> dict[Any, list[T]]:
    grouped: dict[Any, list[T]] = {}
    for item in items:
        grouped.setdefault(key_fn(item), []).append(item)
    return grouped


def _write_section_header(log_file, title: str) -> None:
    log_file.write("-" * 80 + "\n")
    log_file.write(f"{title}\n")
    log_file.write("-" * 80 + "\n\n")


def _count_execution_events_by_cycle(execution_steps: List[ExecutionState]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for step in execution_steps:
        cycle_index = step.cycle_index
        counts[cycle_index] = counts.get(cycle_index, 0) + 1
    return counts


def _count_propagation_events_by_cycle(events: List[PropagationEvent]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for event in events:
        counts[event.cycle_index] = counts.get(event.cycle_index, 0) + 1
    return counts


def _write_cycle_summary(log_file, execution_counts: dict[int, int], risk_counts: dict[int, int]) -> None:
    _write_section_header(log_file, "CYCLE SUMMARY")
    for cycle in sorted(execution_counts.keys()):
        log_file.write(
            f"Cycle {cycle}: {execution_counts[cycle]} execution events, "
            f"{risk_counts.get(cycle, 0)} propagation events\n"
        )
    log_file.write("\n")


def _grade_from_levels(levels: List[int]) -> SecurityGrade:
    if not levels:
        return SecurityGrade.MIXED
    m = min(levels)
    return {2: SecurityGrade.HIGH, 1: SecurityGrade.MIXED}.get(m, SecurityGrade.LOW)


def _extract_subject_object(source, target):
    """Extract subject and object from an edge, normalizing direction.
    Returns (subject, object) or (None, None) if edge doesn't connect subject-object.
    """
    if source.is_subject and not target.is_subject:
        return source, target
    elif not source.is_subject and target.is_subject:
        return target, source
    return None, None


def compute_security_objectives(system: System) -> SecurityObjectives:
    graph = system.graph
    confidentiality_levels: List[int] = []
    integrity_levels: List[int] = []
    availability_levels: List[int] = []

    for edge in graph.edges:
        source = graph.nodes[edge.source]
        target = graph.nodes[edge.target]
        
        subject, obj = _extract_subject_object(source, target)
        if subject is None:
            continue
        
        s = subject.as_subject()
        o = obj.as_object()
        s_cred_lvl = s.credibility.level().value
        
        confidentiality_levels.append(min(s_cred_lvl, o.confidentiality.level().value))
        integrity_levels.append(min(s_cred_lvl, o.correctness.level().value, s.correctness.level().value))
        availability_levels.append(min(s_cred_lvl, o.continuity.level().value, s.continuity.level().value))

    return SecurityObjectives(
        confidentiality=_grade_from_levels(confidentiality_levels),
        integrity=_grade_from_levels(integrity_levels),
        availability=_grade_from_levels(availability_levels),
    )


def validate_structural_constraints(system: System) -> List[StructuralViolation]:
    graph = system.graph
    violations: List[StructuralViolation] = []

    # Component upper-bound rule.
    for edge in graph.edges:
        if edge.type != EdgeType.COMPONENT_OF:
            continue
        child = graph.nodes[edge.source]
        parent = graph.nodes[edge.target]
        if not child.is_subject or not parent.is_subject:
            continue

        child_attr = child.as_subject()
        parent_attr = parent.as_subject()

        for attr_name in ["correctness", "continuity"]:
            parent_attr_val = getattr(parent_attr, attr_name).level().value
            child_attr_val = getattr(child_attr, attr_name).level().value
            if parent_attr_val > child_attr_val:
                violations.append(
                    StructuralViolation(
                        rule="ComponentUpperBound",
                        detail=f"{parent.name}.{attr_name} exceeds {child.name}.{attr_name}",
                    )
                )

    # Dependency upper-bound rule.
    for subject_name, object_names in system.dependencies.items():
        subject = graph.nodes[subject_name]
        if not subject.is_subject:
            continue
        s_attr = subject.as_subject()

        for object_name in object_names:
            obj = graph.nodes[object_name]
            if obj.is_subject:
                continue
            o_attr = obj.as_object()

            for attr_name in ["correctness", "continuity"]:
                s_attr_val = getattr(s_attr, attr_name).level().value
                o_attr_val = getattr(o_attr, attr_name).level().value
                if s_attr_val > o_attr_val:
                    violations.append(
                        StructuralViolation(
                            rule="DependencyUpperBound",
                            detail=f"{subject_name}.{attr_name} exceeds {object_name}.{attr_name}",
                        )
                    )

    return violations


def evaluate_propagation_risks(system: System) -> List[PropagationRisk]:
    graph = system.graph
    risks: List[PropagationRisk] = []

    for edge in graph.edges:
        source = graph.nodes[edge.source]
        target = graph.nodes[edge.target]

        # Confidentiality propagation intuition.
        if source.is_subject and (not target.is_subject):
            s_attr = source.as_subject()
            o_attr = target.as_object()
            if (
                s_attr.credibility == Credibility.UNTRUSTED
                and o_attr.confidentiality == Confidentiality.NON_CONFIDENTIAL
                and edge.attributes.confidentiality == Confidentiality.NON_CONFIDENTIAL
            ):
                risks.append(
                    PropagationRisk(
                        dimension="Confidentiality",
                        detail=f"Potential exposure on edge {edge.name}: {source.name} -> {target.name}",
                    )
                )

        # Continuity propagation intuition.
        if edge.attributes.continuity.level().value == 0:
            risks.append(
                PropagationRisk(
                    dimension="Availability",
                    detail=f"Operation blocked by discontinuous edge {edge.name}",
                )
            )

    return risks


def build_analysis_snapshot(system: System) -> tuple[list[str], list[str]]:
    """Build invariant analysis strings reused by simulator execution states."""
    base_violations = validate_structural_constraints(system)
    base_risks = evaluate_propagation_risks(system)
    return (
        [f"[{violation.rule}] {violation.detail}" for violation in base_violations],
        [f"[{risk.dimension}] {risk.detail}" for risk in base_risks],
    )


def _parse_risk_string(risk: str) -> tuple[str, str]:
    # Risk format is "[Dimension] detail".
    if risk.startswith("[") and "]" in risk:
        close = risk.find("]")
        dimension = risk[1:close].strip()
        detail = risk[close + 1 :].strip()
        if dimension and detail:
            return dimension, detail
    return "Unknown", risk


def log_propagation_events(
    system: System,
    execution_steps: List[ExecutionState],
    output_file: str = "output/propagation_log.txt",
) -> List[PropagationEvent]:
    """Build propagation events from simulation states and optionally write a log file.

    Note: The system parameter is kept for API compatibility.
    """
    del system

    events: List[PropagationEvent] = []
    for step in execution_steps:
        for risk in getattr(step, "risks", []):
            dimension, detail = _parse_risk_string(risk)
            events.append(
                PropagationEvent(
                    step_index=step.step_index,
                    cycle_index=step.cycle_index,
                    stage=step.stage,
                    action=step.action,
                    dimension=dimension,
                    detail=detail,
                )
            )

    if output_file:
        _write_propagation_log(events, execution_steps, output_file)

    return events


def _write_propagation_log(
    events: List[PropagationEvent],
    execution_steps: List[ExecutionState],
    output_file: str,
) -> None:
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("PROPAGATION EVENT LOG\n")
        f.write("=" * 80 + "\n\n")

        events_by_cycle = _count_execution_events_by_cycle(execution_steps)
        risks_by_cycle = _count_propagation_events_by_cycle(events)

        f.write(f"Total Execution Events: {len(execution_steps)}\n")

        if not events:
            f.write("Total Propagation Events: 0\n")
            f.write("Stages with Propagation: 0\n")
            f.write("Risk Dimensions: None\n\n")

            _write_section_header(f, "RISKS BY DIMENSION")
            f.write("No propagation events detected.\n\n")

            _write_section_header(f, "RISKS BY EXECUTION STAGE")
            f.write("No propagation events detected.\n\n")

            _write_cycle_summary(f, events_by_cycle, {})

            _write_all_execution_events(f, execution_steps)
            return

        by_stage = _bucket_by(events, lambda event: event.stage)
        by_dimension = _bucket_by(events, lambda event: event.dimension)

        f.write(f"Total Propagation Events: {len(events)}\n")
        f.write(f"Stages with Propagation: {len(by_stage)}\n")
        f.write(f"Risk Dimensions: {', '.join(sorted(by_dimension.keys()))}\n\n")

        _write_cycle_summary(f, events_by_cycle, risks_by_cycle)

        _write_section_header(f, "RISKS BY DIMENSION")

        for dimension in sorted(by_dimension.keys()):
            risks_by_detail = _bucket_by(by_dimension[dimension], lambda event: event.detail)

            f.write(f"[{dimension}] Total events: {len(by_dimension[dimension])}\n")
            for detail, detail_events in sorted(risks_by_detail.items()):
                f.write(f"  • {detail} ({len(detail_events)} occurrences)\n")
                for event in detail_events[:2]:
                    f.write(
                        f"    - Cycle {event.cycle_index}, Step {event.step_index} "
                        f"[{event.stage}]: {event.action}\n"
                    )
                if len(detail_events) > 2:
                    f.write(f"    ... and {len(detail_events)-2} more occurrences\n")
            f.write("\n")

            _write_section_header(f, "RISKS BY EXECUTION STAGE")

        stage_order = ["Development", "Deployment", "Inference", "Response", "Feedback", "Structural"]
        for stage in stage_order:
            if stage not in by_stage:
                continue
            f.write(f"[{stage}]\n")
            by_dim_in_stage: dict[str, int] = {}
            for event in by_stage[stage]:
                by_dim_in_stage[event.dimension] = by_dim_in_stage.get(event.dimension, 0) + 1

            for dim, count in sorted(by_dim_in_stage.items()):
                f.write(f"  {dim}: {count} risks\n")
            f.write("\n")

        _write_section_header(f, "DETAILED EVENT LOG (First 50 events)")

        for event in events[:50]:
            f.write(
                f"Cycle {event.cycle_index:2d}, Step {event.step_index:2d} "
                f"[{event.stage:12s}] {event.dimension:15s} | {event.detail}\n"
                f"  Action: {event.action}\n\n"
            )

        if len(events) > 50:
            f.write(f"... and {len(events)-50} more events (see above for summary)\n")

        f.write("\n")
        _write_all_execution_events(f, execution_steps)


def _write_all_execution_events(log_file, execution_steps: List[ExecutionState]) -> None:
    log_file.write("-" * 80 + "\n")
    log_file.write("ALL EXECUTION EVENTS\n")
    log_file.write("-" * 80 + "\n\n")

    if not execution_steps:
        log_file.write("No execution events recorded.\n")
        return

    for step in execution_steps:
        cycle_index = step.cycle_index
        log_file.write(
            f"Cycle {cycle_index:2d}, Step {step.step_index:2d} "
            f"[{step.stage:12s}] {step.action}\n"
        )

        violations = step.violations
        if violations:
            log_file.write("  Violations:\n")
            for violation in violations:
                log_file.write(f"    - {violation}\n")
        else:
            log_file.write("  Violations: none\n")

        risks = step.risks
        if risks:
            log_file.write("  Risks:\n")
            for risk in risks:
                log_file.write(f"    - {risk}\n")
        else:
            log_file.write("  Risks: none\n")

        log_file.write("\n")


def print_propagation_summary(events: List[PropagationEvent], log_path: str = "output/propagation_log.txt") -> None:
    if not events:
        print("✓ No propagation risks detected!")
        return

    print(f"\n⚠  PROPAGATION RISKS DETECTED: {len(events)} events\n")

    by_dimension: dict[str, List[PropagationEvent]] = {}
    for event in events:
        by_dimension.setdefault(event.dimension, []).append(event)

    for dimension in sorted(by_dimension.keys()):
        print(f"  [{dimension}] {len(by_dimension[dimension])} events")
        unique_details = {e.detail for e in by_dimension[dimension]}
        for detail in sorted(unique_details)[:3]:
            print(f"    • {detail}")
        if len(unique_details) > 3:
            print(f"    ... and {len(unique_details)-3} more")

    print(f"\nSee {log_path} for detailed event log.\n")
