from __future__ import annotations

"""Structural and propagation analysis for Model 2.0 execution runs."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, List, TypeVar

from .execution import ExecutionState
from .model import (
    Confidentiality,
    Continuity,
    Correctness,
    Credibility,
    SecurityGrade,
    SecurityObjectives,
    System,
    are_opposite_node_types,
)
from .security_aggregation import grade_from_levels


@dataclass(frozen=True)
class StructuralViolation:
    rule: str
    detail: str


@dataclass(frozen=True)
class PropagationRisk:
    dimension: str
    severity: str
    detail: str


@dataclass(frozen=True)
class PropagationEvent:
    step_index: int
    cycle_index: int
    stage: str
    action: str
    dimension: str
    severity: str
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


def _all_steps_share_same_analysis(execution_steps: List[ExecutionState]) -> tuple[bool, bool]:
    """Return whether all execution steps carry identical violation/risk lists."""
    if not execution_steps:
        return False, False

    first_violations = execution_steps[0].violations
    first_risks = execution_steps[0].risks

    same_violations = all(step.violations == first_violations for step in execution_steps)
    same_risks = all(step.risks == first_risks for step in execution_steps)
    return same_violations, same_risks


def _extract_subject_object(source, target):
    """Extract subject and object from an edge, normalizing direction.
    Returns (subject, object) or (None, None) if edge doesn't connect subject-object.
    """
    if source.is_subject and not target.is_subject:
        return source, target
    elif not source.is_subject and target.is_subject:
        return target, source
    return None, None


def _build_confidentiality_risk(edge, severity: str) -> PropagationRisk:
    severity_label = "High" if severity == "high" else "Medium"
    if severity == "high":
        return PropagationRisk(
            dimension="Confidentiality",
            severity=severity_label,
            detail=f"Potential exposure on edge {edge.action}/{edge.name}: {edge.source} -> {edge.target}",
        )
    return PropagationRisk(
        dimension="Confidentiality",
        severity=severity_label,
        detail=f"Medium risk from mixed confidentiality on edge {edge.action}/{edge.name}",
    )


def _build_integrity_risk(edge, severity: str) -> PropagationRisk:
    severity_label = "High" if severity == "high" else "Medium"
    if severity == "high":
        return PropagationRisk(
            dimension="Integrity",
            severity=severity_label,
            detail=f"Potential integrity compromise on edge {edge.action}/{edge.name}",
        )
    return PropagationRisk(
        dimension="Integrity",
        severity=severity_label,
        detail=f"Medium risk from mixed correctness on edge {edge.action}/{edge.name}",
    )


def _build_availability_risk(edge, severity: str) -> PropagationRisk:
    severity_label = "High" if severity == "high" else "Medium"
    if severity == "high":
        return PropagationRisk(
            dimension="Availability",
            severity=severity_label,
            detail=f"Operation blocked by discontinuous edge {edge.action}/{edge.name}",
        )
    return PropagationRisk(
        dimension="Availability",
        severity=severity_label,
        detail=f"Medium risk from mixed continuity on edge {edge.action}/{edge.name}",
    )


def _is_high_confidentiality_risk(s_attr, o_attr, edge) -> bool:
    return (
        s_attr.credibility == Credibility.UNTRUSTED
        and o_attr.confidentiality == Confidentiality.NON_CONFIDENTIAL
        and edge.attributes.confidentiality == Confidentiality.NON_CONFIDENTIAL
    )


def _is_mixed_confidentiality_risk(s_attr, o_attr, edge) -> bool:
    return (
        s_attr.credibility == Credibility.MIXED_CREDIBILITY
        or o_attr.confidentiality == Confidentiality.MIXED_CONFIDENTIALITY
        or edge.attributes.confidentiality == Confidentiality.MIXED_CONFIDENTIALITY
    )


def _is_high_integrity_risk(s_attr, o_attr, edge) -> bool:
    return (
        s_attr.credibility == Credibility.UNTRUSTED
        and (
            s_attr.correctness == Correctness.INCORRECT
            or o_attr.correctness == Correctness.INCORRECT
            or edge.attributes.correctness == Correctness.INCORRECT
        )
    )


def _is_mixed_integrity_risk(s_attr, o_attr, edge) -> bool:
    return (
        s_attr.credibility == Credibility.MIXED_CREDIBILITY
        or s_attr.correctness == Correctness.MIXED_CORRECTNESS
        or o_attr.correctness == Correctness.MIXED_CORRECTNESS
        or edge.attributes.correctness == Correctness.MIXED_CORRECTNESS
    )


def _is_high_availability_risk(edge) -> bool:
    return edge.attributes.continuity.level().value == 0


def _is_mixed_availability_risk(s_attr, o_attr, edge) -> bool:
    return (
        s_attr.continuity == Continuity.MIXED_CONTINUITY
        or o_attr.continuity == Continuity.MIXED_CONTINUITY
        or edge.attributes.continuity == Continuity.MIXED_CONTINUITY
        or s_attr.credibility == Credibility.MIXED_CREDIBILITY
    )


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
        confidentiality=grade_from_levels(confidentiality_levels),
        integrity=grade_from_levels(integrity_levels),
        availability=grade_from_levels(availability_levels),
    )


def validate_structural_constraints(system: System) -> List[StructuralViolation]:
    graph = system.graph
    violations: List[StructuralViolation] = []

    # Model 2.0 requires bipartite connectivity between subject and object endpoints.
    for edge in graph.edges:
        source = graph.nodes[edge.source]
        target = graph.nodes[edge.target]
        if not are_opposite_node_types(source, target):
            violations.append(
                StructuralViolation(
                    rule="BipartiteEndpoint",
                    detail=(
                        f"{edge.action}/{edge.name} connects non-bipartite endpoints: "
                        f"{edge.source} -> {edge.target}"
                    ),
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

        subject, obj = _extract_subject_object(source, target)
        if subject is not None:
            s_attr = subject.as_subject()
            o_attr = obj.as_object()
            if _is_high_confidentiality_risk(s_attr, o_attr, edge):
                risks.append(_build_confidentiality_risk(edge, "high"))
            elif _is_mixed_confidentiality_risk(s_attr, o_attr, edge):
                risks.append(_build_confidentiality_risk(edge, "medium"))

            if _is_high_integrity_risk(s_attr, o_attr, edge):
                risks.append(_build_integrity_risk(edge, "high"))
            elif _is_mixed_integrity_risk(s_attr, o_attr, edge):
                risks.append(_build_integrity_risk(edge, "medium"))

            if _is_high_availability_risk(edge):
                risks.append(_build_availability_risk(edge, "high"))
            elif _is_mixed_availability_risk(s_attr, o_attr, edge):
                risks.append(_build_availability_risk(edge, "medium"))
            continue

        # Non subject-object edges can still carry hard availability failures.
        if _is_high_availability_risk(edge):
            risks.append(_build_availability_risk(edge, "high"))

    return risks


def build_analysis_snapshot(system: System) -> tuple[list[str], list[str]]:
    """Build invariant analysis strings reused by simulator execution states."""
    base_violations = validate_structural_constraints(system)
    base_risks = evaluate_propagation_risks(system)
    return (
        [f"[{violation.rule}] {violation.detail}" for violation in base_violations],
        [f"[{risk.dimension}][{risk.severity}] {risk.detail}" for risk in base_risks],
    )


def _infer_severity_from_detail(detail: str) -> str:
    lowered = detail.lower()
    if "high risk" in lowered or "potential" in lowered or "blocked" in lowered:
        return "High"
    if "medium risk" in lowered or "mixed" in lowered:
        return "Medium"
    return "Unknown"


def _parse_risk_string(risk: str) -> tuple[str, str, str]:
    # Preferred format is "[Dimension][Severity] detail".
    if risk.startswith("[") and "]" in risk:
        close_dim = risk.find("]")
        dimension = risk[1:close_dim].strip()
        rest = risk[close_dim + 1 :].strip()
        if rest.startswith("[") and "]" in rest:
            close_sev = rest.find("]")
            severity = rest[1:close_sev].strip()
            detail = rest[close_sev + 1 :].strip()
            if dimension and severity and detail:
                return dimension, severity, detail

        # Backward-compatible format: "[Dimension] detail"
        detail = rest
        if dimension and detail:
            return dimension, _infer_severity_from_detail(detail), detail

    return "Unknown", "Unknown", risk


def _severity_sort_key(severity: str) -> tuple[int, str]:
    order = {"High": 0, "Medium": 1, "Low": 2, "Unknown": 3}
    return (order.get(severity, 4), severity)


def log_propagation_events(
    execution_steps: List[ExecutionState],
    output_file: str = "output/default_log.txt",
) -> List[PropagationEvent]:
    """Build propagation events from simulation states and optionally write a log file."""

    events: List[PropagationEvent] = []
    for step in execution_steps:
        for risk in getattr(step, "risks", []):
            dimension, severity, detail = _parse_risk_string(risk)
            events.append(
                PropagationEvent(
                    step_index=step.step_index,
                    cycle_index=step.cycle_index,
                    stage=step.stage,
                    action=step.action,
                    dimension=dimension,
                    severity=severity,
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
        by_severity = _bucket_by(events, lambda event: event.severity)

        f.write(f"Total Propagation Events: {len(events)}\n")
        f.write(f"Stages with Propagation: {len(by_stage)}\n")
        f.write(f"Risk Dimensions: {', '.join(sorted(by_dimension.keys()))}\n\n")
        f.write(f"Risk Levels: {', '.join(sorted(by_severity.keys(), key=_severity_sort_key))}\n\n")

        _write_cycle_summary(f, events_by_cycle, risks_by_cycle)

        _write_section_header(f, "RISKS BY DIMENSION AND LEVEL")

        for dimension in sorted(by_dimension.keys()):
            f.write(f"[{dimension}] Total events: {len(by_dimension[dimension])}\n")
            by_severity_in_dim = _bucket_by(by_dimension[dimension], lambda event: event.severity)
            for severity in sorted(by_severity_in_dim.keys(), key=_severity_sort_key):
                severity_events = by_severity_in_dim[severity]
                f.write(f"  [{severity}] {len(severity_events)} events\n")
                risks_by_detail = _bucket_by(severity_events, lambda event: event.detail)
                for detail, detail_events in sorted(risks_by_detail.items()):
                    f.write(f"    • {detail} ({len(detail_events)} occurrences)\n")
                    for event in detail_events[:2]:
                        f.write(
                            f"      - Cycle {event.cycle_index}, Step {event.step_index} "
                            f"[{event.stage}]: {event.action}\n"
                        )
                    if len(detail_events) > 2:
                        f.write(f"      ... and {len(detail_events)-2} more occurrences\n")
            f.write("\n")

        _write_section_header(f, "RISKS BY EXECUTION STAGE")

        stage_order = ["Development", "Deployment", "Inference", "Response", "Feedback"]
        for stage in stage_order:
            if stage not in by_stage:
                continue
            f.write(f"[{stage}]\n")
            by_dim_in_stage = _bucket_by(by_stage[stage], lambda event: event.dimension)

            for dim in sorted(by_dim_in_stage.keys()):
                f.write(f"  {dim}:\n")
                by_severity_in_stage_dim = _bucket_by(by_dim_in_stage[dim], lambda event: event.severity)
                for severity in sorted(by_severity_in_stage_dim.keys(), key=_severity_sort_key):
                    f.write(f"    {severity}: {len(by_severity_in_stage_dim[severity])} risks\n")
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

    same_violations, same_risks = _all_steps_share_same_analysis(execution_steps)

    if same_violations and execution_steps[0].violations:
        _write_section_header(log_file, "SCENARIO-LEVEL STRUCTURAL FINDINGS")
        for violation in execution_steps[0].violations:
            log_file.write(f"- {violation}\n")
        log_file.write("\n")

    if same_risks and execution_steps[0].risks:
        _write_section_header(log_file, "SCENARIO-LEVEL PROPAGATION RISKS")
        for risk in execution_steps[0].risks:
            log_file.write(f"- {risk}\n")
        log_file.write("\n")

    for step in execution_steps:
        cycle_index = step.cycle_index
        log_file.write(
            f"Cycle {cycle_index:2d}, Step {step.step_index:2d} "
            f"[{step.stage:12s}] {step.action}\n"
        )

        violations = step.violations
        if violations:
            if same_violations:
                log_file.write("  Violations: see SCENARIO-LEVEL STRUCTURAL FINDINGS\n")
            else:
                log_file.write("  Violations:\n")
                for violation in violations:
                    log_file.write(f"    - {violation}\n")
        else:
            log_file.write("  Violations: none\n")

        risks = step.risks
        if risks:
            if same_risks:
                log_file.write("  Risks: see SCENARIO-LEVEL PROPAGATION RISKS\n")
            else:
                log_file.write("  Risks:\n")
                for risk in risks:
                    log_file.write(f"    - {risk}\n")
        else:
            log_file.write("  Risks: none\n")

        log_file.write("\n")


def print_propagation_summary(events: List[PropagationEvent], log_path: str = "output/default_log.txt") -> None:
    if not events:
        print("✓ No propagation risks detected!")
        return

    print(f"\n⚠  PROPAGATION RISKS DETECTED: {len(events)} events\n")

    by_dimension: dict[str, List[PropagationEvent]] = {}
    for event in events:
        by_dimension.setdefault(event.dimension, []).append(event)

    for dimension in sorted(by_dimension.keys()):
        print(f"  [{dimension}] {len(by_dimension[dimension])} events")
        by_severity = _bucket_by(by_dimension[dimension], lambda event: event.severity)
        for severity in sorted(by_severity.keys(), key=_severity_sort_key):
            severity_events = by_severity[severity]
            print(f"    - {severity}: {len(severity_events)} events")
            unique_details = {e.detail for e in severity_events}
            for detail in sorted(unique_details)[:2]:
                print(f"      • {detail}")
            if len(unique_details) > 2:
                print(f"      ... and {len(unique_details)-2} more")

    print(f"\nSee {log_path} for detailed event log.\n")
