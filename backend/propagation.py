from __future__ import annotations

"""Risk-string aggregation and visualization propagation helpers.

This module owns the shared vocabulary that sits between simulation analysis
and diagram rendering: security dimensions, stage ordering, risk-string
parsing, and draw.io topology-level propagation filters.
"""

from dataclasses import dataclass, field
import html as _html_mod
import re
from typing import List

from .execution import ExecutionState


SECURITY_DIMENSIONS = ("Confidentiality", "Integrity", "Availability")
STAGE_SEQUENCE = ("Initial", "Development", "Deployment", "Operation", "Feedback")
SIMULATION_STAGES = STAGE_SEQUENCE[1:]
ANALYSIS_STAGES = SIMULATION_STAGES[:-1]


def ordered_stage_names(feedback: bool) -> tuple[str, ...]:
    """Return visualization stage names, optionally omitting Feedback."""
    return STAGE_SEQUENCE if feedback else STAGE_SEQUENCE[:-1]


# ---------------------------------------------------------------------------
# Risk classification utilities
# ---------------------------------------------------------------------------

RISK_EDGE_PATTERN = re.compile(r"edge\s+([^/\s]+)/([^\s]+)")
CPN_ACTION_PATTERN = re.compile(r"CPN\[([^\]]+)\]")
FEEDBACK_EDGE_PATTERN = re.compile(r" edge \w+\.Feedback/")
RISK_RANKS = {"high": 2, "medium": 1, "low": 0}


def risk_rank(severity: str) -> int:
    return RISK_RANKS.get(severity.lower(), -1)


def should_replace_risk(
    current: tuple[str, str] | None,
    severity: str,
    origin: str,
) -> bool:
    if current is None:
        return True
    cur_sev, cur_ori = current
    new_rank, cur_rank = risk_rank(severity), risk_rank(cur_sev)
    if new_rank != cur_rank:
        return new_rank > cur_rank
    # Equal severity: prefer propagated over assigned.
    return (origin == "propagated") > (cur_ori == "propagated")


def action_origin(action_name: str, assigned_actions: set[str]) -> str:
    if action_name in assigned_actions:
        return "assigned"
    if action_name.endswith(".Initialize"):
        return "initialization"
    return "propagated"


def risk_origin(action_name: str, edge_name: str, assigned_object_arcs: set[str]) -> str:
    return "assigned" if f"{action_name}/{edge_name}" in assigned_object_arcs else "propagated"


def filter_risks_by_dimension(risk_strings: list[str], dimension: str) -> list[str]:
    """Return only the risk strings belonging to a given security dimension."""
    prefix = f"[{dimension}]"
    return [risk for risk in risk_strings if risk.startswith(prefix)]


# ---------------------------------------------------------------------------
# Token normalization
# ---------------------------------------------------------------------------

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
FEEDBACK_ACTION_PATTERN = re.compile(r"[mapdo]?f\d")  # e.g. f1feedback, mf1feedback, af1feedback...


def normalize_token(value: str) -> str:
    """Normalize a CPN model name / draw.io label to a plain alphanumeric key."""
    stripped = HTML_TAG_PATTERN.sub("", value)
    decoded = _html_mod.unescape(stripped).replace("&", "and")
    return "".join(ch.lower() for ch in decoded if ch.isalnum())


def clean_label_value(value: str) -> str:
    """Strip draw.io HTML from a cell value while preserving readable text."""
    return _html_mod.unescape(HTML_TAG_PATTERN.sub("", value)).strip()


def has_html_markup(value: str) -> bool:
    return HTML_TAG_PATTERN.search(value) is not None


# ---------------------------------------------------------------------------
# Propagation topology
# ---------------------------------------------------------------------------

@dataclass
class EdgeInfo:
    edge_id: str
    source: str
    target: str
    label_tokens: list[str] = field(default_factory=list)


@dataclass
class Topology:
    """Pre-parsed CPN graph topology (draw.io-independent)."""

    subject_ids: set[str] = field(default_factory=set)
    action_ids: set[str] = field(default_factory=set)
    subject_name_by_id: dict[str, str] = field(default_factory=dict)
    action_name_by_id: dict[str, str] = field(default_factory=dict)
    edges: list[EdgeInfo] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk-level collection and directional propagation filters
# ---------------------------------------------------------------------------

def collect_propagation_targets(
    risk_strings: list[str],
    assigned_actions: set[str] | None = None,
    assigned_object_arcs: set[str] | None = None,
) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    actions_set = assigned_actions or set()
    arcs_set = assigned_object_arcs or set()
    action_levels: dict[str, tuple[str, str]] = {}
    edge_levels: dict[str, tuple[str, str]] = {}

    for risk in risk_strings:
        if not risk.startswith("["):
            continue
        parts = risk.split("]", 2)
        if len(parts) < 3:
            continue
        severity = parts[1].lstrip("[").strip() or "Medium"
        parsed_edge = parse_risk_edge(risk)
        if parsed_edge is None:
            continue

        action_name, edge_name = parsed_edge
        act_origin = action_origin(action_name, actions_set)
        arc_origin = risk_origin(action_name, edge_name, arcs_set)
        action_key = normalize_token(action_name)
        edge_key = normalize_token(edge_name)

        if should_replace_risk(action_levels.get(action_key), severity, act_origin):
            action_levels[action_key] = (severity, act_origin)
        if should_replace_risk(edge_levels.get(edge_key), severity, arc_origin):
            edge_levels[edge_key] = (severity, arc_origin)

    return action_levels, edge_levels


def apply_directional_filters(
    topo: Topology,
    action_levels: dict[str, tuple[str, str]],
    edge_levels: dict[str, tuple[str, str]],
    assigned_subjects: set[str] | None = None,
) -> tuple[
    dict[str, tuple[str, str]],
    dict[str, tuple[str, str]],
    dict[str, tuple[str, str]],
    set[str],
]:
    """Apply Model 2.0 directionality to visualization risk coloring.

    Returns ``(action_levels, edge_levels, subject_levels, cascade_terminal_subjects)``.

    Rules:
    - Actions keep assigned/initialization colors; propagated color only if an
      incoming risky edge label exists.
    - Edge labels keep assigned/initialization colors; propagated color only on
      output arcs (action -> subject) whose source action is colored.
    - Subjects are colored by incoming risky edge labels (action -> subject only).
    """

    filtered_actions: dict[str, tuple[str, str]] = {
        name: level
        for name, level in action_levels.items()
        if level[1] in {"assigned", "initialization"}
    }
    for edge in topo.edges:
        if edge.target not in topo.action_ids:
            continue
        action_token = topo.action_name_by_id.get(edge.target, "")
        if not action_token:
            continue
        current = filtered_actions.get(action_token)
        if current is not None and current[1] in {"assigned", "initialization"}:
            continue
        for label in edge.label_tokens:
            if label not in edge_levels:
                continue
            severity, origin = edge_levels[label]
            if should_replace_risk(filtered_actions.get(action_token), severity, origin):
                filtered_actions[action_token] = (severity, origin)

    colored_arc_tokens: set[str] = set()
    for edge in topo.edges:
        if edge.source in topo.action_ids and edge.target in topo.subject_ids:
            source_token = topo.action_name_by_id.get(edge.source, "")
            if source_token in filtered_actions:
                colored_arc_tokens.update(edge.label_tokens)

    filtered_edges: dict[str, tuple[str, str]] = {}
    for token, (severity, origin) in edge_levels.items():
        if origin in {"assigned", "initialization"} or token in colored_arc_tokens:
            filtered_edges[token] = (severity, origin)

    subjects_set = assigned_subjects or set()
    assigned_subject_tokens = {normalize_token(subject) for subject in subjects_set}
    subject_levels: dict[str, tuple[str, str]] = {}

    for edge in topo.edges:
        if edge.target not in topo.subject_ids:
            continue
        severity = ""
        for label in edge.label_tokens:
            if label in filtered_edges:
                severity, _ = filtered_edges[label]
                break
        if not severity:
            continue

        subject_id = edge.target
        subject_token = topo.subject_name_by_id.get(subject_id, "")
        origin = (
            "assigned"
            if subject_token in assigned_subject_tokens and severity.lower() != "high"
            else "propagated"
        )
        if should_replace_risk(subject_levels.get(subject_id), severity, origin):
            subject_levels[subject_id] = (severity, origin)

    # Cascade through colored subjects: subject -> action -> output arcs.
    # Feedback actions are excluded so propagation stops before the feedback loop.
    for edge in topo.edges:
        if edge.source not in topo.subject_ids or edge.target not in topo.action_ids:
            continue
        if edge.source not in subject_levels:
            continue
        action_token = topo.action_name_by_id.get(edge.target, "")
        if not action_token:
            continue
        if FEEDBACK_ACTION_PATTERN.match(action_token):
            continue
        subject_severity, _ = subject_levels[edge.source]
        for label in edge.label_tokens:
            if label not in filtered_edges:
                if label in edge_levels:
                    filtered_edges[label] = edge_levels[label]
                else:
                    filtered_edges[label] = (subject_severity, "propagated")

        current = filtered_actions.get(action_token)
        if current is not None and current[1] in {"assigned", "initialization"}:
            continue

        if edge.label_tokens:
            for label in edge.label_tokens:
                if label not in filtered_edges:
                    continue
                severity, origin = filtered_edges[label]
                if should_replace_risk(filtered_actions.get(action_token), severity, origin):
                    filtered_actions[action_token] = (severity, origin)
        else:
            if should_replace_risk(filtered_actions.get(action_token), subject_severity, "propagated"):
                filtered_actions[action_token] = (subject_severity, "propagated")

    cascade_terminal: set[str] = set()
    for edge in topo.edges:
        if edge.source in topo.action_ids and edge.target in topo.subject_ids:
            source_token = topo.action_name_by_id.get(edge.source, "")
            if source_token not in filtered_actions:
                continue
            act_severity, _ = filtered_actions[source_token]
            for label in edge.label_tokens:
                if label not in filtered_edges:
                    filtered_edges[label] = (act_severity, "propagated")
            if should_replace_risk(subject_levels.get(edge.target), act_severity, "propagated"):
                subject_levels[edge.target] = (act_severity, "propagated")
                cascade_terminal.add(edge.target)

    return filtered_actions, filtered_edges, subject_levels, cascade_terminal


def propagate_risk_from_subjects(
    topo: Topology,
    edge_levels: dict[str, tuple[str, str]],
    subject_levels: dict[str, tuple[str, str]],
    skip_subjects: set[str] | None = None,
) -> None:
    """Extend edge_levels with risk from colored subjects on outgoing arcs only."""
    for edge in topo.edges:
        subject_id = edge.source
        if subject_id not in subject_levels:
            continue
        if skip_subjects and subject_id in skip_subjects:
            continue
        if edge.target in topo.action_ids:
            target_token = topo.action_name_by_id.get(edge.target, "")
            if FEEDBACK_ACTION_PATTERN.match(target_token):
                continue
        severity, _ = subject_levels[subject_id]
        for label in edge.label_tokens:
            if label not in edge_levels:
                edge_levels[label] = (severity, "propagated")


def parse_risk_edge(risk: str) -> tuple[str, str] | None:
    match = RISK_EDGE_PATTERN.search(risk)
    return (match.group(1), match.group(2)) if match else None


def parse_risk_action_name(risk: str) -> str | None:
    parsed_edge = parse_risk_edge(risk)
    return parsed_edge[0] if parsed_edge else None


def parse_fired_action_name(action_text: str) -> str | None:
    match = CPN_ACTION_PATTERN.search(action_text)
    return match.group(1) if match else None


def build_progressive_stage_risks(
    risk_strings: list[str],
    states: List[ExecutionState],
    development_cycles: int,
    feedback: bool,
) -> dict[tuple[int, int], list[str]]:
    """Build cumulative per-(cycle, stage-index) risk strings from states.

    Stage 0 ("Initial") maps to risks from initialization-time actions.
    Each later stage accumulates risks introduced by fired actions up through
    that checkpoint.
    """
    risks_by_action: dict[str, list[str]] = {}
    for risk in risk_strings:
        action_name = parse_risk_action_name(risk)
        if action_name is not None:
            risks_by_action.setdefault(action_name, []).append(risk)

    fired_actions_by_cycle_stage: dict[tuple[int, str], set[str]] = {}
    for state in states:
        action_name = parse_fired_action_name(state.action)
        if action_name is not None:
            key = (state.cycle_index, state.stage)
            fired_actions_by_cycle_stage.setdefault(key, set()).add(action_name)

    ordered_stages = ordered_stage_names(feedback)
    stage_indexes = {name: idx for idx, name in enumerate(ordered_stages)}

    init_risks: list[str] = []
    seen_init: set[str] = set()
    for action_name, risks in risks_by_action.items():
        if action_name.endswith(".Initialize"):
            for risk in risks:
                if risk not in seen_init:
                    seen_init.add(risk)
                    init_risks.append(risk)

    progressive: dict[tuple[int, int], list[str]] = {}
    for cycle_index in range(1, development_cycles + 1):
        cumulative_actions: set[str] = set()
        progressive[(cycle_index, 0)] = init_risks
        for stage_name in ordered_stages[1:]:
            cumulative_actions.update(
                fired_actions_by_cycle_stage.get((cycle_index, stage_name), set())
            )
            seen: set[str] = set(init_risks)
            stage_risks: list[str] = list(init_risks)
            for action_name in cumulative_actions:
                for risk in risks_by_action.get(action_name, []):
                    if risk not in seen:
                        seen.add(risk)
                        stage_risks.append(risk)
            progressive[(cycle_index, stage_indexes[stage_name])] = stage_risks

    return progressive


def aggregate_risk_strings(states: List[ExecutionState]) -> list[str]:
    """Collect unique delta risk strings from all ExecutionState steps in order."""
    seen: set[str] = set()
    result: list[str] = []
    for state in states:
        for risk in state.risks:
            if risk not in seen:
                seen.add(risk)
                result.append(risk)
    return result


def exclude_feedback_risks(risk_strings: list[str]) -> list[str]:
    """Drop risk strings that originate from any Feedback stage edge."""
    return [risk for risk in risk_strings if not FEEDBACK_EDGE_PATTERN.search(risk)]
