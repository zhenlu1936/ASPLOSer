from __future__ import annotations

"""Generate scenario docs from YAML metadata and override blocks."""

from pathlib import Path
from string import Template

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_DIR = ROOT / "scripts" / "scenarios"
TEMPLATE_PATH = SCENARIOS_DIR / "template.md"

HIGH_VALUE_BY_ATTR = {
    "credibility": "Trusted",
    "confidentiality": "Confidential",
    "correctness": "Correct",
    "continuity": "Continuous",
}


def _format_attr_value(attr: str, value: str) -> str:
    high_value = HIGH_VALUE_BY_ATTR.get(attr)
    if high_value is None:
        return value
    return value if value == high_value else f"**{value}**"


def _render_node_section(payload: dict) -> str:
    subject_overrides = payload.get("subject_overrides", [])
    action_overrides = payload.get("action_overrides", [])
    if not subject_overrides and not action_overrides:
        return "No subject/action overrides."

    lines: list[str] = ["Overrides and inferred highlights:", ""]
    for entry in sorted(subject_overrides, key=lambda item: item.get("name", "")):
        node_name = entry.get("name", "UnknownNode")
        attrs = entry.get("attributes", {})
        for attr_name in ["credibility", "confidentiality", "correctness", "continuity"]:
            if attr_name in attrs:
                val = _format_attr_value(attr_name, str(attrs[attr_name]))
                lines.append(f"- {node_name} {attr_name}: {val}")

    for entry in sorted(action_overrides, key=lambda item: item.get("name", "")):
        node_name = entry.get("name", "UnknownAction")
        attrs = entry.get("attributes", {})
        for attr_name in ["confidentiality", "correctness", "continuity"]:
            if attr_name in attrs:
                val = _format_attr_value(attr_name, str(attrs[attr_name]))
                lines.append(f"- {node_name} {attr_name}: {val}")

    return "\n".join(lines)


def _render_edge_section(payload: dict) -> str:
    lines: list[str] = []

    edge_overrides = payload.get("object_initialization_overrides", [])
    if edge_overrides:
        if lines:
            lines.append("")
        lines.append("Initialization object overrides:")
        lines.append("")
        for entry in edge_overrides:
            source = entry.get("source", "*")   # action
            target = entry.get("target", "*")   # subject
            name = entry.get("name", "UnknownObject")  # object name (P-suffix)
            attrs = entry.get("attributes", {})
            attr_bits = []
            for attr_name in ["confidentiality", "correctness", "continuity"]:
                if attr_name in attrs:
                    val = _format_attr_value(attr_name, str(attrs[attr_name]))
                    attr_bits.append(f"{attr_name} {val}")
            attr_desc = ", ".join(attr_bits) if attr_bits else "attribute overrides"
            lines.append(f"- {name} ({source} -> {target}): {attr_desc}")

    if not lines:
        return "No edge overrides."

    return "\n".join(lines)


def _render_doc(template: Template, scenario_file: Path, payload: dict) -> str:
    metadata = payload.get("doc_metadata") or {}
    scenario_num = "".join(ch for ch in scenario_file.stem if ch.isdigit()) or "?"

    title = metadata.get("title") or f"Scenario {scenario_num}: {payload.get('name', scenario_file.stem)}"
    composition_note = metadata.get("composition_note") or "Scenario composition metadata is defined in the scenario YAML file."
    overview = metadata.get("overview") or "This scenario applies runtime and edge overrides to represent a specific deployment condition."

    values = {
        "TITLE": str(title),
        "SCENARIO_FILE": scenario_file.name,
        "COMPOSITION_NOTE": str(composition_note),
        "OVERVIEW": str(overview),
        "NODE_SECTION": _render_node_section(payload),
        "EDGE_SECTION": _render_edge_section(payload),
    }
    return template.safe_substitute(values)


def main() -> None:
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    scenario_files = sorted(SCENARIOS_DIR.glob("*.yaml"))
    for scenario_file in scenario_files:
        payload = yaml.safe_load(scenario_file.read_text(encoding="utf-8")) or {}
        doc_content = _render_doc(template, scenario_file, payload)
        doc_path = SCENARIOS_DIR / f"{scenario_file.stem}.md"
        doc_path.write_text(doc_content + "\n", encoding="utf-8")
        print(f"Generated {doc_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
