from __future__ import annotations

"""Visualization export helpers for Model 2.0 system views."""

from html import escape
from pathlib import Path
import re
import shutil
import subprocess
from typing import Dict, List, Tuple
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from .model import EdgeType, System


_RISK_EDGE_PATTERN = re.compile(r"edge\s+([^/\s]+)/([^\s]+)")
_CPN_ACTION_PATTERN = re.compile(r"CPN\[([^\]]+)\]")
_STAGE_SEQUENCE = ["Initial", "Development", "Deployment", "Inference", "Response", "Feedback"]


def _normalize_token(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def _risk_rank(severity: str) -> int:
    levels = {"high": 2, "medium": 1, "low": 0}
    return levels.get(severity.lower(), -1)


def _risk_origin_rank(origin: str) -> int:
    # Prefer propagated over assigned when severity is equal.
    return 1 if origin == "propagated" else 0


def _scenario_stem(scenario_name: str | None) -> str:
    if not scenario_name:
        return "default"
    normalized = scenario_name.strip()
    if not normalized:
        return "default"
    if normalized == "default (asploser)":
        return "default"
    return Path(normalized).stem or "default"


def _parse_style(style: str) -> dict[str, str]:
    style_map: dict[str, str] = {}
    for item in style.split(";"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            style_map[key] = value
        else:
            style_map[item] = ""
    return style_map


def _serialize_style(style_map: dict[str, str]) -> str:
    parts = []
    for key, value in style_map.items():
        if value == "":
            parts.append(key)
        else:
            parts.append(f"{key}={value}")
    return ";".join(parts) + ";"


def _risk_origin(action_name: str) -> str:
    return "assigned" if action_name.endswith(".Initialize") else "propagated"


def _risk_palette(severity: str, origin: str) -> tuple[str, str, str]:
    if origin == "assigned":
        if severity.lower() == "high":
            return "#bfdbfe", "#1d4ed8", "#1e3a8a"
        return "#dbeafe", "#2563eb", "#1e40af"

    if severity.lower() == "high":
        return "#fecaca", "#b91c1c", "#7f1d1d"
    return "#fde68a", "#b45309", "#78350f"


def _collect_propagation_targets(
    risk_strings: list[str],
) -> tuple[dict[str, tuple[str, str]], dict[str, tuple[str, str]]]:
    action_levels: dict[str, tuple[str, str]] = {}
    edge_levels: dict[str, tuple[str, str]] = {}

    for risk in risk_strings:
        if not risk.startswith("["):
            continue

        # Expected format: [Dimension][Severity] detail
        parts = risk.split("]", 2)
        if len(parts) < 3:
            continue
        severity = parts[1].lstrip("[").strip() or "Medium"
        detail = parts[2].strip()

        match = _RISK_EDGE_PATTERN.search(detail)
        if not match:
            continue

        action_name, edge_name = match.group(1), match.group(2)
        origin = _risk_origin(action_name)
        action_key = _normalize_token(action_name)
        edge_key = _normalize_token(edge_name)

        current_action = action_levels.get(action_key)
        should_update_action = current_action is None or (
            _risk_rank(severity) > _risk_rank(current_action[0])
            or (
                _risk_rank(severity) == _risk_rank(current_action[0])
                and _risk_origin_rank(origin) > _risk_origin_rank(current_action[1])
            )
        )
        if should_update_action:
            action_levels[action_key] = (severity, origin)

        current_edge = edge_levels.get(edge_key)
        should_update_edge = current_edge is None or (
            _risk_rank(severity) > _risk_rank(current_edge[0])
            or (
                _risk_rank(severity) == _risk_rank(current_edge[0])
                and _risk_origin_rank(origin) > _risk_origin_rank(current_edge[1])
            )
        )
        if should_update_edge:
            edge_levels[edge_key] = (severity, origin)

    return action_levels, edge_levels


def _node_id(name: str) -> str:
    cleaned = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            cleaned.append(ch)
        else:
            cleaned.append("_")
    return "n_" + "".join(cleaned)


def _subject_label(node) -> str:
    s = node.as_subject()
    return (
        f"{node.name}\\n"
        f"credibility: {s.credibility.value}\\n"
        f"correctness: {s.correctness.value}\\n"
        f"continuity: {s.continuity.value}"
    )


def _object_label(node) -> str:
    o = node.as_object()
    return (
        f"{node.name}\\n"
        f"confidentiality: {o.confidentiality.value}\\n"
        f"correctness: {o.correctness.value}\\n"
        f"continuity: {o.continuity.value}"
    )


def build_holistic_picture_mermaid(system: System) -> str:
    """Build a Mermaid flowchart that shows a holistic model picture."""
    graph = system.graph

    groups: Dict[str, List[str]] = {
        "Subject": [],
        "Action": [],
        "Object": [],
    }

    for node in sorted(graph.nodes.values(), key=lambda n: n.name):
        bucket = "Subject" if node.is_subject else "Object"
        groups[bucket].append(node.name)

    for action in sorted(graph.actions.values(), key=lambda a: a.name):
        groups["Action"].append(action.name)

    lines: List[str] = [
        "flowchart LR",
        "  %% Auto-generated holistic model view",
    ]

    group_titles = {
        "Subject": "Subjects",
        "Action": "Actions",
        "Object": "Objects",
    }

    for key in ["Subject", "Action", "Object"]:
        names = groups[key]
        if not names:
            continue
        lines.append(f"  subgraph {key}[{group_titles[key]}]")
        for name in names:
            if key == "Action":
                action = graph.actions[name]
                label = f"{action.name}\\nstage: {action.stage}"
                lines.append(f"    {_node_id(name)}[\"{label}\"]")
            else:
                node = graph.nodes[name]
                label = _subject_label(node) if node.is_subject else _object_label(node)
                lines.append(f"    {_node_id(name)}[\"{label}\"]")
        lines.append("  end")

    for edge in graph.edges:
        action = _node_id(edge.action)
        src = _node_id(edge.source)
        tgt = _node_id(edge.target)
        in_label = f"{edge.name} ({edge.type.value})"
        out_label = f"{edge.name}"
        lines.append(f"  {src} -->|{in_label}| {action}")
        lines.append(f"  {action} -->|{out_label}| {tgt}")

    return "\n".join(lines)


def _derive_output_paths(scenario_name: str, output_file: str | None) -> Tuple[Path, Path]:
    if output_file:
        md_path = Path(output_file)
    else:
        stem = _scenario_stem(scenario_name)
        md_path = Path("output") / f"{stem}_pic.md"
    svg_path = md_path.with_suffix(".svg")
    return md_path, svg_path


def _derive_drawio_output_path(scenario_name: str, output_file: str | None) -> Path:
    if output_file:
        return Path(output_file)
    stem = _scenario_stem(scenario_name)
    return Path("output") / f"{stem}_pic.drawio"


def _derive_png_output_path(stem_name: str, output_file: str | None) -> Path:
    if output_file:
        return Path(output_file)
    return Path("output") / f"{stem_name}.png"


def _parse_risk_action_name(risk: str) -> str | None:
    match = _RISK_EDGE_PATTERN.search(risk)
    if not match:
        return None
    return match.group(1)


def _parse_fired_action_name(action_text: str) -> str | None:
    match = _CPN_ACTION_PATTERN.search(action_text)
    if not match:
        return None
    return match.group(1)


def _build_progressive_stage_risks(
    risk_strings: list[str],
    states,
    development_cycles: int,
    feedback: bool,
) -> dict[tuple[int, int], list[str]]:
    risks_by_action: dict[str, list[str]] = {}
    for risk in risk_strings:
        action_name = _parse_risk_action_name(risk)
        if action_name is None:
            continue
        risks_by_action.setdefault(action_name, []).append(risk)

    fired_actions_by_cycle_stage: dict[tuple[int, str], set[str]] = {}
    for state in states:
        action_name = _parse_fired_action_name(state.action)
        if action_name is None:
            continue
        key = (state.cycle_index, state.stage)
        fired_actions_by_cycle_stage.setdefault(key, set()).add(action_name)

    progressive: dict[tuple[int, int], list[str]] = {}
    ordered_stages = _STAGE_SEQUENCE if feedback else _STAGE_SEQUENCE[:-1]
    stage_indexes = {name: idx for idx, name in enumerate(_STAGE_SEQUENCE)}

    for cycle_index in range(1, development_cycles + 1):
        cumulative_actions: set[str] = set()
        progressive[(cycle_index, 0)] = []

        for stage_name in ordered_stages[1:]:
            cumulative_actions.update(
                fired_actions_by_cycle_stage.get((cycle_index, stage_name), set())
            )

            seen: set[str] = set()
            stage_risks: list[str] = []
            for action_name in cumulative_actions:
                for risk in risks_by_action.get(action_name, []):
                    if risk in seen:
                        continue
                    seen.add(risk)
                    stage_risks.append(risk)

            progressive[(cycle_index, stage_indexes[stage_name])] = stage_risks

        if not feedback:
            progressive[(cycle_index, 5)] = progressive.get((cycle_index, 4), [])

    return progressive


def _collect_existing_cell_ids(mx_root: Element) -> set[str]:
    ids: set[str] = set()
    for cell in mx_root.findall("mxCell"):
        cell_id = cell.get("id")
        if cell_id:
            ids.add(cell_id)
    return ids


def _next_legend_id(existing_ids: set[str], suffix: str) -> str:
    base = f"legend-{suffix}"
    if base not in existing_ids:
        existing_ids.add(base)
        return base

    index = 1
    while True:
        candidate = f"{base}-{index}"
        if candidate not in existing_ids:
            existing_ids.add(candidate)
            return candidate
        index += 1


def _append_vertex_cell(
    mx_root: Element,
    existing_ids: set[str],
    suffix: str,
    value: str,
    style: str,
    x: int,
    y: int,
    width: int,
    height: int,
) -> None:
    cell_id = _next_legend_id(existing_ids, suffix)
    cell = SubElement(
        mx_root,
        "mxCell",
        id=cell_id,
        value=value,
        style=style,
        vertex="1",
        parent="1",
    )
    SubElement(
        cell,
        "mxGeometry",
        x=str(x),
        y=str(y),
        width=str(width),
        height=str(height),
        **{"as": "geometry"},
    )


def _append_propagation_legend(
    xml_root: Element,
    action_levels: dict[str, tuple[str, str]],
    edge_levels: dict[str, tuple[str, str]],
) -> None:
    mx_root = xml_root.find("./diagram/mxGraphModel/root")
    if mx_root is None:
        return

    existing_ids = _collect_existing_cell_ids(mx_root)
    impacted_actions = len(action_levels)
    impacted_arcs = len(edge_levels)
    assigned_actions = sum(1 for _, origin in action_levels.values() if origin == "assigned")
    assigned_arcs = sum(1 for _, origin in edge_levels.values() if origin == "assigned")
    propagated_actions = impacted_actions - assigned_actions
    propagated_arcs = impacted_arcs - assigned_arcs

    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="panel",
        value="Propagation Color Legend",
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#94a3b8;"
            "fontStyle=1;fontSize=12;"
        ),
        x=1360,
        y=20,
        width=410,
        height=40,
    )
    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="prop-high",
        value="Propagated High risk (action or arc label)",
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#fecaca;strokeColor=#b91c1c;"
            "fontColor=#7f1d1d;fontSize=11;"
        ),
        x=1360,
        y=66,
        width=410,
        height=32,
    )
    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="prop-medium",
        value="Propagated Medium risk (action or arc label)",
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#fde68a;strokeColor=#b45309;"
            "fontColor=#78350f;fontSize=11;"
        ),
        x=1360,
        y=102,
        width=410,
        height=32,
    )
    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="assign-high",
        value="Assigned High risk (initialize-time)",
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#bfdbfe;strokeColor=#1d4ed8;"
            "fontColor=#1e3a8a;fontSize=11;"
        ),
        x=1360,
        y=138,
        width=410,
        height=32,
    )
    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="assign-medium",
        value="Assigned Medium risk (initialize-time)",
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#dbeafe;strokeColor=#2563eb;"
            "fontColor=#1e40af;fontSize=11;"
        ),
        x=1360,
        y=174,
        width=410,
        height=32,
    )
    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="scope",
        value=(
            "Risk impact coverage: "
            f"{impacted_actions} action nodes, {impacted_arcs} object-arc labels"
        ),
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#64748b;"
            "fontColor=#1e293b;fontSize=11;"
        ),
        x=1360,
        y=210,
        width=410,
        height=32,
    )
    _append_vertex_cell(
        mx_root=mx_root,
        existing_ids=existing_ids,
        suffix="split",
        value=(
            "Assigned vs Propagated: "
            f"actions {assigned_actions}/{propagated_actions}, "
            f"arcs {assigned_arcs}/{propagated_arcs}"
        ),
        style=(
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#94a3b8;"
            "fontColor=#334155;fontSize=11;"
        ),
        x=1360,
        y=246,
        width=410,
        height=32,
    )


def _render_template_propagation_drawio(
    risk_strings: list[str],
    template_path: Path,
    output_path: Path,
) -> Path:
    xml_text = template_path.read_text(encoding="utf-8")
    root = fromstring(xml_text)
    action_levels, edge_levels = _collect_propagation_targets(risk_strings)

    for cell in root.iter("mxCell"):
        style = cell.get("style", "")
        value = cell.get("value", "")
        normalized = _normalize_token(value)
        if not normalized:
            continue

        style_map = _parse_style(style)
        severity = ""
        origin = ""

        if normalized in action_levels and "rounded" in style_map:
            severity, origin = action_levels[normalized]
        elif normalized in edge_levels and "edgeLabel" in style_map:
            severity, origin = edge_levels[normalized]

        if not severity:
            continue

        fill, stroke, font = _risk_palette(severity, origin)
        if "edgeLabel" in style_map:
            style_map["labelBackgroundColor"] = fill
            style_map["fontColor"] = font
            style_map["strokeColor"] = stroke
        else:
            style_map["fillColor"] = fill
            style_map["strokeColor"] = stroke
            style_map["fontColor"] = font

        cell.set("style", _serialize_style(style_map))

    _append_propagation_legend(root, action_levels, edge_levels)

    rendered = tostring(root, encoding="unicode")
    output_path.write_text(rendered, encoding="utf-8")
    return output_path


def _find_drawio_command() -> str | None:
    """Find a usable draw.io CLI command in PATH."""
    candidates = ["drawio", "draw.io", "diagrams"]
    for command in candidates:
        resolved = shutil.which(command)
        if resolved:
            return resolved
    return None


def _run_drawio_png_export(input_path: Path, output_path: Path) -> None:
    command = _find_drawio_command()
    if not command:
        raise RuntimeError(
            "draw.io CLI not found. Install draw.io and ensure one of these commands is in PATH: "
            "drawio, draw.io, or diagrams."
        )

    attempts = [
        [command, "--export", "--format", "png", "--output", str(output_path), str(input_path)],
        [command, "-x", "-f", "png", "-o", str(output_path), str(input_path)],
    ]

    last_error = ""
    for cmd in attempts:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists():
            return
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or f"exit code {result.returncode}"
        last_error = f"command {' '.join(cmd)} failed: {details}"

    raise RuntimeError(
        "Failed to export PNG from draw.io XML. "
        f"Last error: {last_error}"
    )


def _grouped_node_names(system: System) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {
        "Subject": [],
        "Object": [],
    }
    for node in sorted(system.graph.nodes.values(), key=lambda n: n.name):
        groups["Subject" if node.is_subject else "Object"].append(node.name)
    return groups


def _node_svg_label_lines(node) -> List[str]:
    return _build_node_label_lines(node, node.name)


def _build_node_label_lines(node, header_name: str) -> List[str]:
    if node.is_subject:
        s = node.as_subject()
        return [
            header_name,
            f"credibility: {s.credibility.value}",
            f"correctness: {s.correctness.value}",
            f"continuity: {s.continuity.value}",
        ]
    o = node.as_object()
    return [
        header_name,
        f"confidentiality: {o.confidentiality.value}",
        f"correctness: {o.correctness.value}",
        f"continuity: {o.continuity.value}",
    ]


def _role_alias_label_lines(node, alias_name: str) -> List[str]:
    return _build_node_label_lines(node, alias_name)


def _draw_card(
    parts: List[str],
    x: float,
    y: float,
    width: float,
    height: float,
    header_fill: str,
    body_fill: str,
    stroke: str,
    label_lines: List[str],
    dashed: bool = False,
) -> None:
    dash_attr = ' stroke-dasharray="5 3"' if dashed else ""
    parts.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height}" fill="{body_fill}" stroke="{stroke}" stroke-width="1.1" rx="7"{dash_attr}/>'
    )
    parts.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="24" fill="{header_fill}" stroke="{stroke}" stroke-width="1.1" rx="7"{dash_attr}/>'
    )
    parts.append(
        f'<line x1="{x:.1f}" y1="{y + 24:.1f}" x2="{x + width:.1f}" y2="{y + 24:.1f}" stroke="#aab2bf" stroke-width="0.8"/>'
    )
    for idx, line in enumerate(label_lines):
        font_weight = "700" if idx == 0 else "400"
        font_size = 11.5 if dashed and idx == 0 else 10 if dashed else 12 if idx == 0 else 10.5
        y_text = y + 17 if idx == 0 else y + 20 + idx * 19
        text_fill = "#1f2937" if dashed else "#111"
        parts.append(
            f'<text x="{x + 10:.1f}" y="{y_text:.1f}" font-family="Helvetica,Arial,sans-serif" font-size="{font_size}" font-weight="{font_weight}" fill="{text_fill}">{escape(line)}</text>'
        )


def _build_alias_endpoint_map() -> Dict[str, Dict[str, str]]:
    return {
        "Users": {
            "F1.Feedback": "Users (upper)",
            "O1.Input": "Users (lower)",
            "O4.Postprocess": "Users (lower)",
        },
        "ModelDevelopers": {
            "M4.Train": "Model Developers (train)",
            "M5.Upload": "Model Developers (upload)",
        },
        "AppDevelopers": {
            "A1.Program": "App Developers (program)",
            "A2.Upload": "App Developers (upload)",
        },
        "Maintainers": {
            "M6.Download": "Maintainers (download)",
            "A3.Download": "Maintainers (download)",
            "P2.Download": "Maintainers (download)",
            "D2.Delopy": "Maintainers (assemble)",
            "F1.Feedback": "Maintainers (assemble)",
        },
        "OutsideEnv": {
            "O4.Postprocess": "Operating Env (response)",
            "O1.Input": "Operating Env (response)",
        },
    }


def _select_visual_edges(system: System, positions: Dict[str, Tuple[float, float]]) -> list:
    """Select a less cluttered edge set for visualization.

    Strategy:
    - Keep all object arcs to preserve complete Petri-style connectivity.
    """
    del positions
    return list(system.graph.edges)


def _build_holistic_picture_svg(system: System) -> str:
    """Build a standalone SVG picture for the holistic model view.

    Layout intention: resemble the layered visual structure in model4.0.
    """
    groups = _grouped_node_names(system)

    box_w = 232
    box_h = 88
    width = 3600
    height = 1720

    # Layer bands from top to bottom (similar to model4.0 visual hierarchy).
    layer_specs = [
        ("Data & Participants", 90, 270, "#f9fbff"),
        ("Development Artifacts", 290, 540, "#fffaf3"),
        ("Supply Chain & Deployment", 560, 980, "#f7fcf8"),
        ("System Core", 1000, 1220, "#f7f8ff"),
        ("Inference Pipeline", 1240, 1530, "#fff7fb"),
        ("Interaction Layer", 1540, 1680, "#f5fbff"),
    ]

    # Hand-tuned anchor map to make node layering similar to the reference image.
    preferred_positions: Dict[str, Tuple[float, float]] = {
        "RawData": (110, 140),
        "DataWorkers": (380, 140),
        "Users": (1500, 140),

        "ModelPretrained": (120, 340),
        "ProcessedData": (560, 340),
        "ModelDevelopers": (1010, 340),
        "ModelTrained": (120, 470),
        "ModelHub": (560, 470),

        "AppDevelopers": (1450, 620),
        "ApplicationProgrammed": (1900, 620),
        "AppHub": (1450, 760),
        "DependencyHub": (2350, 760),

        "Maintainers": (1900, 900),
        "Model": (120, 900),
        "Application": (1450, 900),
        "Dependency": (2350, 900),

        "OutsideEnv": (2820, 1080),

        "PreprocessingModule": (1200, 1290),
        "InferenceModule": (1900, 1290),
        "PostprocessingModule": (2600, 1290),

        "InputQuery": (840, 1460),
        "InputToken": (1550, 1460),
        "OutputToken": (2250, 1460),
        "OutputMaterialized": (2950, 1460),
    }

    # Duplicated role cards for readability across layers (visual aliases).
    role_aliases: List[Tuple[str, str, float, float]] = [
        ("Users (upper)", "Users", 1470, 140),
        ("Users (lower)", "Users", 760, 1580),
        ("Model Developers (train)", "ModelDevelopers", 840, 340),
        ("Model Developers (upload)", "ModelDevelopers", 840, 470),
        ("App Developers (program)", "AppDevelopers", 1490, 620),
        ("App Developers (upload)", "AppDevelopers", 1490, 760),
        ("Maintainers (download)", "Maintainers", 2620, 820),
        ("Maintainers (assemble)", "Maintainers", 2140, 1080),
        ("Operating Env (response)", "OutsideEnv", 3180, 1080),
    ]
    alias_positions = {alias_name: (ax, ay) for alias_name, _, ax, ay in role_aliases}
    alias_endpoint_map = _build_alias_endpoint_map()

    # Fallback placement for nodes not in the hand-tuned map.
    fallback_x = 120
    fallback_y = 600
    fallback_step = 270
    fallback_row = 0
    positions: Dict[str, Tuple[float, float]] = {}
    for name in sorted(system.graph.nodes.keys()):
        if name in preferred_positions:
            positions[name] = preferred_positions[name]
            continue
        positions[name] = (fallback_x + (fallback_row % 10) * fallback_step, fallback_y + (fallback_row // 10) * 120)
        fallback_row += 1

    parts: List[str] = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    parts.append("<defs>")
    parts.append(
        '  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
    )
    parts.append('    <path d="M 0 0 L 10 5 L 0 10 z" fill="#3d3d3d"/>')
    parts.append("  </marker>")
    parts.append("</defs>")
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0f1115"/>')
    parts.append(
        '<text x="36" y="34" font-family="Helvetica,Arial,sans-serif" font-size="22" font-weight="700" fill="#f3f6fb">Holistic Model Picture</text>'
    )
    parts.append(
        '<text x="36" y="58" font-family="Helvetica,Arial,sans-serif" font-size="12" fill="#c9d1dc">Stage-oriented diagram generated from the current system graph</text>'
    )

    for layer_name, y1, y2, color in layer_specs:
        parts.append(
            f'<rect x="50" y="{y1}" width="{width - 100}" height="{y2 - y1}" fill="{color}" fill-opacity="0.93" stroke="#d6deea" stroke-width="1" rx="10"/>'
        )
        parts.append(
            f'<text x="68" y="{y1 + 20}" font-family="Helvetica,Arial,sans-serif" font-size="13" font-weight="700" fill="#2c3a4b">{escape(layer_name)}</text>'
        )

    draw_edges = _select_visual_edges(system, positions)

    def _resolve_endpoint(edge, is_source: bool) -> Tuple[float, float]:
        node_name = edge.source if is_source else edge.target

        alias_name = alias_endpoint_map.get(node_name, {}).get(edge.action)
        if alias_name is not None:
            return alias_positions[alias_name]

        return positions[node_name]

    for edge in draw_edges:
        sx, sy = _resolve_endpoint(edge, is_source=True)
        tx, ty = _resolve_endpoint(edge, is_source=False)
        x1 = sx + box_w
        y1 = sy + box_h / 2
        x2 = tx
        y2 = ty + box_h / 2

        dash = ""
        stroke = "#4c9dff"
        stroke_width = 2.05
        bend = abs(x2 - x1) * 0.34
        cx1 = x1 + bend if x2 >= x1 else x1 - bend
        cx2 = x2 - bend if x2 >= x1 else x2 + bend
        path = f'M {x1:.1f} {y1:.1f} C {cx1:.1f} {y1:.1f}, {cx2:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}'

        parts.append(
            f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" marker-end="url(#arrow)"{dash}/>'
        )

        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2 - 6
        parts.append(
            f'<text x="{mx:.1f}" y="{my:.1f}" font-family="Helvetica,Arial,sans-serif" font-size="9.5" fill="#d7dde7" text-anchor="middle">{escape(edge.name)}</text>'
        )

    # Intentionally omit alias-link lines to reduce visual twisting.

    hidden_base_nodes = {
        "Users",
        "ModelDevelopers",
        "AppDevelopers",
        "Maintainers",
        "OutsideEnv",
    }

    for name, (x, y) in positions.items():
        if name in hidden_base_nodes:
            continue
        node = system.graph.nodes[name]
        fill = "#fcfcfd" if node.is_subject else "#f8fbff"
        _draw_card(parts, x, y, box_w, box_h, "#e9edf3", fill, "#8f99aa", _node_svg_label_lines(node))

    # Draw duplicated role cards on top for easier layer-based reading.
    for alias_name, base_name, x, y in role_aliases:
        base_node = system.graph.nodes.get(base_name)
        if base_node is None:
            continue
        _draw_card(parts, x, y, box_w, box_h, "#eef2f7", "#ffffff", "#8d99a8", _role_alias_label_lines(base_node, alias_name), dashed=True)

    # Group hints
    group_names = ["Subject", "Object"]
    gy = 74
    gx = 980
    for idx, group in enumerate(group_names):
        if not groups.get(group):
            continue
        x = gx + idx * 180
        parts.append(
            f'<rect x="{x}" y="{gy - 12}" width="14" height="14" fill="#ffffff" stroke="#98a1ae" stroke-width="1" rx="2"/>'
        )
        parts.append(
            f'<text x="{x + 20}" y="{gy}" font-family="Helvetica,Arial,sans-serif" font-size="11" fill="#475467">{escape(group)} nodes</text>'
        )

    # Legend
    lx = 34
    ly = height - 118
    parts.append(
        f'<rect x="{lx}" y="{ly}" width="560" height="88" fill="#ffffff" stroke="#cfd6df" stroke-width="1" rx="8"/>'
    )
    parts.append(
        f'<text x="{lx + 12}" y="{ly + 20}" font-family="Helvetica,Arial,sans-serif" font-size="12" font-weight="700" fill="#243447">Edge Legend</text>'
    )
    legend_items = [
        ("ObjectArc", "#2f6fb5", ""),
    ]
    for idx, (name, color, dash) in enumerate(legend_items):
        y = ly + 40 + idx * 10
        x = lx + 14 + idx * 132
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x + 28}" y2="{y}" stroke="{color}" stroke-width="2"{dash}/>'
        )
        parts.append(
            f'<text x="{x + 34}" y="{y + 3}" font-family="Helvetica,Arial,sans-serif" font-size="10.5" fill="#1f2937">{name}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def build_holistic_picture_drawio(system: System, diagram_name: str = "Holistic Model Picture") -> str:
    """Build a Draw.io diagram XML from the current system graph."""

    root = Element("mxfile", host="app.diagrams.net", version="24.7.17")
    diagram = SubElement(root, "diagram", id="asploser-model2", name=diagram_name)
    model = SubElement(
        diagram,
        "mxGraphModel",
        dx="1800",
        dy="1000",
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="1",
        pageScale="1",
        pageWidth="3000",
        pageHeight="2000",
        math="0",
        shadow="0",
    )
    mx_root = SubElement(model, "root")
    SubElement(mx_root, "mxCell", id="0")
    SubElement(mx_root, "mxCell", id="1", parent="0")

    def _append_geometry(parent, **attrs) -> None:
        geometry_attrs = dict(attrs)
        geometry_attrs["as"] = "geometry"
        SubElement(parent, "mxGeometry", **geometry_attrs)

    def _grid_position(index: int, start_x: int, start_y: int, columns: int, col_gap: int, row_gap: int) -> tuple[int, int]:
        col = index % columns
        row = index // columns
        return start_x + col * col_gap, start_y + row * row_gap

    graph = system.graph
    subjects = sorted([node for node in graph.nodes.values() if node.is_subject], key=lambda n: n.name)
    objects = sorted([node for node in graph.nodes.values() if not node.is_subject], key=lambda n: n.name)
    actions = sorted(graph.actions.values(), key=lambda a: (a.stage, a.name))

    id_counter = 2
    node_ids: Dict[str, str] = {}
    action_ids: Dict[str, str] = {}

    stage_y = {
        "Development": 80,
        "Deployment": 360,
        "Inference": 640,
        "Response": 920,
        "Feedback": 1200,
    }
    stage_counts: Dict[str, int] = {stage: 0 for stage in stage_y.keys()}

    for idx, node in enumerate(subjects):
        cell_id = str(id_counter)
        id_counter += 1
        node_ids[node.name] = cell_id
        value = _subject_label(node).replace("\n", "<br/>")
        x, y = _grid_position(idx, start_x=60, start_y=80, columns=2, col_gap=300, row_gap=120)
        cell = SubElement(
            mx_root,
            "mxCell",
            id=cell_id,
            value=value,
            style="ellipse;whiteSpace=wrap;html=1;strokeWidth=1.4;fillColor=#e7f0ff;strokeColor=#2f6fb5;",
            vertex="1",
            parent="1",
        )
        _append_geometry(cell, x=str(x), y=str(y), width="260", height="92")

    for idx, action in enumerate(actions):
        cell_id = str(id_counter)
        id_counter += 1
        action_ids[action.name] = cell_id
        base_y = stage_y.get(action.stage, 80)
        action_row = stage_counts.get(action.stage, 0)
        stage_counts[action.stage] = action_row + 1
        y = base_y + action_row * 82
        value = f"{action.name}<br/>stage: {action.stage}"
        cell = SubElement(
            mx_root,
            "mxCell",
            id=cell_id,
            value=value,
            style="rounded=0;whiteSpace=wrap;html=1;strokeWidth=1.4;fillColor=#fff2cc;strokeColor=#a87000;",
            vertex="1",
            parent="1",
        )
        _append_geometry(cell, x="740", y=str(y), width="320", height="72")

    for idx, node in enumerate(objects):
        cell_id = str(id_counter)
        id_counter += 1
        node_ids[node.name] = cell_id
        value = _object_label(node).replace("\n", "<br/>")
        x, y = _grid_position(idx, start_x=1220, start_y=80, columns=2, col_gap=340, row_gap=120)
        cell = SubElement(
            mx_root,
            "mxCell",
            id=cell_id,
            value=value,
            style="rounded=1;whiteSpace=wrap;html=1;strokeWidth=1.4;fillColor=#eaf7ea;strokeColor=#2f8f4e;",
            vertex="1",
            parent="1",
        )
        _append_geometry(cell, x=str(x), y=str(y), width="320", height="92")

    for edge in graph.edges:
        if edge.source not in node_ids or edge.target not in node_ids or edge.action not in action_ids:
            continue

        to_action_id = str(id_counter)
        id_counter += 1
        edge_value = f"{edge.name} ({edge.type.value})"
        edge_cell = SubElement(
            mx_root,
            "mxCell",
            id=to_action_id,
            value=edge_value,
            style="endArrow=block;html=1;rounded=0;strokeColor=#5f6368;",
            edge="1",
            parent="1",
            source=node_ids[edge.source],
            target=action_ids[edge.action],
        )
        _append_geometry(edge_cell, relative="1")

        from_action_id = str(id_counter)
        id_counter += 1
        edge_cell = SubElement(
            mx_root,
            "mxCell",
            id=from_action_id,
            value=edge.name,
            style="endArrow=block;html=1;rounded=0;strokeColor=#5f6368;",
            edge="1",
            parent="1",
            source=action_ids[edge.action],
            target=node_ids[edge.target],
        )
        _append_geometry(edge_cell, relative="1")

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(root, encoding="unicode")


def export_holistic_picture(
    system: System,
    scenario_name: str = "default",
    output_file: str | None = None,
) -> Tuple[Path, Path]:
    """Export a holistic model picture as markdown+Mermaid and a true SVG image."""
    md_path, svg_path = _derive_output_paths(scenario_name, output_file)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)

    mermaid = build_holistic_picture_mermaid(system)
    content = (
        "# Holistic Model Picture\n\n"
        "This diagram is auto-generated from the current scenario graph.\n\n"
        f"Generated image: {svg_path.name}\n\n"
        "```mermaid\n"
        f"{mermaid}\n"
        "```\n"
    )
    md_path.write_text(content, encoding="utf-8")

    svg = _build_holistic_picture_svg(system)
    svg_path.write_text(svg, encoding="utf-8")

    return md_path, svg_path


def export_holistic_picture_drawio(
    system: System,
    scenario_name: str = "default",
    output_file: str | None = None,
) -> Path:
    """Export a holistic model picture as a Draw.io diagram file (.drawio)."""
    drawio_path = _derive_drawio_output_path(scenario_name, output_file)
    drawio_path.parent.mkdir(parents=True, exist_ok=True)
    drawio_xml = build_holistic_picture_drawio(system)
    drawio_path.write_text(drawio_xml, encoding="utf-8")
    return drawio_path


def export_template_propagation_drawio(
    scenario_name: str,
    risk_strings: list[str],
    template_file: str = "docs/model.drawio",
    output_file: str | None = None,
) -> Path:
    """Copy the provided draw.io XML template and recolor cells based on propagation risks."""

    template_path = Path(template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Template draw.io file not found: {template_path}")

    output_path = _derive_drawio_output_path(scenario_name, output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return _render_template_propagation_drawio(risk_strings, template_path, output_path)


def export_template_propagation_drawio_per_stage(
    scenario_name: str,
    risk_strings: list[str],
    states,
    development_cycles: int,
    feedback: bool,
    output_dir: str | None = None,
    template_file: str = "docs/model.drawio",
) -> list[Path]:
    """Export six draw.io files per cycle: initial + five stage checkpoints."""

    template_path = Path(template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Template draw.io file not found: {template_path}")

    base_dir = Path(output_dir) if output_dir else Path("output")
    base_dir.mkdir(parents=True, exist_ok=True)

    stem = _scenario_stem(scenario_name)
    stage_risks = _build_progressive_stage_risks(
        risk_strings=risk_strings,
        states=states,
        development_cycles=development_cycles,
        feedback=feedback,
    )

    exported: list[Path] = []
    for cycle_index in range(1, development_cycles + 1):
        for stage_index, stage_name in enumerate(_STAGE_SEQUENCE):
            file_name = (
                f"{stem}_pic_cycle{cycle_index}_stage{stage_index}_{stage_name.lower()}.drawio"
            )
            output_path = base_dir / file_name
            stage_specific_risks = stage_risks.get((cycle_index, stage_index), [])
            exported.append(
                _render_template_propagation_drawio(
                    risk_strings=stage_specific_risks,
                    template_path=template_path,
                    output_path=output_path,
                )
            )

    return exported


def export_drawio_xml_to_png(
    drawio_file: str | Path,
    output_file: str | None = None,
) -> Path:
    """Export a draw.io XML file to PNG using draw.io CLI."""
    input_path = Path(drawio_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Draw.io source file not found: {input_path}")

    stem_name = input_path.stem
    output_path = _derive_png_output_path(stem_name, output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_drawio_png_export(input_path, output_path)
    return output_path


def export_reference_model_png(
    source_drawio_file: str = "docs/model.drawio",
    output_file: str | None = None,
) -> Path:
    """Export the provided canonical model draw.io XML to PNG."""
    return export_drawio_xml_to_png(source_drawio_file, output_file=output_file)
