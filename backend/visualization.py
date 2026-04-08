from __future__ import annotations

"""Visualization export helpers for Model 2.0 system views."""

import html as _html_mod
from dataclasses import dataclass, field
from pathlib import Path
import re
import shutil
import subprocess
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from .model import EdgeType, System


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------
_RISK_EDGE_PATTERN = re.compile(r"edge\s+([^/\s]+)/([^\s]+)")
_CPN_ACTION_PATTERN = re.compile(r"CPN\[([^\]]+)\]")
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_FEEDBACK_ACTION_PATTERN = re.compile(r"^f\d")  # e.g. f1feedback, f2...

_STAGE_SEQUENCE = ["Initial", "Development", "Deployment", "Operation", "Feedback"]
_DIMENSIONS = ["Confidentiality", "Integrity", "Availability"]

# ---------------------------------------------------------------------------
# Tiny helpers (no template access)
# ---------------------------------------------------------------------------

def _normalize_token(value: str) -> str:
    stripped = _HTML_TAG_PATTERN.sub("", value)
    decoded = _html_mod.unescape(stripped).replace("&", "and")
    return "".join(ch.lower() for ch in decoded if ch.isalnum())


def _clean_cell_value(value: str) -> str:
    return _html_mod.unescape(_HTML_TAG_PATTERN.sub("", value)).strip()


_RISK_RANKS = {"high": 2, "medium": 1, "low": 0}


def _risk_rank(severity: str) -> int:
    return _RISK_RANKS.get(severity.lower(), -1)


def _should_replace_risk(
    current: tuple[str, str] | None,
    severity: str,
    origin: str,
) -> bool:
    if current is None:
        return True
    cur_sev, cur_ori = current
    new_rank, cur_rank = _risk_rank(severity), _risk_rank(cur_sev)
    if new_rank != cur_rank:
        return new_rank > cur_rank
    # Equal severity → prefer propagated over assigned.
    return (origin == "propagated") > (cur_ori == "propagated")


def _action_origin(action_name: str, assigned_actions: set[str]) -> str:
    if action_name in assigned_actions:
        return "assigned"
    if action_name.endswith(".Initialize") or action_name.endswith(".Initialization"):
        return "initialization"
    return "propagated"


def _risk_origin(action_name: str, edge_name: str, assigned_object_arcs: set[str]) -> str:
    return "assigned" if f"{action_name}/{edge_name}" in assigned_object_arcs else "propagated"


# Color palette: (fill, stroke, font) keyed by (origin_group, severity_group).
_PALETTE = {
    ("initialization", "high"):   ("#bbf7d0", "#16a34a", "#14532d"),
    ("initialization", "medium"): ("#bbf7d0", "#16a34a", "#14532d"),
    ("assigned", "high"):         ("#e9d5ff", "#7e22ce", "#4c1d95"),
    ("assigned", "medium"):       ("#dbeafe", "#2563eb", "#1e40af"),
    ("propagated", "high"):       ("#fecaca", "#b91c1c", "#7f1d1d"),
    ("propagated", "medium"):     ("#fde68a", "#b45309", "#78350f"),
}


def _risk_palette(severity: str, origin: str) -> tuple[str, str, str]:
    key = (origin, severity.lower())
    return _PALETTE.get(key, _PALETTE[("propagated", "medium")])


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
        parts.append(key if value == "" else f"{key}={value}")
    return ";".join(parts) + ";"


def _scenario_stem(scenario_name: str | None) -> str:
    if not scenario_name:
        return "default"
    normalized = scenario_name.strip()
    if not normalized:
        return "default"
    if normalized == "default (asploser)":
        return "default"
    return Path(normalized).stem or "default"


# ---------------------------------------------------------------------------
# Risk-string parsing (template-independent)
# ---------------------------------------------------------------------------

def _collect_propagation_targets(
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
        match = _RISK_EDGE_PATTERN.search(parts[2])
        if not match:
            continue

        action_name, edge_name = match.group(1), match.group(2)
        act_origin = _action_origin(action_name, actions_set)
        arc_origin = _risk_origin(action_name, edge_name, arcs_set)
        action_key = _normalize_token(action_name)
        edge_key = _normalize_token(edge_name)

        if _should_replace_risk(action_levels.get(action_key), severity, act_origin):
            action_levels[action_key] = (severity, act_origin)
        if _should_replace_risk(edge_levels.get(edge_key), severity, arc_origin):
            edge_levels[edge_key] = (severity, arc_origin)

    return action_levels, edge_levels


def _filter_risks_by_dimension(risk_strings: list[str], dimension: str) -> list[str]:
    prefix = f"[{dimension}]"
    return [r for r in risk_strings if r.startswith(prefix)]


# ---------------------------------------------------------------------------
# Template topology – scanned once, reused by all directional filters
# ---------------------------------------------------------------------------

@dataclass
class _EdgeInfo:
    edge_id: str
    source: str
    target: str
    label_tokens: list[str] = field(default_factory=list)


@dataclass
class _Topology:
    """Pre-parsed draw.io template topology."""
    mx_root: Element
    subject_ids: set[str] = field(default_factory=set)
    action_ids: set[str] = field(default_factory=set)
    subject_name_by_id: dict[str, str] = field(default_factory=dict)
    action_name_by_id: dict[str, str] = field(default_factory=dict)
    edges: list[_EdgeInfo] = field(default_factory=list)


def _scan_topology(xml_root: Element) -> _Topology | None:
    mx_root = xml_root.find("./diagram/mxGraphModel/root")
    if mx_root is None:
        return None

    topo = _Topology(mx_root=mx_root)

    # Classify vertices.
    for cell in mx_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        cell_id = cell.get("id", "")
        if not cell_id:
            continue
        style_map = _parse_style(cell.get("style", ""))
        token = _normalize_token(cell.get("value", ""))
        if "ellipse" in style_map:
            topo.subject_ids.add(cell_id)
            topo.subject_name_by_id[cell_id] = token
        elif style_map.get("rounded") == "0":
            topo.action_ids.add(cell_id)
            if token:
                topo.action_name_by_id[cell_id] = token

    # Collect edges with their label children.
    child_labels: dict[str, list[str]] = {}  # parent edge_id → label tokens
    for cell in mx_root.findall("mxCell"):
        parent_id = cell.get("parent", "")
        val = cell.get("value", "")
        if parent_id and val:
            token = _normalize_token(val)
            if token:
                child_labels.setdefault(parent_id, []).append(token)

    for cell in mx_root.findall("mxCell"):
        if cell.get("edge") != "1":
            continue
        source = cell.get("source")
        target = cell.get("target")
        if not source or not target:
            continue
        edge_id = cell.get("id", "")
        topo.edges.append(_EdgeInfo(
            edge_id=edge_id,
            source=source,
            target=target,
            label_tokens=child_labels.get(edge_id, []),
        ))

    return topo


# ---------------------------------------------------------------------------
# Directional filtering – single pass over topology
# ---------------------------------------------------------------------------

def _apply_directional_filters(
    topo: _Topology,
    action_levels: dict[str, tuple[str, str]],
    edge_levels: dict[str, tuple[str, str]],
    assigned_subjects: set[str] | None = None,
) -> tuple[
    dict[str, tuple[str, str]],
    dict[str, tuple[str, str]],
    dict[str, tuple[str, str]],
    set[str],
]:
    """Return (action_levels, edge_levels, subject_levels, cascade_terminal_subjects)
    after directional filtering.  cascade_terminal_subjects are subject IDs colored
    solely by step-4 cascade; they should NOT propagate further.

    Rules:
    - Actions keep assigned/initialization colors; propagated color only if an
      incoming risky edge label exists.
    - Edge labels keep assigned/initialization colors; propagated color only on
      output arcs (action→subject) whose source action is colored.
    - Subjects are colored by incoming risky edge labels (action→subject only).
    """

    # --- 1. Directional action filtering ---
    filtered_actions: dict[str, tuple[str, str]] = {
        name: level for name, level in action_levels.items()
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
            if _should_replace_risk(filtered_actions.get(action_token), severity, origin):
                filtered_actions[action_token] = (severity, origin)

    # --- 2. Directional edge filtering (action→subject output arcs) ---
    # Keep labels on action→subject arcs whose source action is colored.
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

    # --- 3. Subject coloring (action→subject edges only) ---
    subjects_set = assigned_subjects or set()
    assigned_subject_tokens = {_normalize_token(s) for s in subjects_set}
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
        if _should_replace_risk(subject_levels.get(subject_id), severity, origin):
            subject_levels[subject_id] = (severity, origin)

    # --- 4. Cascade through colored subjects: subject→action→output arcs ---
    # When a colored subject feeds into an action, that input arc is colored,
    # the action itself becomes colored, and its output arcs inherit the risk.
    # Feedback actions (f1, f2, …) are excluded: cascade stops before them.
    for edge in topo.edges:
        if edge.source not in topo.subject_ids or edge.target not in topo.action_ids:
            continue
        if edge.source not in subject_levels:
            continue
        action_token = topo.action_name_by_id.get(edge.target, "")
        if not action_token:
            continue
        # Do not cascade into feedback actions.
        if _FEEDBACK_ACTION_PATTERN.match(action_token):
            continue
        # Color input arc labels from colored subject.  Labels inherit the
        # subject's risk even when the analysis never flagged them (e.g. the
        # arc's property is at baseline).
        subject_severity, _ = subject_levels[edge.source]
        for label in edge.label_tokens:
            if label not in filtered_edges:
                if label in edge_levels:
                    filtered_edges[label] = edge_levels[label]
                else:
                    filtered_edges[label] = (subject_severity, "propagated")

        # Color the downstream action from these input labels (or directly
        # from the subject when the edge is unlabeled).
        current = filtered_actions.get(action_token)
        if current is not None and current[1] in {"assigned", "initialization"}:
            continue

        if edge.label_tokens:
            for label in edge.label_tokens:
                if label not in filtered_edges:
                    continue
                severity, origin = filtered_edges[label]
                if _should_replace_risk(filtered_actions.get(action_token), severity, origin):
                    filtered_actions[action_token] = (severity, origin)
        else:
            # Unlabeled edge: propagate the subject's risk directly.
            if _should_replace_risk(filtered_actions.get(action_token), subject_severity, "propagated"):
                filtered_actions[action_token] = (subject_severity, "propagated")

    # Color output arcs of actions that were newly colored in step 4,
    # and propagate to the target subjects of those arcs.
    cascade_terminal: set[str] = set()
    for edge in topo.edges:
        if edge.source in topo.action_ids and edge.target in topo.subject_ids:
            source_token = topo.action_name_by_id.get(edge.source, "")
            if source_token not in filtered_actions:
                continue
            act_severity, act_origin = filtered_actions[source_token]
            for label in edge.label_tokens:
                if label not in filtered_edges:
                    filtered_edges[label] = (act_severity, "propagated")
            # Color the target subject of this output arc (terminal – no further propagation).
            if _should_replace_risk(subject_levels.get(edge.target), act_severity, "propagated"):
                subject_levels[edge.target] = (act_severity, "propagated")
                cascade_terminal.add(edge.target)

    return filtered_actions, filtered_edges, subject_levels, cascade_terminal


# ---------------------------------------------------------------------------
# Colored subject → outgoing arc propagation
# ---------------------------------------------------------------------------


def _propagate_risk_from_subjects(
    topo: _Topology,
    edge_levels: dict[str, tuple[str, str]],
    subject_levels: dict[str, tuple[str, str]],
    skip_subjects: set[str] | None = None,
) -> None:
    """Extend edge_levels with risk from any colored subject (outgoing arcs only).

    Skips arcs targeting feedback actions (f1, f2, …) to prevent backward
    cascade through the feedback loop.
    """
    for edge in topo.edges:
        subject_id = edge.source
        if subject_id not in subject_levels:
            continue
        if skip_subjects and subject_id in skip_subjects:
            continue
        # Do not propagate into feedback actions.
        if edge.target in topo.action_ids:
            target_token = topo.action_name_by_id.get(edge.target, "")
            if _FEEDBACK_ACTION_PATTERN.match(target_token):
                continue
        severity, _ = subject_levels[subject_id]
        for label in edge.label_tokens:
            if label not in edge_levels:
                edge_levels[label] = (severity, "propagated")


# ---------------------------------------------------------------------------
# Progressive stage risk builder
# ---------------------------------------------------------------------------

def _parse_risk_action_name(risk: str) -> str | None:
    match = _RISK_EDGE_PATTERN.search(risk)
    return match.group(1) if match else None


def _parse_fired_action_name(action_text: str) -> str | None:
    match = _CPN_ACTION_PATTERN.search(action_text)
    return match.group(1) if match else None


def _build_progressive_stage_risks(
    risk_strings: list[str],
    states,
    development_cycles: int,
    feedback: bool,
) -> dict[tuple[int, int], list[str]]:
    risks_by_action: dict[str, list[str]] = {}
    for risk in risk_strings:
        action_name = _parse_risk_action_name(risk)
        if action_name is not None:
            risks_by_action.setdefault(action_name, []).append(risk)

    fired_actions_by_cycle_stage: dict[tuple[int, str], set[str]] = {}
    for state in states:
        action_name = _parse_fired_action_name(state.action)
        if action_name is not None:
            key = (state.cycle_index, state.stage)
            fired_actions_by_cycle_stage.setdefault(key, set()).add(action_name)

    ordered_stages = _STAGE_SEQUENCE if feedback else _STAGE_SEQUENCE[:-1]
    stage_indexes = {name: idx for idx, name in enumerate(ordered_stages)}

    progressive: dict[tuple[int, int], list[str]] = {}
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
                    if risk not in seen:
                        seen.add(risk)
                        stage_risks.append(risk)
            progressive[(cycle_index, stage_indexes[stage_name])] = stage_risks

    return progressive


# ---------------------------------------------------------------------------
# Legend
# ---------------------------------------------------------------------------

_LEGEND_ENTRIES = [
    ("panel",       "Propagation Color Legend",                     "#f8fafc", "#94a3b8", None,      True),
    ("prop-high",   "Propagated High risk (action or arc label)",   "#fecaca", "#b91c1c", "#7f1d1d", False),
    ("prop-medium", "Propagated Medium risk (action or arc label)", "#fde68a", "#b45309", "#78350f", False),
    ("assign-high", "Assigned High risk (initialize-time)",         "#e9d5ff", "#7e22ce", "#4c1d95", False),
    ("assign-med",  "Assigned Medium risk",                         "#dbeafe", "#2563eb", "#1e40af", False),
    ("init",        "Initialization action",                        "#bbf7d0", "#16a34a", "#14532d", False),
]


def _append_propagation_legend(
    mx_root: Element,
    action_levels: dict[str, tuple[str, str]],
    edge_levels: dict[str, tuple[str, str]],
    subject_levels: dict[str, tuple[str, str]],
) -> None:
    existing_ids = {
        cell.get("id") for cell in mx_root.findall("mxCell") if cell.get("id")
    }

    def _next_id(suffix: str) -> str:
        base = f"legend-{suffix}"
        if base not in existing_ids:
            existing_ids.add(base)
            return base
        idx = 1
        while f"{base}-{idx}" in existing_ids:
            idx += 1
        existing_ids.add(f"{base}-{idx}")
        return f"{base}-{idx}"

    def _add(suffix: str, value: str, style: str, y: int, height: int = 32) -> None:
        cell_id = _next_id(suffix)
        cell = SubElement(mx_root, "mxCell", id=cell_id, value=value,
                          style=style, vertex="1", parent="1")
        SubElement(cell, "mxGeometry", x="1360", y=str(y),
                   width="410", height=str(height), **{"as": "geometry"})

    y = 20
    for suffix, label, fill, stroke, font, is_header in _LEGEND_ENTRIES:
        font_extra = "fontStyle=1;fontSize=12;" if is_header else f"fontColor={font};fontSize=11;"
        style = (
            f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
            + font_extra
        )
        height = 40 if is_header else 32
        _add(suffix, label, style, y, height)
        y += height + (6 if is_header else 4)

    # Summary rows.
    def _count(levels, origin):
        return sum(1 for _, o in levels.values() if o == origin)

    na, ne, ns = len(action_levels), len(edge_levels), len(subject_levels)
    aa = _count(action_levels, "assigned")
    ia = _count(action_levels, "initialization")
    ae = _count(edge_levels, "assigned")
    ie = _count(edge_levels, "initialization")
    a_s = _count(subject_levels, "assigned")

    _add("scope",
         f"Risk impact coverage: {na} action nodes, {ne} object-arc labels, {ns} subject nodes",
         "rounded=1;whiteSpace=wrap;html=1;fillColor=#e2e8f0;strokeColor=#64748b;fontColor=#1e293b;fontSize=11;",
         y)
    y += 36
    _add("split",
         f"Assigned / Init / Propagated: "
         f"actions {aa}/{ia}/{na - aa - ia}, "
         f"arcs {ae}/{ie}/{ne - ae - ie}, "
         f"subjects {a_s}/0/{ns - a_s}",
         "rounded=1;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#94a3b8;fontColor=#334155;fontSize=11;",
         y)


# ---------------------------------------------------------------------------
# Core render: recolor a draw.io template with propagation data
# ---------------------------------------------------------------------------

def _render_template_propagation_drawio(
    risk_strings: list[str],
    template_path: Path,
    output_path: Path,
    assigned_actions: set[str] | None = None,
    assigned_object_arcs: set[str] | None = None,
    assigned_subjects: set[str] | None = None,
) -> Path:
    xml_text = template_path.read_text(encoding="utf-8")
    root = fromstring(xml_text)

    # 1. Parse risks into raw levels.
    action_levels, edge_levels = _collect_propagation_targets(
        risk_strings,
        assigned_actions=assigned_actions,
        assigned_object_arcs=assigned_object_arcs,
    )

    # 2. Scan template topology once.
    topo = _scan_topology(root)
    if topo is None:
        output_path.write_text(xml_text, encoding="utf-8")
        return output_path

    # 3. Apply all directional filters in one pass.
    action_levels, edge_levels, subject_levels, cascade_terminal = _apply_directional_filters(
        topo, action_levels, edge_levels, assigned_subjects=assigned_subjects,
    )

    # 4. Propagate risk from inferred-module subjects (skip cascade-terminal ones).
    _propagate_risk_from_subjects(topo, edge_levels, subject_levels, skip_subjects=cascade_terminal)

    # 5. Apply colors to cells.
    for cell in root.iter("mxCell"):
        cell_id = cell.get("id", "")
        value = cell.get("value", "")
        normalized = _normalize_token(value)
        style_map = _parse_style(cell.get("style", ""))

        is_action = style_map.get("rounded") == "0"
        is_init = is_action and (
            normalized.endswith("initialize") or normalized.endswith("initialization")
        )
        is_edge_label = "edgeLabel" in style_map or (
            "text" in style_map and "ellipse" not in style_map and not is_action
        )

        # Initialization actions always get green.
        if is_init:
            style_map["fillColor"] = "#bbf7d0"
            style_map["strokeColor"] = "#16a34a"
            style_map["fontColor"] = "#14532d"
            cell.set("style", _serialize_style(style_map))
            if _HTML_TAG_PATTERN.search(value):
                cell.set("value", _clean_cell_value(value))
            continue

        # Determine risk level for this cell.
        severity, origin = "", ""
        if normalized and is_action and normalized in action_levels:
            severity, origin = action_levels[normalized]
        elif normalized and is_edge_label and normalized in edge_levels:
            severity, origin = edge_levels[normalized]
        elif cell_id in subject_levels and "ellipse" in style_map:
            severity, origin = subject_levels[cell_id]

        if not severity:
            # Clear stale colors from unaffected action boxes.
            if is_action:
                for key in ("fillColor", "strokeColor", "fontColor"):
                    style_map.pop(key, None)
                cell.set("style", _serialize_style(style_map))
                if _HTML_TAG_PATTERN.search(value):
                    cell.set("value", _clean_cell_value(value))
            continue

        fill, stroke, font = _risk_palette(severity, origin)
        if "edgeLabel" in style_map:
            style_map["labelBackgroundColor"] = fill
            style_map["fontColor"] = font
            style_map["strokeColor"] = stroke
        elif "text" in style_map and is_edge_label:
            style_map["fontColor"] = font
            style_map.setdefault("fontStyle", "0")
        else:
            style_map["fillColor"] = fill
            style_map["strokeColor"] = stroke
            style_map["fontColor"] = font

        cell.set("style", _serialize_style(style_map))
        if _HTML_TAG_PATTERN.search(value):
            cell.set("value", _clean_cell_value(value))

    _append_propagation_legend(topo.mx_root, action_levels, edge_levels, subject_levels)

    output_path.write_text(tostring(root, encoding="unicode"), encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Output path helpers
# ---------------------------------------------------------------------------

def _derive_drawio_output_path(scenario_name: str, output_file: str | None) -> Path:
    if output_file:
        return Path(output_file)
    return Path("output") / f"{_scenario_stem(scenario_name)}_pic.drawio"


def _derive_png_output_path(stem_name: str, output_file: str | None) -> Path:
    if output_file:
        return Path(output_file)
    return Path("output") / f"{stem_name}.png"


def _derive_dimension_drawio_paths(
    scenario_name: str,
    output_file: str | None,
) -> dict[str, Path]:
    base = Path(output_file) if output_file else _derive_drawio_output_path(scenario_name, None)
    return {
        dim: base.with_name(f"{base.stem}_{dim.lower()}.drawio")
        for dim in _DIMENSIONS
    }


# ---------------------------------------------------------------------------
# draw.io CLI PNG export
# ---------------------------------------------------------------------------

def _find_drawio_command() -> str | None:
    for candidate in ("drawio", "draw.io", "diagrams"):
        resolved = shutil.which(candidate)
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
        details = (result.stderr or result.stdout or "").strip() or f"exit code {result.returncode}"
        last_error = f"command {' '.join(cmd)} failed: {details}"

    raise RuntimeError(f"Failed to export PNG from draw.io XML. Last error: {last_error}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_template_propagation_drawio(
    scenario_name: str,
    risk_strings: list[str],
    template_file: str = "docs/model.drawio",
    output_file: str | None = None,
    assigned_actions: set[str] | None = None,
    assigned_object_arcs: set[str] | None = None,
    assigned_subjects: set[str] | None = None,
) -> Path:
    """Copy the provided draw.io XML template and recolor cells based on propagation risks."""
    template_path = Path(template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Template draw.io file not found: {template_path}")

    output_path = _derive_drawio_output_path(scenario_name, output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return _render_template_propagation_drawio(
        risk_strings, template_path, output_path,
        assigned_actions=assigned_actions,
        assigned_object_arcs=assigned_object_arcs,
        assigned_subjects=assigned_subjects,
    )


def export_template_propagation_drawio_per_dimension(
    scenario_name: str,
    risk_strings: list[str],
    template_file: str = "docs/model.drawio",
    output_file: str | None = None,
    assigned_actions: set[str] | None = None,
    assigned_object_arcs: set[str] | None = None,
    assigned_subjects: set[str] | None = None,
) -> dict[str, Path]:
    """Export one draw.io file per risk dimension."""
    template_path = Path(template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Template draw.io file not found: {template_path}")

    output_paths = _derive_dimension_drawio_paths(scenario_name, output_file)
    exported: dict[str, Path] = {}
    for dimension, path in output_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        exported[dimension] = _render_template_propagation_drawio(
            risk_strings=_filter_risks_by_dimension(risk_strings, dimension),
            template_path=template_path,
            output_path=path,
            assigned_actions=assigned_actions,
            assigned_object_arcs=assigned_object_arcs,
            assigned_subjects=assigned_subjects,
        )
    return exported


def export_template_propagation_drawio_per_stage(
    scenario_name: str,
    risk_strings: list[str],
    states,
    development_cycles: int,
    feedback: bool,
    output_dir: str | None = None,
    template_file: str = "docs/model.drawio",
    assigned_actions: set[str] | None = None,
    assigned_object_arcs: set[str] | None = None,
    assigned_subjects: set[str] | None = None,
) -> list[Path]:
    """Export draw.io files per cycle: initial plus one checkpoint per execution stage."""
    template_path = Path(template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Template draw.io file not found: {template_path}")

    base_dir = Path(output_dir) if output_dir else Path("output")
    base_dir.mkdir(parents=True, exist_ok=True)

    stem = _scenario_stem(scenario_name)
    ordered_stages = _STAGE_SEQUENCE if feedback else _STAGE_SEQUENCE[:-1]
    stage_risks = _build_progressive_stage_risks(
        risk_strings=risk_strings, states=states,
        development_cycles=development_cycles, feedback=feedback,
    )

    exported: list[Path] = []
    for cycle_index in range(1, development_cycles + 1):
        for stage_index, stage_name in enumerate(ordered_stages):
            file_name = f"{stem}_pic_cycle{cycle_index}_stage{stage_index}_{stage_name.lower()}.drawio"
            output_path = base_dir / file_name
            exported.append(
                _render_template_propagation_drawio(
                    risk_strings=stage_risks.get((cycle_index, stage_index), []),
                    template_path=template_path,
                    output_path=output_path,
                    assigned_actions=assigned_actions,
                    assigned_object_arcs=assigned_object_arcs,
                    assigned_subjects=assigned_subjects,
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

    output_path = _derive_png_output_path(input_path.stem, output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _run_drawio_png_export(input_path, output_path)
    return output_path


def export_reference_model_png(
    source_drawio_file: str = "docs/model.drawio",
    output_file: str | None = None,
) -> Path:
    """Export the provided canonical model draw.io XML to PNG."""
    return export_drawio_xml_to_png(source_drawio_file, output_file=output_file)
