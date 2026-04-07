from __future__ import annotations

"""Model 2.0 simulation engine and compatibility execution entrypoints."""

from dataclasses import dataclass
from typing import Dict, List

from .execution import ExecutionState
from .model import (
    Confidentiality,
    Continuity,
    Correctness,
    Credibility,
    Edge,
    EdgeType,
    System,
)


@dataclass(frozen=True)
class TokenColor:
    confidentiality: Confidentiality | None
    credibility: Credibility | None
    correctness: Correctness
    continuity: Continuity


def _classify_stage(edge_name: str) -> str:
    """Classify edge into lifecycle stage based on edge name prefix."""
    if edge_name.startswith("R"):
        # Response and feedback stages
        if edge_name in {"R1.Respond", "R2.Respond", "R3.Respond"}:
            return "Response"
        else:  # R4, R5, R6, R7
            return "Feedback"
    elif edge_name.startswith("ComponentOf"):
        return "Structural"
    else:
        # Parse numeric prefix: 1-3=Development, 4-9=Deployment, 10-13=Inference
        try:
            prefix = edge_name.split(".")[0]
            num = int(prefix)
            if 1 <= num <= 3:
                return "Development"
            elif 4 <= num <= 9:
                return "Deployment"
            elif 10 <= num <= 13:
                return "Inference"
        except (ValueError, IndexError):
            pass
    return "Other"


def _sort_key(edge_name: str) -> tuple:
    """Generate a sort key for edge ordering."""
    stage_order = {
        "Development": 0,
        "Deployment": 1,
        "Inference": 2,
        "Response": 3,
        "Feedback": 4,
        "Structural": 5,
        "Other": 6,
    }
    stage = _classify_stage(edge_name)
    try:
        # Extract numeric prefix for in-stage ordering.
        prefix = edge_name.split(".")[0]
        # Handle R-prefixed edges separately.
        if prefix.startswith("R"):
            num = int(prefix[1:]) + 100
        else:
            num = int(prefix)
    except (ValueError, IndexError):
        num = 999
    return (stage_order.get(stage, 100), num)


def _enum_from_level(enum_cls, level_value: int):
    for member in enum_cls:
        if member.level().value == level_value:
            return member
    raise ValueError(f"No {enum_cls.__name__} member for level={level_value}")


def _level_min(values: List[int], fallback: int = 2) -> int:
    return min(values) if values else fallback


def _node_token_color(node) -> TokenColor:
    if node.is_subject:
        s = node.as_subject()
        return TokenColor(
            confidentiality=None,
            credibility=s.credibility,
            correctness=s.correctness,
            continuity=s.continuity,
        )
    o = node.as_object()
    return TokenColor(
        confidentiality=o.confidentiality,
        credibility=None,
        correctness=o.correctness,
        continuity=o.continuity,
    )


def _edge_token_color(edge: Edge) -> TokenColor:
    return TokenColor(
        confidentiality=edge.attributes.confidentiality,
        credibility=None,
        correctness=edge.attributes.correctness,
        continuity=edge.attributes.continuity,
    )


def _color_brief(color: TokenColor) -> str:
    conf = color.confidentiality.value if color.confidentiality else "N/A"
    cred = color.credibility.value if color.credibility else "N/A"
    return (
        f"conf={conf},cred={cred},corr={color.correctness.value},cont={color.continuity.value}"
    )


def _fire_act_transition(graph, edge: Edge, marking: Dict[str, TokenColor], acted_on_by_map: Dict[str, List[Edge]]) -> tuple[str, TokenColor]:
    actor = edge.source
    output = edge.target
    op_name = edge.name

    input_nodes: List[str] = []
    for input_edge in acted_on_by_map.get(op_name, []):
        if input_edge.target == actor:
            input_nodes.append(input_edge.source)

    actor_color = marking.get(actor, _node_token_color(graph.nodes[actor]))
    edge_color = _edge_token_color(edge)
    input_colors = [marking.get(name, _node_token_color(graph.nodes[name])) for name in input_nodes]

    output_node = graph.nodes[output]

    corr_levels = [actor_color.correctness.level().value, edge_color.correctness.level().value]
    corr_levels.extend(token.correctness.level().value for token in input_colors)
    out_corr = _enum_from_level(Correctness, _level_min(corr_levels, fallback=2))

    cont_levels = [actor_color.continuity.level().value, edge_color.continuity.level().value]
    cont_levels.extend(token.continuity.level().value for token in input_colors)
    out_cont = _enum_from_level(Continuity, _level_min(cont_levels, fallback=2))

    if output_node.is_subject:
        designated = _node_token_color(output_node)
        out_color = TokenColor(
            confidentiality=None,
            credibility=designated.credibility,
            correctness=out_corr,
            continuity=out_cont,
        )
    else:
        conf_levels: List[int] = [edge_color.confidentiality.level().value]
        if actor_color.credibility is not None:
            conf_levels.append(actor_color.credibility.level().value)
        conf_levels.extend(
            token.confidentiality.level().value
            for token in input_colors
            if token.confidentiality is not None
        )
        out_conf = _enum_from_level(Confidentiality, _level_min(conf_levels, fallback=2))
        out_color = TokenColor(
            confidentiality=out_conf,
            credibility=None,
            correctness=out_corr,
            continuity=out_cont,
        )

    marking[output] = out_color

    method_name = op_name.split(".")[-1] if "." in op_name else op_name
    inputs_str = ", ".join(input_nodes)
    action = (
        f"CPN[{op_name}] {output} = {actor}.{method_name}({inputs_str}) "
        f"=> {{{_color_brief(out_color)}}}"
    )
    return action, out_color


def _fire_respond_transition(graph, edge: Edge, marking: Dict[str, TokenColor]) -> tuple[str, TokenColor]:
    source_color = marking.get(edge.source, _node_token_color(graph.nodes[edge.source]))
    target_node = graph.nodes[edge.target]
    target_color = marking.get(edge.target, _node_token_color(target_node))
    edge_color = _edge_token_color(edge)

    corr_levels = [source_color.correctness.level().value, edge_color.correctness.level().value, target_color.correctness.level().value]
    cont_levels = [source_color.continuity.level().value, edge_color.continuity.level().value, target_color.continuity.level().value]
    out_corr = _enum_from_level(Correctness, _level_min(corr_levels, fallback=2))
    out_cont = _enum_from_level(Continuity, _level_min(cont_levels, fallback=2))

    if target_node.is_subject:
        designated = _node_token_color(target_node)
        out_color = TokenColor(
            confidentiality=None,
            credibility=designated.credibility,
            correctness=out_corr,
            continuity=out_cont,
        )
    else:
        designated = _node_token_color(target_node)
        out_color = TokenColor(
            confidentiality=designated.confidentiality,
            credibility=None,
            correctness=out_corr,
            continuity=out_cont,
        )

    marking[edge.target] = out_color
    action = (
        f"CPN[{edge.name}] {edge.source}.Respond({edge.target}) "
        f"=> {{{_color_brief(out_color)}}}"
    )
    return action, out_color


def run_cpn_cycles(
    system: System,
    development_cycles: int = 1,
    feedback: bool = True,
    base_violation_strs: list[str] | None = None,
    base_risk_strs: list[str] | None = None,
) -> List[ExecutionState]:
    """Run Model 2.0 execution using Colored Petri Net transition firing.

    The API name is kept for backward compatibility with existing CLI integrations.
    """
    graph = system.graph

    # Group edges by stage.
    stages: Dict[str, List] = {
        "Development": [],
        "Deployment": [],
        "Inference": [],
        "Response": [],
        "Feedback": [],
        "Structural": [],
    }

    for edge in graph.edges:
        stage = _classify_stage(edge.name)
        if stage in stages:
            stages[stage].append(edge)

    # Sort edges within each stage by their numeric prefix.
    for stage_edges in stages.values():
        stage_edges.sort(key=lambda e: _sort_key(e.name))

    # Build a mapping: edge_name -> list of ACTED_ON_BY edges with that name
    acted_on_by_map: Dict[str, List] = {}
    for edge in graph.edges:
        if edge.type == EdgeType.ACTED_ON_BY:
            if edge.name not in acted_on_by_map:
                acted_on_by_map[edge.name] = []
            acted_on_by_map[edge.name].append(edge)

    all_states: List[ExecutionState] = []
    marking: Dict[str, TokenColor] = {
        name: _node_token_color(node) for name, node in graph.nodes.items()
    }
    # Human-readable execution traces are 1-based.
    step_index = 1

    # Simulation reuses precomputed analysis strings to keep this module decoupled.
    if base_violation_strs is None:
        base_violation_strs = []
    if base_risk_strs is None:
        base_risk_strs = []

    def _create_execution_state(cycle_index: int, stage_name: str, action: str) -> ExecutionState:
        """Create an execution state using cached analysis results."""
        return ExecutionState(
            step_index=step_index,
            cycle_index=cycle_index,
            stage=stage_name,
            action=action,
            violations=base_violation_strs,
            risks=base_risk_strs,
        )

    def _process_stage(cycle_index: int, stage_name: str, edges: List) -> None:
        """Fire stage transitions and emit colored-token state snapshots."""
        nonlocal step_index
        processed_names: set = set()

        for edge in edges:
            if edge.type == EdgeType.ACT:
                # Skip ComponentOf and Respond edges; they're handled separately.
                if edge.name == "ComponentOf" or edge.name.startswith("R"):
                    continue

                # Avoid duplicate processing of the same operation.
                if edge.name in processed_names:
                    continue
                processed_names.add(edge.name)

                action, _ = _fire_act_transition(graph, edge, marking, acted_on_by_map)
                all_states.append(_create_execution_state(cycle_index, stage_name, action))
                step_index += 1

            elif edge.type == EdgeType.RESPOND:
                action, _ = _fire_respond_transition(graph, edge, marking)
                all_states.append(_create_execution_state(cycle_index, stage_name, action))
                step_index += 1

    for cycle in range(1, development_cycles + 1):
        _process_stage(cycle, "Development", stages["Development"])
        _process_stage(cycle, "Deployment", stages["Deployment"])
        _process_stage(cycle, "Inference", stages["Inference"])
        _process_stage(cycle, "Response", stages["Response"])
        if feedback:
            _process_stage(cycle, "Feedback", stages["Feedback"])

    return all_states


