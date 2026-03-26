from __future__ import annotations

from typing import Dict, List

from .execution import ExecutionState
from .model import EdgeType, System


def _classify_stage(edge_name: str) -> str:
    """Classify edge into SSA stage based on edge name prefix."""
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


def run_ssa_cycles(
    system: System,
    development_cycles: int = 1,
    feedback: bool = True,
    base_violation_strs: list[str] | None = None,
    base_risk_strs: list[str] | None = None,
) -> List[ExecutionState]:
    """Simulate the system by traversing the graph edges in SSA-defined stages.
    
    Returns a list of ExecutionState objects tracking each step, violations, and risks.
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
        """Process edges in a given stage, generating SSA-style statements and analyzing after each."""
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

                src = graph.nodes[edge.source]
                tgt = graph.nodes[edge.target]
                
                # Extract method name from edge name (e.g., "1.Process" -> "Process")
                method_name = edge.name.split(".")[-1] if "." in edge.name else edge.name

                # Find all inputs (ACTED_ON_BY edges with the same name where src is the subject).
                inputs = []
                if edge.name in acted_on_by_map:
                    for input_edge in acted_on_by_map[edge.name]:
                        if input_edge.target == edge.source:
                            inputs.append(graph.nodes[input_edge.source].name)

                # Generate SSA-style statement: output = subject.method(inputs...)
                inputs_str = ", ".join(inputs)
                action = f"{tgt.name} = {src.name}.{method_name}({inputs_str})"
                all_states.append(_create_execution_state(cycle_index, stage_name, action))
                step_index += 1

            elif edge.type == EdgeType.RESPOND:
                # Response edges: output.Respond(target)
                src = graph.nodes[edge.source]
                tgt = graph.nodes[edge.target]
                action = f"{src.name}.Respond({tgt.name})"
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
