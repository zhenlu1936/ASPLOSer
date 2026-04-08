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
    System,
    is_object_to_subject_edge,
    is_subject_to_object_edge,
    level_to_enum_member,
    stage_sort_key,
)
from .security_aggregation import min_level


@dataclass(frozen=True)
class TokenColor:
    confidentiality: Confidentiality | None
    credibility: Credibility | None
    correctness: Correctness
    continuity: Continuity


def _build_token_color(
    correctness: Correctness,
    continuity: Continuity,
    confidentiality: Confidentiality | None = None,
    credibility: Credibility | None = None,
) -> TokenColor:
    return TokenColor(
        confidentiality=confidentiality,
        credibility=credibility,
        correctness=correctness,
        continuity=continuity,
    )


def _node_token_color(node) -> TokenColor:
    if node.is_subject:
        s = node.as_subject()
        return _build_token_color(
            credibility=s.credibility,
            correctness=s.correctness,
            continuity=s.continuity,
        )
    o = node.as_object()
    return _build_token_color(
        confidentiality=o.confidentiality,
        correctness=o.correctness,
        continuity=o.continuity,
    )


def _edge_token_color(edge: Edge) -> TokenColor:
    return _build_token_color(
        confidentiality=edge.attributes.confidentiality,
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
    op_name = edge.action

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
    out_corr = level_to_enum_member(Correctness, min_level(corr_levels))

    cont_levels = [actor_color.continuity.level().value, edge_color.continuity.level().value]
    cont_levels.extend(token.continuity.level().value for token in input_colors)
    out_cont = level_to_enum_member(Continuity, min_level(cont_levels))

    if output_node.is_subject:
        designated = _node_token_color(output_node)
        out_color = _build_token_color(
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
        out_conf = level_to_enum_member(Confidentiality, min_level(conf_levels))
        out_color = _build_token_color(
            confidentiality=out_conf,
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
    out_corr = level_to_enum_member(Correctness, min_level(corr_levels))
    out_cont = level_to_enum_member(Continuity, min_level(cont_levels))

    if target_node.is_subject:
        designated = _node_token_color(target_node)
        out_color = _build_token_color(
            credibility=designated.credibility,
            correctness=out_corr,
            continuity=out_cont,
        )
    else:
        designated = _node_token_color(target_node)
        out_color = _build_token_color(
            confidentiality=designated.confidentiality,
            correctness=out_corr,
            continuity=out_cont,
        )

    marking[edge.target] = out_color
    action = (
        f"CPN[{edge.action}] {edge.source}.Respond({edge.target}) "
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

    # Group actions by stage, then resolve the corresponding object-flow edges.
    stage_actions: Dict[str, List[str]] = {
        "Development": [],
        "Deployment": [],
        "Operation": [],
        "Feedback": [],
    }

    for action in graph.actions.values():
        if action.stage in stage_actions:
            stage_actions[action.stage].append(action.name)

    for action_names in stage_actions.values():
        action_names.sort(key=stage_sort_key)

    stages: Dict[str, List] = {
        "Development": [],
        "Deployment": [],
        "Operation": [],
        "Feedback": [],
    }

    edges_by_action: Dict[str, List] = {}
    for edge in graph.edges:
        edges_by_action.setdefault(edge.action, []).append(edge)

    for stage_name, action_names in stage_actions.items():
        for action_name in action_names:
            stages[stage_name].extend(edges_by_action.get(action_name, []))

    # Build a mapping: action_name -> object->subject edges (potential action inputs)
    acted_on_by_map: Dict[str, List] = {}
    for edge in graph.edges:
        if is_object_to_subject_edge(edge, graph):
            if edge.action not in acted_on_by_map:
                acted_on_by_map[edge.action] = []
            acted_on_by_map[edge.action].append(edge)

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
            if edge.action in processed_names:
                continue
            processed_names.add(edge.action)

            action_edges = [item for item in edges if item.action == edge.action]
            input_edges = [item for item in action_edges if is_object_to_subject_edge(item, graph)]
            actor_subjects = {item.target for item in input_edges}
            if not actor_subjects:
                actor_subjects = {item.source for item in action_edges if graph.nodes[item.source].is_subject}

            output_edges = [
                item
                for item in action_edges
                if is_subject_to_object_edge(item, graph) and item.source in actor_subjects
            ]
            if not output_edges:
                output_edges = [
                    item
                    for item in action_edges
                    if graph.nodes[item.source].is_subject and graph.nodes[item.target].is_subject and item.source in actor_subjects
                ]

            for output_edge in output_edges:
                action_text, _ = _fire_act_transition(graph, output_edge, marking, acted_on_by_map)
                all_states.append(_create_execution_state(cycle_index, stage_name, action_text))
                step_index += 1

            respond_edges = [
                item
                for item in action_edges
                if item not in output_edges and item not in input_edges and item.target not in actor_subjects
            ]
            for respond_edge in respond_edges:
                action_text, _ = _fire_respond_transition(graph, respond_edge, marking)
                all_states.append(_create_execution_state(cycle_index, stage_name, action_text))
                step_index += 1

    for cycle in range(1, development_cycles + 1):
        _process_stage(cycle, "Development", stages["Development"])
        _process_stage(cycle, "Deployment", stages["Deployment"])
        _process_stage(cycle, "Operation", stages["Operation"])
        if feedback:
            _process_stage(cycle, "Feedback", stages["Feedback"])

    return all_states


