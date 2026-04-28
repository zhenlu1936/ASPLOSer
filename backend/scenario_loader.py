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
    Node,
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

_ENUM_MAPPING_BY_CLASS: dict[type, dict[str, Any]] = {
    Credibility: _CREDIBILITY_MAP,
    Confidentiality: _CONFIDENTIALITY_MAP,
    Correctness: _CORRECTNESS_MAP,
    Continuity: _CONTINUITY_MAP,
}

_SUBJECT_ATTR_SCHEMA = {
    "credibility": Credibility,
    "correctness": Correctness,
    "continuity": Continuity,
}

_OBJECT_ATTR_SCHEMA = {
    "confidentiality": Confidentiality,
    "correctness": Correctness,
    "continuity": Continuity,
}

_EDGE_ATTR_SCHEMA = {
    "confidentiality": Confidentiality,
    "correctness": Correctness,
    "continuity": Continuity,
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


def _merge_attributes(current, updates: dict[str, Any], schema: dict[str, type]):
    parsed = {
        key: _resolve_attr(updates, key, getattr(current, key).value, enum_cls)
        for key, enum_cls in schema.items()
    }
    return replace(current, **parsed)


def _merge_edge_attributes(current: EdgeAttributes, updates: dict[str, Any]) -> EdgeAttributes:
    return _merge_attributes(current, updates, _EDGE_ATTR_SCHEMA)


def _update_node_attributes(node: Node, attrs: dict[str, Any]) -> Node:
    """Update node attributes (subject or object) from attribute dict."""
    if node.is_subject:
        updated = _merge_attributes(node.as_subject(), attrs, _SUBJECT_ATTR_SCHEMA)
        return replace(node, subject_attributes=updated)
    updated = _merge_attributes(node.as_object(), attrs, _OBJECT_ATTR_SCHEMA)
    return replace(node, object_attributes=updated)


def _apply_subject_overrides(graph, subject_overrides: list[dict[str, Any]]) -> None:
    for node_patch in subject_overrides:
        name = node_patch.get("name")
        if not name or name not in graph.nodes:
            raise ValueError(f"subject_overrides entry references unknown node: {name}")
        if not graph.nodes[name].is_subject:
            raise ValueError(f"subject_overrides entry must reference a subject node: {name}")
        attrs = node_patch.get("attributes", {})
        graph.nodes[name] = _update_node_attributes(graph.nodes[name], attrs)


def _apply_action_overrides(graph, action_overrides: list[dict[str, Any]]) -> None:
    for action_patch in action_overrides:
        name = action_patch.get("name")
        if not name or name not in graph.actions:
            raise ValueError(f"action_overrides entry references unknown action: {name}")

        updates = action_patch.get("attributes", {})
        matched = False
        for idx, edge in enumerate(graph.edges):
            if edge.action != name:
                continue
            graph.edges[idx] = replace(edge, attributes=_merge_edge_attributes(edge.attributes, updates))
            matched = True

        if not matched:
            raise ValueError(f"action_overrides entry did not match any object-arc: {name}")


def _edge_matches_init_override(edge, source, target, name) -> bool:
    """Match edge for object_initialization_overrides: source=action, target=subject, name=object."""
    if source is not None and edge.action != source:
        return False
    if target is not None and edge.target != target:
        return False
    if name is not None and edge.name != name:
        return False
    return True


def _edge_key(edge) -> str:
    return f"{edge.action}/{edge.name}"


def _collect_assigned_sets(system: System, payload: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    """Return (assigned_actions, assigned_object_arcs, assigned_subjects).

    assigned_actions: action names from action_overrides or object_initialization_overrides.
    assigned_object_arcs: arc keys from object_initialization_overrides only.
    assigned_subjects: subject names from subject_overrides.
    """
    graph = system.graph
    actions: set[str] = set()
    arcs: set[str] = set()
    subjects: set[str] = set()

    for entry in payload.get("subject_overrides", []):
        name = entry.get("name")
        if name:
            subjects.add(name)

    for entry in payload.get("object_initialization_overrides", []):
        source = entry.get("source")  # action name
        target = entry.get("target")  # subject name
        name = entry.get("name")      # object name (ends with 'P')

        for edge in graph.edges:
            if _edge_matches_init_override(edge, source, target, name):
                arcs.add(_edge_key(edge))
                actions.add(edge.action)

    for action_patch in payload.get("action_overrides", []):
        action_name = action_patch.get("name")
        if action_name:
            actions.add(action_name)

    return actions, arcs, subjects


def _apply_object_initialization_overrides(graph, object_initialization_overrides: list[dict[str, Any]]) -> None:
    for entry in object_initialization_overrides:
        source = entry.get("source")  # action name
        target = entry.get("target")  # subject name
        name = entry.get("name")      # object name (must end with 'P')

        if not name or not name.endswith("P"):
            raise ValueError(
                "object_initialization_overrides entry must reference an initialization "
                f"object (name ending with 'P'): {name}"
            )

        updates = entry.get("attributes", {})

        matched = False
        for idx, edge in enumerate(graph.edges):
            if not _edge_matches_init_override(edge, source, target, name):
                continue
            graph.edges[idx] = replace(edge, attributes=_merge_edge_attributes(edge.attributes, updates))
            matched = True

        if not matched:
            raise ValueError(
                "object_initialization_overrides entry did not match any edge: "
                f"source={source}, target={target}, name={name}"
            )


def _apply_yaml_overrides(system: System, payload: dict[str, Any]) -> System:
    graph = system.graph

    allowed_keys = {
        "base",
        "name",
        "doc_metadata",
        "subject_overrides",
        "action_overrides",
        "object_initialization_overrides",
    }
    unknown_keys = [key for key in payload.keys() if key not in allowed_keys]
    if unknown_keys:
        raise ValueError(
            "Unsupported scenario keys: "
            + ", ".join(sorted(unknown_keys))
            + ". Allowed keys are subject_overrides, action_overrides, object_initialization_overrides."
        )

    if (
        "subject_overrides" not in payload
        and "action_overrides" not in payload
        and "object_initialization_overrides" not in payload
    ):
        raise ValueError(
            "Scenario must provide at least one of: subject_overrides, action_overrides, object_initialization_overrides."
        )

    _apply_subject_overrides(graph, payload.get("subject_overrides", []))
    _apply_action_overrides(graph, payload.get("action_overrides", []))
    _apply_object_initialization_overrides(
        graph,
        payload.get("object_initialization_overrides", []),
    )

    # Track explicitly assigned actions and object-arcs for visualization origin labeling.
    system.assigned_actions, system.assigned_object_arcs, system.assigned_subjects = _collect_assigned_sets(system, payload)

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
    """Resolve scenario path using direct path, scripts/scenarios, then docs."""
    path = Path(filepath)
    if path.exists():
        return path

    candidate_paths = [
        Path("scripts") / "scenarios" / filepath,
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
    
    Searches in: current directory, scripts/scenarios/, and docs/.
    """
    path = _resolve_scenario_path(filepath)

    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return _load_yaml_scenario(path)
    if suffix == ".md":
        return build_default_system()

    raise ValueError(f"Unsupported scenario format: {path.suffix}")


def get_available_scenarios() -> list[str]:
    """List available scenario files in the framework and scripts/scenarios directory."""
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
    scenarios.extend(_collect_scenarios(framework_dir / "scripts" / "scenarios"))
    scenarios.extend(_collect_scenarios(framework_dir / "docs"))

    return sorted(set(scenarios))
