from __future__ import annotations

"""Scenario override loading for Model 2.0 runs."""

from dataclasses import replace
from pathlib import Path
from typing import Any

from .instance import build_default_system
from .instance import infer_subject_attributes_from_assets
from .model import (
    Confidentiality,
    Continuity,
    Correctness,
    Credibility,
    EdgeAttributes,
    EdgeType,
    Node,
    ObjectNodeAttributes,
    SubjectNodeAttributes,
    System,
)


_CREDIBILITY_MAP = {
    "Untrusted": Credibility.UNTRUSTED,
    "MixedCredibility": Credibility.MIXED_CREDIBILITY,
    "Trusted": Credibility.TRUSTED,
}

_CONFIDENTIALITY_MAP = {
    "NonConfidential": Confidentiality.NON_CONFIDENTIAL,
    "MixedConfidentiality": Confidentiality.MIXED_CONFIDENTIALITY,
    "Confidential": Confidentiality.CONFIDENTIAL,
}

_CORRECTNESS_MAP = {
    "Incorrect": Correctness.INCORRECT,
    "MixedCorrectness": Correctness.MIXED_CORRECTNESS,
    "Correct": Correctness.CORRECT,
}

_CONTINUITY_MAP = {
    "Discontinuous": Continuity.DISCONTINUOUS,
    "MixedContinuity": Continuity.MIXED_CONTINUITY,
    "Continuous": Continuity.CONTINUOUS,
}

_EDGE_TYPE_MAP = {
    "ObjectArc": EdgeType.OBJECT_ARC,
}

_ENUM_MAPPING_BY_CLASS: dict[type, dict[str, Any]] = {
    Credibility: _CREDIBILITY_MAP,
    Confidentiality: _CONFIDENTIALITY_MAP,
    Correctness: _CORRECTNESS_MAP,
    Continuity: _CONTINUITY_MAP,
    EdgeType: _EDGE_TYPE_MAP,
}


def _parse_enum(enum_cls, value: str, enum_mapping: dict[str, Any]) -> Any:
    """Generic enum parser: strict token lookup against canonical values."""
    token = value.strip()
    if token not in enum_mapping:
        raise ValueError(f"Invalid {enum_cls.__name__} value: {value}")
    return enum_mapping[token]


def _parse_enum_value(enum_cls: type, value: str) -> Any:
    enum_mapping = _ENUM_MAPPING_BY_CLASS.get(enum_cls)
    if enum_mapping is None:
        raise ValueError(f"Unsupported enum class: {enum_cls}")
    return _parse_enum(enum_cls, value, enum_mapping)


def _resolve_attr(updates: dict[str, Any], key: str, current_value: str, enum_cls: type) -> Any:
    return _parse_enum_value(enum_cls, updates.get(key, current_value))


def _merge_edge_attributes(current: EdgeAttributes, updates: dict[str, Any]) -> EdgeAttributes:
    return EdgeAttributes(
        confidentiality=_resolve_attr(updates, "confidentiality", current.confidentiality.value, Confidentiality),
        correctness=_resolve_attr(updates, "correctness", current.correctness.value, Correctness),
        continuity=_resolve_attr(updates, "continuity", current.continuity.value, Continuity),
    )


def _update_node_attributes(node: Node, attrs: dict[str, Any]) -> Node:
    """Update node attributes (subject or object) from attribute dict."""
    if node.is_subject:
        current = node.as_subject()
        updated = SubjectNodeAttributes(
            credibility=_resolve_attr(attrs, "credibility", current.credibility.value, Credibility),
            correctness=_resolve_attr(attrs, "correctness", current.correctness.value, Correctness),
            continuity=_resolve_attr(attrs, "continuity", current.continuity.value, Continuity),
        )
        return replace(node, subject_attributes=updated)
    else:
        current = node.as_object()
        updated = ObjectNodeAttributes(
            confidentiality=_resolve_attr(attrs, "confidentiality", current.confidentiality.value, Confidentiality),
            correctness=_resolve_attr(attrs, "correctness", current.correctness.value, Correctness),
            continuity=_resolve_attr(attrs, "continuity", current.continuity.value, Continuity),
        )
        return replace(node, object_attributes=updated)


def _apply_node_overrides(graph, node_overrides: list[dict[str, Any]]) -> None:
    for node_patch in node_overrides:
        name = node_patch.get("name")
        if not name or name not in graph.nodes:
            raise ValueError(f"node_overrides entry references unknown node: {name}")
        attrs = node_patch.get("attributes", {})
        graph.nodes[name] = _update_node_attributes(graph.nodes[name], attrs)


def _apply_default_edge_attributes(graph, raw_attrs: dict[str, Any] | None) -> None:
    if not raw_attrs:
        return
    default_attrs = _merge_edge_attributes(graph.edges[0].attributes, raw_attrs)
    graph.edges = [replace(edge, attributes=default_attrs) for edge in graph.edges]


def _edge_matches_patch(edge, source, target, name, parsed_edge_type) -> bool:
    if source is not None and edge.source != source:
        return False
    if target is not None and edge.target != target:
        return False
    if name is not None and edge.action != name:
        return False
    if parsed_edge_type is not None and edge.type != parsed_edge_type:
        return False
    return True


def _apply_initialize_edge_overrides(graph, edge_overrides: list[dict[str, Any]]) -> None:
    for edge_patch in edge_overrides:
        source = edge_patch.get("source")
        target = edge_patch.get("target")
        name = edge_patch.get("name")
        edge_type = edge_patch.get("type")
        parsed_edge_type = _parse_enum_value(EdgeType, edge_type) if edge_type is not None else None
        updates = edge_patch.get("attributes", {})

        matched = False
        for idx, edge in enumerate(graph.edges):
            if not _edge_matches_patch(edge, source, target, name, parsed_edge_type):
                continue
            graph.edges[idx] = replace(edge, attributes=_merge_edge_attributes(edge.attributes, updates))
            matched = True

        if not matched:
            raise ValueError(
                "initialize_edge_overrides entry did not match any edge: "
                f"source={source}, target={target}, name={name}, type={edge_type}"
            )


def _apply_dependency_overrides(system: System, dep_overrides: dict[str, Any] | None) -> None:
    if not dep_overrides:
        return
    graph = system.graph
    for subject_name, object_names in dep_overrides.items():
        if subject_name not in graph.nodes:
            raise ValueError(f"dependency_overrides references unknown node: {subject_name}")
        system.dependencies[subject_name] = set(object_names)


def remove_edge_pairs(system: System, removals: list[dict[str, Any]]) -> System:
    """Remove matching operation edge pairs from the system graph.

    Each removal entry supports:
    - name: required edge operation name, such as "A2.Upload" or "D2.Delopy"
    - source: optional exact source-node filter
    - target: optional exact target-node filter
    - types: optional list of edge types to remove, defaults to ["ObjectArc"]
    """
    if not removals:
        return system

    filtered_edges = system.graph.edges
    for removal in removals:
        name = removal.get("name")
        if not name:
            raise ValueError("edge_pair_omissions entry requires a name")

        source = removal.get("source")
        target = removal.get("target")
        raw_types = removal.get("types", ["ObjectArc"])
        if not isinstance(raw_types, list) or not raw_types:
            raise ValueError(f"edge_pair_omissions.types must be a non-empty list for name={name}")
        parsed_types = {_parse_enum_value(EdgeType, raw_type) for raw_type in raw_types}

        matched = False
        remaining = []
        for edge in filtered_edges:
            is_match = edge.action == name and edge.type in parsed_types
            if is_match and source is not None:
                is_match = edge.source == source
            if is_match and target is not None:
                is_match = edge.target == target

            if is_match:
                matched = True
                continue
            remaining.append(edge)

        if not matched:
            raise ValueError(
                "edge_pair_omissions entry did not match any edge: "
                f"source={source}, target={target}, name={name}, types={raw_types}"
            )
        filtered_edges = remaining

    system.graph.edges = filtered_edges
    return system


def _apply_yaml_overrides(system: System, payload: dict[str, Any]) -> System:
    graph = system.graph

    if "edge_default_attributes" in payload or "edge_overrides" in payload:
        raise ValueError(
            "Legacy edge override keys are not supported. "
            "Use initialize_edge_default_attributes and initialize_edge_overrides."
        )

    _apply_node_overrides(graph, payload.get("node_overrides", []))
    _apply_default_edge_attributes(graph, payload.get("initialize_edge_default_attributes"))

    edge_pair_omissions = payload.get("edge_pair_omissions", [])
    remove_edge_pairs(system, edge_pair_omissions)

    _apply_initialize_edge_overrides(graph, payload.get("initialize_edge_overrides", []))
    _apply_dependency_overrides(system, payload.get("dependency_overrides"))

    # Always infer these subject attributes from dependencies, even if user overrides exist.
    infer_subject_attributes_from_assets(system)

    return system


def _load_yaml_scenario(path: Path) -> System:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "YAML scenario support requires PyYAML. Install with: pip install pyyaml"
        ) from exc

    with path.open("r", encoding="utf-8") as f:
        payload = yaml.safe_load(f) or {}

    if not isinstance(payload, dict):
        raise ValueError(f"Invalid YAML scenario structure in {path.name}: expected mapping root")

    base = payload.get("base", "default")
    if base != "default":
        raise ValueError(f"Unsupported scenario base: {base}")

    system = build_default_system()
    return _apply_yaml_overrides(system, payload)


def _resolve_scenario_path(filepath: str) -> Path:
    """Resolve scenario path using direct path, docs/scenarios, then docs."""
    path = Path(filepath)
    if path.exists():
        return path

    candidate_paths = [
        Path("docs") / "scenarios" / filepath,
        Path("docs") / filepath,
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Scenario file not found: {filepath}")


def load_scenario_from_file(filepath: str) -> System:
    """Load a scenario from file and return a System.

    Supported formats:
    - .yaml/.yml: override-based scenario definitions on top of default system
    - .md: currently falls back to default system
    
    Searches in: current directory, docs/scenarios/, and docs/.
    """
    path = _resolve_scenario_path(filepath)

    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _load_yaml_scenario(path)
    if suffix == ".md":
        return build_default_system()

    raise ValueError(f"Unsupported scenario format: {path.suffix}")


def get_available_scenarios() -> list[str]:
    """List available scenario files in the framework and docs/scenarios directory."""
    framework_dir = Path(__file__).parent.parent

    def _collect_scenarios(directory: Path) -> list[str]:
        names: list[str] = []
        if not directory.exists():
            return names
        for ext in ("*.yaml", "*.yml"):
            for scenario_file in directory.glob(ext):
                lowered = scenario_file.name.lower()
                if (
                    "readme" not in lowered
                    and "template" not in lowered
                ):
                    names.append(scenario_file.name)
        return names

    scenarios = _collect_scenarios(framework_dir)
    scenarios.extend(_collect_scenarios(framework_dir / "docs" / "scenarios"))
    scenarios.extend(_collect_scenarios(framework_dir / "docs"))

    return sorted(set(scenarios))
