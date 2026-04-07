from __future__ import annotations

"""Visualization export helpers for Model 2.0 system views."""

from html import escape
from pathlib import Path
from typing import Dict, List, Tuple

from .model import EdgeType, System


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
        "Agent": [],
        "Participant": [],
        "Asset": [],
        "Source": [],
        "Other": [],
    }

    for node in sorted(graph.nodes.values(), key=lambda n: n.name):
        bucket = node.type if node.type in groups else "Other"
        groups[bucket].append(node.name)

    lines: List[str] = [
        "flowchart LR",
        "  %% Auto-generated holistic model view",
    ]

    group_titles = {
        "Agent": "Agents",
        "Participant": "Participants",
        "Asset": "Assets",
        "Source": "Sources",
        "Other": "Other",
    }

    for key in ["Agent", "Participant", "Source", "Asset", "Other"]:
        names = groups[key]
        if not names:
            continue
        lines.append(f"  subgraph {key}[{group_titles[key]}]")
        for name in names:
            node = graph.nodes[name]
            label = _subject_label(node) if node.is_subject else _object_label(node)
            lines.append(f"    {_node_id(name)}[\"{label}\"]")
        lines.append("  end")

    for edge in graph.edges:
        src = _node_id(edge.source)
        tgt = _node_id(edge.target)
        if edge.type == EdgeType.ACT:
            connector = "-->"
        elif edge.type == EdgeType.ACTED_ON_BY:
            connector = "-.->"
        elif edge.type == EdgeType.RESPOND:
            connector = "==>"
        else:
            connector = "--"
        label = f"{edge.name} ({edge.type.value})"
        lines.append(f"  {src} {connector}|{label}| {tgt}")

    return "\n".join(lines)


def _derive_output_paths(scenario_name: str, output_file: str | None) -> Tuple[Path, Path]:
    if output_file:
        md_path = Path(output_file)
    else:
        stem = Path(scenario_name).stem if scenario_name else "default"
        md_path = Path("output") / f"{stem}_pic.md"
    svg_path = md_path.with_suffix(".svg")
    return md_path, svg_path


def _grouped_node_names(system: System) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {
        "Agent": [],
        "Participant": [],
        "Asset": [],
        "Source": [],
        "Other": [],
    }
    for node in sorted(system.graph.nodes.values(), key=lambda n: n.name):
        groups[node.type if node.type in groups else "Other"].append(node.name)
    return groups


def _node_svg_label_lines(node) -> List[str]:
    if node.is_subject:
        s = node.as_subject()
        return [
            node.name,
            f"credibility: {s.credibility.value}",
            f"correctness: {s.correctness.value}",
            f"continuity: {s.continuity.value}",
        ]
    o = node.as_object()
    return [
        node.name,
        f"confidentiality: {o.confidentiality.value}",
        f"correctness: {o.correctness.value}",
        f"continuity: {o.continuity.value}",
    ]


def _role_alias_label_lines(node, alias_name: str) -> List[str]:
    if node.is_subject:
        s = node.as_subject()
        return [
            alias_name,
            f"credibility: {s.credibility.value}",
            f"correctness: {s.correctness.value}",
            f"continuity: {s.continuity.value}",
        ]
    o = node.as_object()
    return [
        alias_name,
        f"confidentiality: {o.confidentiality.value}",
        f"correctness: {o.correctness.value}",
        f"continuity: {o.continuity.value}",
    ]


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
        "User": {
            "R4.Respond": "Users (upper)",
            "R5.Respond": "Users (upper)",
            "R6.Respond": "Users (upper)",
            "R7.Respond": "Users (upper)",
            "10.Propose": "Users (lower)",
            "R1.Respond": "Users (lower)",
        },
        "ModelDeveloper": {
            "2.Train": "Model Developers (train)",
            "3.Upload": "Model Developers (upload)",
        },
        "AppDeveloper": {
            "5.Program": "App Developers (program)",
            "6.Upload": "App Developers (upload)",
        },
        "Maintainer": {
            "4.Download": "Maintainers (download)",
            "7.Download": "Maintainers (download)",
            "8.Download": "Maintainers (download)",
            "9.Assemble": "Maintainers (assemble)",
            "R7.Respond": "Maintainers (assemble)",
        },
        "OperatingEnvironment": {
            "R2.Respond": "Operating Env (response)",
            "R3.Respond": "Operating Env (response)",
            "ComponentOf": "Operating Env (response)",
        },
    }


def _select_visual_edges(system: System, positions: Dict[str, Tuple[float, float]]) -> list:
    """Select a less cluttered edge set for visualization.

    Strategy:
    - Keep all non-ACTED_ON_BY edges.
    - For ACTED_ON_BY with multiple inputs to the same operation target,
      keep only one representative edge to reduce twists.
    """
    selected = []
    acted_best: Dict[Tuple[str, str], object] = {}
    acted_score: Dict[Tuple[str, str], float] = {}

    for edge in system.graph.edges:
        if edge.type != EdgeType.ACTED_ON_BY:
            selected.append(edge)
            continue

        key = (edge.name, edge.target)
        sx, sy = positions[edge.source]
        tx, ty = positions[edge.target]
        score = abs(tx - sx) + abs(ty - sy)
        if key not in acted_score or score < acted_score[key]:
            acted_score[key] = score
            acted_best[key] = edge

    selected.extend(acted_best.values())
    return selected


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
        "DataWorker": (380, 140),
        "User": (1500, 140),

        "ModelPretrained": (120, 340),
        "ProcessedData": (560, 340),
        "ModelDeveloper": (1010, 340),
        "ModelTrained": (120, 470),
        "ModelHub": (560, 470),

        "AppDeveloper": (1450, 620),
        "ApplicationProgrammed": (1900, 620),
        "AppHub": (1450, 760),
        "DependencyHub": (2350, 760),

        "Maintainer": (1900, 900),
        "Model": (120, 900),
        "Application": (1450, 900),
        "Dependency": (2350, 900),

        "IntelligentSystem": (1900, 1080),
        "OperatingEnvironment": (2820, 1080),

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
        ("Users (upper)", "User", 1470, 140),
        ("Users (lower)", "User", 760, 1580),
        ("Model Developers (train)", "ModelDeveloper", 840, 340),
        ("Model Developers (upload)", "ModelDeveloper", 840, 470),
        ("App Developers (program)", "AppDeveloper", 1490, 620),
        ("App Developers (upload)", "AppDeveloper", 1490, 760),
        ("Maintainers (download)", "Maintainer", 2620, 820),
        ("Maintainers (assemble)", "Maintainer", 2140, 1080),
        ("Operating Env (response)", "OperatingEnvironment", 3180, 1080),
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

        alias_name = alias_endpoint_map.get(node_name, {}).get(edge.name)
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
        if edge.type == EdgeType.ACTED_ON_BY:
            dash = ' stroke-dasharray="7 4"'
            stroke = "#8c93a1"
        elif edge.type == EdgeType.RESPOND:
            stroke = "#f0c24f"
            stroke_width = 2.45
        elif edge.type == EdgeType.COMPONENT_OF:
            dash = ' stroke-dasharray="2 3"'
            stroke = "#71c08a"

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
        "User",
        "ModelDeveloper",
        "AppDeveloper",
        "Maintainer",
        "OperatingEnvironment",
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
    group_names = ["Participant", "Source", "Agent", "Asset", "Other"]
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
            f'<text x="{x + 20}" y="{gy}" font-family="Helvetica,Arial,sans-serif" font-size="11" fill="#475467">{escape(group)} node</text>'
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
        ("Act", "#2f6fb5", ""),
        ("ActedOnBy", "#6b7280", ' stroke-dasharray="7 4"'),
        ("Respond", "#c58a00", ""),
        ("ComponentOf", "#3f8a5e", ' stroke-dasharray="2 3"'),
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
