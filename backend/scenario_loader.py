"""Load scenario files and construct system instances."""

from __future__ import annotations

"""Scenario override loading with backward-compatible schema for Model 2.0 runs."""

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
    "Act": EdgeType.ACT,
    "ActedOnBy": EdgeType.ACTED_ON_BY,
    "Respond": EdgeType.RESPOND,
    "ComponentOf": EdgeType.COMPONENT_OF,
}


def _normalize_enum_token(token: str) -> str:
    token = token.strip()
    aliases = {
        "Public": "NonConfidential",
        "Mixed": "MixedCredibility",
    }
    return aliases.get(token, token)


def _parse_enum(enum_cls, value: str, enum_mapping: dict[str, Any]) -> Any:
    """Generic enum parser: normalize token, look up in mapping, raise on mismatch."""
    normalized = _normalize_enum_token(value)
    if normalized not in enum_mapping:
        raise ValueError(f"Invalid {enum_cls.__name__} value: {value}")
    return enum_mapping[normalized]


def _parse_credibility(value: str) -> Credibility:
    return _parse_enum(Credibility, value, _CREDIBILITY_MAP)


def _parse_confidentiality(value: str) -> Confidentiality:
    return _parse_enum(Confidentiality, value, _CONFIDENTIALITY_MAP)


def _parse_correctness(value: str) -> Correctness:
    return _parse_enum(Correctness, value, _CORRECTNESS_MAP)


def _parse_continuity(value: str) -> Continuity:
    return _parse_enum(Continuity, value, _CONTINUITY_MAP)


def _parse_edge_type(value: str) -> EdgeType:
    return _parse_enum(EdgeType, value, _EDGE_TYPE_MAP)


def _resolve_attr(updates: dict[str, Any], key: str, current_value: str, parser) -> Any:
    return parser(updates.get(key, current_value))


def _merge_edge_attributes(current: EdgeAttributes, updates: dict[str, Any]) -> EdgeAttributes:
    return EdgeAttributes(
        confidentiality=_resolve_attr(updates, "confidentiality", current.confidentiality.value, _parse_confidentiality),
        correctness=_resolve_attr(updates, "correctness", current.correctness.value, _parse_correctness),
        continuity=_resolve_attr(updates, "continuity", current.continuity.value, _parse_continuity),
    )


def _update_node_attributes(node: Node, attrs: dict[str, Any]) -> Node:
    """Update node attributes (subject or object) from attribute dict."""
    if node.is_subject:
        current = node.as_subject()
        updated = SubjectNodeAttributes(
            credibility=_resolve_attr(attrs, "credibility", current.credibility.value, _parse_credibility),
            correctness=_resolve_attr(attrs, "correctness", current.correctness.value, _parse_correctness),
            continuity=_resolve_attr(attrs, "continuity", current.continuity.value, _parse_continuity),
        )
        return replace(node, subject_attributes=updated)
    else:
        current = node.as_object()
        updated = ObjectNodeAttributes(
            confidentiality=_resolve_attr(attrs, "confidentiality", current.confidentiality.value, _parse_confidentiality),
            correctness=_resolve_attr(attrs, "correctness", current.correctness.value, _parse_correctness),
            continuity=_resolve_attr(attrs, "continuity", current.continuity.value, _parse_continuity),
        )
        return replace(node, object_attributes=updated)


def remove_edge_pairs(system: System, removals: list[dict[str, Any]]) -> System:
    """Remove matching operation edge pairs from the system graph.

    Each removal entry supports:
    - name: required edge operation name, such as "6.Upload" or "9.Assemble"
    - source: optional exact source-node filter
    - target: optional exact target-node filter
    - types: optional list of edge types to remove, defaults to ["Act", "ActedOnBy"]
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
        raw_types = removal.get("types", ["Act", "ActedOnBy"])
        if not isinstance(raw_types, list) or not raw_types:
            raise ValueError(f"edge_pair_omissions.types must be a non-empty list for name={name}")
        parsed_types = {_parse_edge_type(raw_type) for raw_type in raw_types}

        matched = False
        remaining = []
        for edge in filtered_edges:
            is_match = edge.name == name and edge.type in parsed_types
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

    for node_patch in payload.get("node_overrides", []):
        name = node_patch.get("name")
        if not name or name not in graph.nodes:
            raise ValueError(f"node_overrides entry references unknown node: {name}")
        if name == "IntelligentSystem":
            raise ValueError(
                "IntelligentSystem attributes are fully inferred from dependencies and cannot be overridden"
            )
        node = graph.nodes[name]
        attrs = node_patch.get("attributes", {})
        graph.nodes[name] = _update_node_attributes(node, attrs)

    edge_default_attrs_raw = payload.get("edge_default_attributes")
    if edge_default_attrs_raw:
        default_attrs = _merge_edge_attributes(system.graph.edges[0].attributes, edge_default_attrs_raw)
        graph.edges = [replace(edge, attributes=default_attrs) for edge in graph.edges]

    edge_pair_omissions = payload.get("edge_pair_omissions", [])
    remove_edge_pairs(system, edge_pair_omissions)

    for edge_patch in payload.get("edge_overrides", []):
        source = edge_patch.get("source")
        target = edge_patch.get("target")
        name = edge_patch.get("name")
        edge_type = edge_patch.get("type")
        parsed_edge_type = _parse_edge_type(edge_type) if edge_type is not None else None
        updates = edge_patch.get("attributes", {})

        matched = False
        for idx, edge in enumerate(graph.edges):
            if source is not None and edge.source != source:
                continue
            if target is not None and edge.target != target:
                continue
            if name is not None and edge.name != name:
                continue
            if parsed_edge_type is not None and edge.type != parsed_edge_type:
                continue
            graph.edges[idx] = replace(edge, attributes=_merge_edge_attributes(edge.attributes, updates))
            matched = True

        if not matched:
            raise ValueError(
                "edge_overrides entry did not match any edge: "
                f"source={source}, target={target}, name={name}, type={edge_type}"
            )

    dep_overrides = payload.get("dependency_overrides")
    if dep_overrides:
        for subject_name, object_names in dep_overrides.items():
            if subject_name not in graph.nodes:
                raise ValueError(f"dependency_overrides references unknown node: {subject_name}")
            system.dependencies[subject_name] = set(object_names)

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


def load_scenario_from_file(filepath: str) -> System:
    """Load a scenario from file and return a System.

    Supported formats:
    - .yaml/.yml: override-based scenario definitions on top of default system
    - .md: currently falls back to default system
    
    Searches in: current directory, docs/ subdirectory.
    """
    path = Path(filepath)
    if not path.exists():
        # Try docs/ subdirectory
        alt_path = Path("docs") / filepath
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(f"Scenario file not found: {filepath}")

    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _load_yaml_scenario(path)
    if suffix == ".md":
        return build_default_system()

    raise ValueError(f"Unsupported scenario format: {path.suffix}")


def get_available_scenarios() -> list[str]:
    """List available scenario files in the framework directory and docs subdirectory."""
    framework_dir = Path(__file__).parent.parent

    def _collect_scenarios(directory: Path) -> list[str]:
        names: list[str] = []
        if not directory.exists():
            return names
        for ext in ("*.md", "*.yaml", "*.yml"):
            for scenario_file in directory.glob(ext):
                lowered = scenario_file.name.lower()
                if lowered.startswith("scenario") and "readme" not in lowered:
                    names.append(scenario_file.name)
        return names

    scenarios = _collect_scenarios(framework_dir)
    scenarios.extend(_collect_scenarios(framework_dir / "docs"))

    return sorted(set(scenarios))
