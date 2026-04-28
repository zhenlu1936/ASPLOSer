from __future__ import annotations

"""Model 2.0 Colored Petri Net simulation engine."""

from dataclasses import dataclass
from typing import Dict, List

from .analysis import evaluate_risks_for_marking_delta
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
from .propagation import SIMULATION_STAGES
from .security_aggregation import min_level


@dataclass(frozen=True)
class TokenColor:
    correctness: Correctness
    continuity: Continuity
    confidentiality: Confidentiality | None = None
    credibility: Credibility | None = None


def _node_token_color(node) -> TokenColor:
    if node.is_subject:
        s = node.as_subject()
        return TokenColor(s.correctness, s.continuity, credibility=s.credibility)
    o = node.as_object()
    return TokenColor(o.correctness, o.continuity, o.confidentiality)


def _edge_token_color(edge: Edge) -> TokenColor:
    return TokenColor(
        edge.attributes.correctness,
        edge.attributes.continuity,
        edge.attributes.confidentiality,
    )


def _color_brief(color: TokenColor) -> str:
    conf = color.confidentiality.value if color.confidentiality else "N/A"
    cred = color.credibility.value if color.credibility else "N/A"
    return (
        f"conf={conf},cred={cred},corr={color.correctness.value},cont={color.continuity.value}"
    )


def _output_corr_cont(
    colors: list[TokenColor],
    edge: Edge,
    designated_corr: Correctness,
) -> tuple[Correctness, Continuity]:
    """Compute output correctness and continuity from a list of input token colors."""
    out_corr = (
        Correctness.CORRECT
        if designated_corr == Correctness.CORRECT
        and edge.attributes.correctness == Correctness.CORRECT
        else level_to_enum_member(Correctness, min_level([c.correctness.level().value for c in colors]))
    )
    out_cont = level_to_enum_member(
        Continuity, min_level([c.continuity.level().value for c in colors])
    )
    return out_corr, out_cont


def _fire_act_transition(graph, edge: Edge, marking: Dict[str, TokenColor], acted_on_by_map: Dict[str, List[Edge]]) -> tuple[str, TokenColor]:
    actor = edge.source
    output = edge.target
    op_name = edge.action

    input_nodes = [e.source for e in acted_on_by_map.get(op_name, []) if e.target == actor]

    # Designated attributes come from graph.nodes (post-scenario, pre-simulation).
    # Current-marking attributes may differ after module degradation propagates.
    actor_designated = _node_token_color(graph.nodes[actor])
    actor_color = marking.get(actor, actor_designated)
    edge_color = _edge_token_color(edge)
    input_colors = [marking.get(name, _node_token_color(graph.nodes[name])) for name in input_nodes]

    output_node = graph.nodes[output]

    out_corr, out_cont = _output_corr_cont(
        [actor_color, edge_color, *input_colors], edge, actor_designated.correctness
    )

    if output_node.is_subject:
        designated = _node_token_color(output_node)
        out_color = TokenColor(out_corr, out_cont, credibility=designated.credibility)
    else:
        conf_levels: List[int] = [edge_color.confidentiality.level().value]
        if actor_color.credibility is not None:
            conf_levels.append(actor_color.credibility.level().value)
        conf_levels.extend(
            token.confidentiality.level().value
            for token in input_colors
            if token.confidentiality is not None
        )
        # Downstream receiver filter: a TRUSTED actor on a CONFIDENTIAL arc
        # absorbs upstream confidentiality degradation and resets output.
        if (
            actor_designated.credibility == Credibility.TRUSTED
            and edge.attributes.confidentiality == Confidentiality.CONFIDENTIAL
        ):
            out_conf = Confidentiality.CONFIDENTIAL
        else:
            out_conf = level_to_enum_member(Confidentiality, min_level(conf_levels))
        out_color = TokenColor(out_corr, out_cont, out_conf)

    marking[output] = out_color

    method_name = op_name.split(".")[-1] if "." in op_name else op_name
    inputs_str = ", ".join(input_nodes)
    action = (
        f"CPN[{op_name}] {output} = {actor}.{method_name}({inputs_str}) "
        f"=> {{{_color_brief(out_color)}}}"
    )
    return action, out_color


def _fire_respond_transition(graph, edge: Edge, marking: Dict[str, TokenColor]) -> tuple[str, TokenColor]:
    source_node = graph.nodes[edge.source]
    source_designated = _node_token_color(source_node)
    source_color = marking.get(edge.source, source_designated)
    target_node = graph.nodes[edge.target]
    target_color = marking.get(edge.target, _node_token_color(target_node))
    edge_color = _edge_token_color(edge)

    out_corr, out_cont = _output_corr_cont(
        [source_color, edge_color, target_color], edge, source_designated.correctness
    )

    if target_node.is_subject:
        designated = _node_token_color(target_node)
        out_color = TokenColor(out_corr, out_cont, credibility=designated.credibility)
    else:
        designated = _node_token_color(target_node)
        out_color = TokenColor(out_corr, out_cont, designated.confidentiality)

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
) -> List[ExecutionState]:
    """Run Model 2.0 execution using Colored Petri Net transition firing.

    Each returned ExecutionState carries:
    - ``risks``: delta risks introduced by THAT transition only (marking-based).
    - ``marking_snapshot``: shallow copy of marking after that transition fires.

    Risks are computed per-step from the CPN marking. Use the ``risks`` fields
    on the returned states or aggregate them in the caller for visualization.
    """
    graph = system.graph

    # Group actions by stage, then resolve the corresponding object-flow edges.
    stage_actions: Dict[str, List[str]] = {stage: [] for stage in SIMULATION_STAGES}

    for action in graph.actions.values():
        if action.stage in stage_actions:
            stage_actions[action.stage].append(action.name)

    for action_names in stage_actions.values():
        action_names.sort(key=stage_sort_key)

    edges_by_action: Dict[str, List] = {}
    for edge in graph.edges:
        edges_by_action.setdefault(edge.action, []).append(edge)

    stages: Dict[str, List] = {
        stage_name: [e for name in action_names for e in edges_by_action.get(name, [])]
        for stage_name, action_names in stage_actions.items()
    }

    # Build a mapping: action_name -> object->subject edges (potential action inputs)
    acted_on_by_map: Dict[str, List] = {}
    for edge in graph.edges:
        if is_object_to_subject_edge(edge, graph):
            acted_on_by_map.setdefault(edge.action, []).append(edge)

    all_states: List[ExecutionState] = []
    marking: Dict[str, TokenColor] = {
        name: _node_token_color(node) for name, node in graph.nodes.items()
    }
    # Human-readable execution traces are 1-based.
    step_index = 1

    if base_violation_strs is None:
        base_violation_strs = []

    def _emit_state(
        cycle_index: int,
        stage_name: str,
        action_text: str,
        target_names: list[str],
        action_name: str,
    ) -> None:
        nonlocal step_index
        delta_risks = evaluate_risks_for_marking_delta(
            graph, marking, target_names, action_name
        )
        all_states.append(ExecutionState(
            step_index=step_index,
            cycle_index=cycle_index,
            stage=stage_name,
            action=action_text,
            violations=base_violation_strs,
            risks=delta_risks,
            marking_snapshot=dict(marking),  # shallow copy — TokenColor is frozen
        ))
        step_index += 1

    def _process_stage(cycle_index: int, stage_name: str, edges: List) -> None:
        """Fire stage transitions and emit colored-token state snapshots."""
        grouped: dict[str, list] = {}
        for e in edges:
            grouped.setdefault(e.action, []).append(e)

        for action_name, action_edges in grouped.items():
            input_edges = [e for e in action_edges if is_object_to_subject_edge(e, graph)]
            actor_subjects = {e.target for e in input_edges}
            if not actor_subjects:
                actor_subjects = {e.source for e in action_edges if graph.nodes[e.source].is_subject}

            output_edges = [
                e for e in action_edges
                if is_subject_to_object_edge(e, graph) and e.source in actor_subjects
            ]
            if not output_edges:
                output_edges = [
                    e for e in action_edges
                    if graph.nodes[e.source].is_subject and graph.nodes[e.target].is_subject and e.source in actor_subjects
                ]

            output_set = {id(e) for e in output_edges}
            input_set = {id(e) for e in input_edges}
            respond_edges = [
                e for e in action_edges
                if id(e) not in output_set and id(e) not in input_set and e.target not in actor_subjects
            ]

            for output_edge in output_edges:
                action_text, _ = _fire_act_transition(graph, output_edge, marking, acted_on_by_map)
                _emit_state(cycle_index, stage_name, action_text, [output_edge.target], output_edge.action)

            for respond_edge in respond_edges:
                action_text, _ = _fire_respond_transition(graph, respond_edge, marking)
                _emit_state(cycle_index, stage_name, action_text, [respond_edge.target], respond_edge.action)

    for cycle in range(1, development_cycles + 1):
        for stage_name in SIMULATION_STAGES:
            if stage_name == "Feedback" and not feedback:
                continue
            _process_stage(cycle, stage_name, stages[stage_name])

    return all_states
