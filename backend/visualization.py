from __future__ import annotations

"""Visualization export helpers for Model 2.0 system views."""

from pathlib import Path
import re
import shutil
import subprocess
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from .propagation import (
    SECURITY_DIMENSIONS,
    EdgeInfo,
    Topology,
    apply_directional_filters,
    build_progressive_stage_risks,
    clean_label_value,
    collect_propagation_targets,
    filter_risks_by_dimension,
    has_html_markup,
    normalize_token,
    ordered_stage_names,
    parse_fired_action_name,
    parse_risk_action_name,
    parse_risk_edge,
    propagate_risk_from_subjects,
)

# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------


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


def _require_template(template_file: str) -> Path:
    path = Path(template_file)
    if not path.exists():
        raise FileNotFoundError(f"Template draw.io file not found: {path}")
    return path


# ---------------------------------------------------------------------------
# Template topology scanner
# ---------------------------------------------------------------------------

def _scan_topology(mx_root: Element | None) -> Topology | None:
    if mx_root is None:
        return None

    topo = Topology()

    # Classify vertices.
    for cell in mx_root.findall("mxCell"):
        if cell.get("vertex") != "1":
            continue
        cell_id = cell.get("id", "")
        if not cell_id:
            continue
        style_map = _parse_style(cell.get("style", ""))
        token = normalize_token(cell.get("value", ""))
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
            token = normalize_token(val)
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
        topo.edges.append(EdgeInfo(
            edge_id=edge_id,
            source=source,
            target=target,
            label_tokens=child_labels.get(edge_id, []),
        ))

    return topo


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
    action_levels, edge_levels = collect_propagation_targets(
        risk_strings,
        assigned_actions=assigned_actions,
        assigned_object_arcs=assigned_object_arcs,
    )

    # 2. Scan template topology once.
    mx_root = root.find("./diagram/mxGraphModel/root")
    topo = _scan_topology(mx_root)
    if topo is None:
        output_path.write_text(xml_text, encoding="utf-8")
        return output_path

    # 3. Apply all directional filters in one pass.
    action_levels, edge_levels, subject_levels, cascade_terminal = apply_directional_filters(
        topo, action_levels, edge_levels, assigned_subjects=assigned_subjects,
    )

    # 4. Propagate risk from inferred-module subjects (skip cascade-terminal ones).
    propagate_risk_from_subjects(topo, edge_levels, subject_levels, skip_subjects=cascade_terminal)

    # 5. Apply colors to cells.
    for cell in root.iter("mxCell"):
        cell_id = cell.get("id", "")
        value = cell.get("value", "")
        normalized = normalize_token(value)
        style_map = _parse_style(cell.get("style", ""))

        is_action = style_map.get("rounded") == "0"
        is_init = is_action and normalized.endswith("initialize")
        is_edge_label = "edgeLabel" in style_map or (
            "text" in style_map and "ellipse" not in style_map and not is_action
        )

        # Initialization actions always get green.
        if is_init:
            style_map["fillColor"] = "#bbf7d0"
            style_map["strokeColor"] = "#16a34a"
            style_map["fontColor"] = "#14532d"
            cell.set("style", _serialize_style(style_map))
            if has_html_markup(value):
                cell.set("value", clean_label_value(value))
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
                if has_html_markup(value):
                    cell.set("value", clean_label_value(value))
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
        if has_html_markup(value):
            cell.set("value", clean_label_value(value))

    _append_propagation_legend(mx_root, action_levels, edge_levels, subject_levels)

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
        for dim in SECURITY_DIMENSIONS
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
    template_path = _require_template(template_file)
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
    template_path = _require_template(template_file)
    output_paths = _derive_dimension_drawio_paths(scenario_name, output_file)
    exported: dict[str, Path] = {}
    for dimension, path in output_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        exported[dimension] = _render_template_propagation_drawio(
            risk_strings=filter_risks_by_dimension(risk_strings, dimension),
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
    template_path = _require_template(template_file)
    base_dir = Path(output_dir) if output_dir else Path("output")
    base_dir.mkdir(parents=True, exist_ok=True)

    stem = _scenario_stem(scenario_name)
    ordered_stages = ordered_stage_names(feedback)
    stage_risks = build_progressive_stage_risks(
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


# ---------------------------------------------------------------------------
# GIF animation export (per-dimension, one frame per CPN transition)
# ---------------------------------------------------------------------------

# Banner accent colors per dimension (RGB tuples for PIL).
_GIF_DIM_COLORS = {
    "Confidentiality": (147, 197, 253),  # blue-300
    "Integrity":       (134, 239, 172),  # green-300
    "Availability":    (252, 211, 77),   # yellow-300
}


def _gif_load_font(size: int):
    """Load a PIL TrueType font, falling back to the built-in default."""
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    for candidate in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


_RISK_SUMMARY_RE = re.compile(
    r"\[(?P<dim>\w+)\]\[(?P<sev>\w+)\].*?on edge\s+(?P<act>[^/\s]+)/(?P<arc>\S+)\s*\((?P<detail>[^)]+)\)"
)


def _gif_frame0_overlay(img, assigned_events: list, dimension: str):
    """Overlay an annotation box onto the frame-0 diagram listing assigned defects."""
    from PIL import Image, ImageDraw

    if not assigned_events:
        return img

    img = img.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_title = _gif_load_font(16)
    font_body  = _gif_load_font(13)
    kw_t = {"font": font_title} if font_title else {}
    kw_b = {"font": font_body}  if font_body  else {}

    LINE_H = 22
    PAD    = 12

    dim_color   = _GIF_DIM_COLORS.get(dimension, (255, 255, 255))
    title_text  = f"Initial {dimension} Assignment"
    event_lines = [_gif_event_short(e, is_assigned=True) for e in assigned_events]

    # Estimate box width from longest line.
    all_texts = [title_text] + event_lines
    approx_w  = max(len(t) for t in all_texts) * 8 + PAD * 2
    box_w = min(max(320, approx_w), img.width - 30)
    box_h = PAD + LINE_H + len(event_lines) * LINE_H + PAD

    x, y = 14, 14  # top-left corner of the diagram canvas

    draw.rectangle(
        [x, y, x + box_w, y + box_h],
        fill=(15, 23, 42, 218),
        outline=(55, 80, 120, 255),
        width=1,
    )
    draw.text((x + PAD, y + PAD), title_text, fill=dim_color, **kw_t)
    for i, line in enumerate(event_lines):
        draw.text(
            (x + PAD, y + PAD + LINE_H + i * LINE_H),
            line,
            fill=(216, 180, 254),  # purple-300
            **kw_b,
        )

    return Image.alpha_composite(img, overlay).convert("RGB")


def _gif_event_short(risk: str, is_assigned: bool = False) -> str:
    """Compress a risk string to a single compact bullet line."""
    m = _RISK_SUMMARY_RE.search(risk)
    if m:
        prefix = "[assigned] " if is_assigned else "[+propagated] "
        return f"{prefix}{m.group('act')} / {m.group('arc')}  ({m.group('detail')})"
    # fallback: truncate raw string
    return risk[:100]


def _gif_frame_banner(
    img,
    dimension: str,
    step_label: str,
    delta_risks: list[str],
    banner_events: list[str] | None = None,
    events_are_assigned: bool = False,
    fixed_lines: int = 0,
):
    """Append a status banner below a diagram frame PIL Image.

    ``banner_events`` are listed as bullet lines in the banner body.
    If None, ``delta_risks`` is used.  ``events_are_assigned`` controls
    whether bullets say "[assigned]" or "[+propagated]".
    ``fixed_lines`` sets a minimum banner height so all frames in a GIF have
    identical dimensions (required for proper GIF encoding).

    Returns a new PIL Image with the banner stitched on at the bottom.
    """
    from PIL import Image, ImageDraw

    if banner_events is None:
        banner_events = delta_risks

    img = img.convert("RGB")
    w, h = img.size

    LINE_H    = 22   # pixels per event bullet line
    HEADER_H  = 62   # fixed header area height
    n_lines   = max(len(banner_events), fixed_lines)
    banner_h  = HEADER_H + n_lines * LINE_H
    banner    = Image.new("RGB", (w, banner_h), (15, 23, 42))   # slate-950
    draw      = ImageDraw.Draw(banner)

    font_title = _gif_load_font(18)
    font_body  = _gif_load_font(14)
    font_event = _gif_load_font(13)
    kw_t = {"font": font_title} if font_title else {}
    kw_b = {"font": font_body}  if font_body  else {}
    kw_e = {"font": font_event} if font_event else {}

    # Left side: "[ Dimension ]" + step label.
    dim_color = _GIF_DIM_COLORS.get(dimension, (255, 255, 255))
    draw.text((14, 6),  f"[ {dimension} ]", fill=dim_color, **kw_t)
    draw.text((14, 34), step_label, fill=(203, 213, 225), **kw_b)

    # Right side: summary indicator.
    if delta_risks:
        risk_text  = f"+{len(delta_risks)} new risk(s) this step"
        risk_color = (252, 165, 165)   # red-300
    elif events_are_assigned and banner_events:
        risk_text  = f"{len(banner_events)} assigned defect(s)"
        risk_color = (216, 180, 254)   # purple-300
    else:
        risk_text  = "No new risks this step"
        risk_color = (167, 243, 208)   # green-200

    try:
        bbox = draw.textbbox((0, 0), risk_text, font=font_title)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw = len(risk_text) * 10

    draw.text((w - tw - 14, 6), risk_text, fill=risk_color, **kw_t)

    # Horizontal separator.
    draw.line([(0, HEADER_H - 2), (w, HEADER_H - 2)], fill=(30, 41, 59), width=1)

    # Event bullet lines.
    bullet_color = (
        (216, 180, 254) if events_are_assigned else (252, 165, 165)  # purple / red
    )
    for i, risk in enumerate(banner_events):
        y = HEADER_H + i * LINE_H + 2
        short = _gif_event_short(risk, is_assigned=events_are_assigned)
        draw.text((14, y), short, fill=bullet_color, **kw_e)

    combined = Image.new("RGB", (w, h + banner_h))
    combined.paste(img, (0, 0))
    combined.paste(banner, (0, h))
    return combined


def export_propagation_gif_per_dimension(
    system,
    states,
    scenario_name: str,
    output_dir: str | None = None,
    frame_duration_ms: int = 600,
    template_file: str = "docs/model.drawio",
) -> dict[str, Path]:
    """Export three GIF files (Confidentiality / Integrity / Availability).

    Each frame is the draw.io template recolored with cumulative propagation
    risks up to that simulation step, annotated with a step/stage banner,
    converted to PNG via the draw.io CLI, and assembled into an animated GIF.
    Frame 0 shows the clean baseline (no risks yet).

    Draw.io renders are cached by risk fingerprint to avoid redundant CLI
    calls when consecutive steps introduce no new risks.

    Requires: draw.io CLI in PATH, and Pillow (``pip install pillow``).
    Returns a dict mapping dimension name → output GIF path.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "Pillow is required for GIF export. Install with: pip install pillow"
        ) from exc

    import tempfile

    template_path = _require_template(template_file)
    base_dir = Path(output_dir) if output_dir else Path("output")
    base_dir.mkdir(parents=True, exist_ok=True)
    stem = _scenario_stem(scenario_name)

    # Build per-frame data: (cumulative_risks, step_label, delta_risks).
    # Frame 0 shows scenario-assigned defects only (purple, no transitions yet).
    # Collect all risks across all steps first so we can filter to assigned ones.
    cumulative: list[str] = []
    seen: set[str] = set()
    step_frames: list[tuple[list[str], str, list[str]]] = []
    for state in states:
        delta = [r for r in (state.risks or []) if r not in seen]
        for r in delta:
            seen.add(r)
            cumulative.append(r)
        action_id = parse_fired_action_name(state.action) or "—"
        label = f"Step {state.step_index}  |  {state.stage}  |  {action_id}"
        step_frames.append((list(cumulative), label, delta))

    # Assigned-origin sets from the system (for correct purple/blue coloring).
    assigned_actions     = getattr(system, "assigned_actions",     None) or set()
    assigned_object_arcs = getattr(system, "assigned_object_arcs", None) or set()
    assigned_subjects    = getattr(system, "assigned_subjects",    None) or set()

    # Frame 0: show scenario-assigned defects from the start (purple coloring),
    # even before any transitions fire.
    all_final_risks = step_frames[-1][0] if step_frames else []
    assigned_initial: list[str] = []
    for risk in all_final_risks:
        action_name = parse_risk_action_name(risk)
        if action_name and action_name in assigned_actions:
            assigned_initial.append(risk)
        else:
            # Also include risks whose object arc was directly assigned.
            parsed_edge = parse_risk_edge(risk)
            if parsed_edge and f"{parsed_edge[0]}/{parsed_edge[1]}" in assigned_object_arcs:
                assigned_initial.append(risk)

    n_assigned = len(assigned_initial)
    if n_assigned:
        init_label = (
            f"Step 0  |  Initial state  |  {n_assigned} assigned defect(s) shown"
        )
    else:
        init_label = "Step 0  |  Initial state  |  (no scenario-assigned defects)"

    frame_data: list[tuple[list[str], str, list[str]]] = [
        (assigned_initial, init_label, [])
    ]
    frame_data.extend(step_frames)

    output_paths: dict[str, Path] = {}

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # Cache: (dimension, risk_tuple) → cached PNG Path.
        # Avoids duplicate draw.io CLI calls when consecutive steps share
        # the same cumulative risk set.
        _png_cache: dict[tuple, Path] = {}

        for dimension in SECURITY_DIMENSIONS:
            frames_pil: list[Image.Image] = []

            # Pre-compute max bullet lines across all frames so every frame
            # gets the same banner height (GIF frames must be identical size).
            max_bullets = max(
                len(filter_risks_by_dimension(
                    risks if i == 0 else delta, dimension
                ))
                for i, (risks, _, delta) in enumerate(frame_data)
            )

            for risk_list, label, delta in frame_data:
                dim_risks = filter_risks_by_dimension(risk_list, dimension)
                cache_key = (dimension, tuple(dim_risks))

                if cache_key not in _png_cache:
                    idx = len(_png_cache)
                    drawio_path = tmp / f"c{idx}_{dimension.lower()}.drawio"
                    png_path    = tmp / f"c{idx}_{dimension.lower()}.png"
                    _render_template_propagation_drawio(
                        risk_strings=dim_risks,
                        template_path=template_path,
                        output_path=drawio_path,
                        assigned_actions=assigned_actions,
                        assigned_object_arcs=assigned_object_arcs,
                        assigned_subjects=assigned_subjects,
                    )
                    _run_drawio_png_export(drawio_path, png_path)
                    _png_cache[cache_key] = png_path

                src_png = _png_cache[cache_key]
                if not src_png.exists():
                    continue

                # Filter delta/assigned to only risks belonging to this dimension.
                dim_delta = filter_risks_by_dimension(delta, dimension)

                # Frame 0 has no delta; show its assigned_initial as bullets.
                is_frame0 = (risk_list is frame_data[0][0] and label == frame_data[0][1])
                if is_frame0:
                    banner_evts = filter_risks_by_dimension(risk_list, dimension)
                    is_assigned = True
                else:
                    banner_evts = dim_delta
                    is_assigned = False

                frame_img = Image.open(src_png).copy()
                if is_frame0 and banner_evts:
                    frame_img = _gif_frame0_overlay(frame_img, banner_evts, dimension)
                frames_pil.append(
                    _gif_frame_banner(
                        frame_img, dimension, label, dim_delta,
                        banner_events=banner_evts,
                        events_are_assigned=is_assigned,
                        fixed_lines=max_bullets,
                    )
                )

            if not frames_pil:
                continue

            out_path = base_dir / f"{stem}_{dimension.lower()[:4]}.gif"
            frames_pil[0].save(
                out_path,
                save_all=True,
                append_images=frames_pil[1:],
                duration=frame_duration_ms,
                loop=0,
                optimize=False,
            )
            output_paths[dimension] = out_path

    return output_paths
