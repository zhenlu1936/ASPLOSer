from __future__ import annotations

"""CLI entrypoint for ASPLOSER Model 2.0 scenarios and simulation."""

import argparse
from pathlib import Path

from backend import (
    SECURITY_DIMENSIONS,
    aggregate_risk_strings,
    build_analysis_snapshot,
    build_default_system,
    exclude_feedback_risks,
    export_drawio_xml_to_png,
    export_propagation_gif_per_dimension,
    export_reference_model_png,
    export_template_propagation_drawio_per_dimension,
    export_template_propagation_drawio_per_stage,
    export_template_propagation_drawio,
    get_available_scenarios,
    load_scenario_from_file,
    log_propagation_events,
    print_propagation_summary,
    project_system_to_model2,
    run_cpn_cycles,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ASPLOSER framework with scenario support")
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Path to scenario file (e.g., scripts/scenarios/corporations.yaml)",
    )
    parser.add_argument("--cycles", type=int, default=1, help="Number of development cycles")
    parser.add_argument(
        "--no-feedback",
        action="store_true",
        help="Disable feedback stage in each cycle",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenario files and exit",
    )
    parser.add_argument(
        "--export-drawio",
        nargs="?",
        const="AUTO",
        type=str,
        default=None,
        help="Export holistic model picture as draw.io (.drawio). Optional path overrides default <scenario>_pic.drawio",
    )
    parser.add_argument(
        "--export-drawio-per-stage",
        nargs="?",
        const="AUTO",
        type=str,
        default=None,
        help=(
            "Export six draw.io files per cycle (initial + five stages). "
            "Optional argument sets output directory."
        ),
    )
    parser.add_argument(
        "--export-png",
        nargs="?",
        const="AUTO",
        type=str,
        default=None,
        help="Export scenario draw.io diagram to PNG. Optional path overrides default <scenario>_pic.png",
    )
    parser.add_argument(
        "--export-model-png",
        nargs="?",
        const="AUTO",
        type=str,
        default=None,
        help="Export reference model docs/model.drawio to PNG. Optional path overrides default output/model.png",
    )
    parser.add_argument(
        "--export-gif",
        nargs="?",
        const="AUTO",
        type=str,
        default=None,
        help=(
            "Export per-dimension GIF animations (Conf/Int/Avail), one frame per CPN tick. "
            "Optional argument sets output directory."
        ),
    )
    return parser


def _print_available_scenarios() -> None:
    scenarios = get_available_scenarios()
    print("Available scenarios:")
    for scenario in scenarios:
        print(f"  - {scenario}")


def _load_system(scenario_path: str | None):
    if scenario_path:
        system = load_scenario_from_file(scenario_path)
        return system, scenario_path
    return build_default_system(), "default (asploser)"


def _scenario_stem(scenario_name: str, has_custom_scenario: bool) -> str:
    if not has_custom_scenario:
        return "default"
    return Path(scenario_name).stem


def _optional_export_path(export_arg: str | None) -> str | None:
    return None if export_arg in (None, "AUTO") else export_arg


def _visualization_assignments(system) -> dict:
    return {
        "assigned_actions": system.assigned_actions,
        "assigned_object_arcs": system.assigned_object_arcs,
        "assigned_subjects": system.assigned_subjects,
    }


def _print_dimension_exports(title: str, paths: dict) -> None:
    print(title)
    for dimension in SECURITY_DIMENSIONS:
        print(f"  - {dimension}: {paths[dimension]}")
    print()


def _dimension_png_output_path(custom_path: str | None, dimension: str) -> str | None:
    if custom_path is None:
        return None
    custom_png = Path(custom_path)
    suffix = custom_png.suffix or ".png"
    return str(custom_png.with_name(f"{custom_png.stem}_{dimension.lower()}{suffix}"))


def _maybe_export_gif(
    system,
    scenario_name: str,
    states,
    export_gif_arg: str | None,
) -> None:
    if not export_gif_arg:
        return
    output_dir = _optional_export_path(export_gif_arg)
    try:
        gif_paths = export_propagation_gif_per_dimension(
            system=system,
            states=states,
            scenario_name=scenario_name,
            output_dir=output_dir,
        )
    except (ImportError, RuntimeError) as exc:
        print(f"GIF export failed: {exc}")
        print()
        return
    print("Per-dimension GIF animations exported:")
    for dimension, path in gif_paths.items():
        print(f"  - {dimension}: {path}")
    print()


def _print_system_summary(system, scenario_name: str) -> None:
    print("=== ASPLOSER Framework ===")
    print(f"Scenario: {scenario_name}")
    print(f"Nodes: {len(system.graph.nodes)}")
    print(f"Actions: {len(system.graph.actions)}")
    print(f"Edges: {len(system.graph.edges)}")
    model2 = project_system_to_model2(system)
    print(
        "Model 2.0 projection: "
        f"subjects={len(model2.subjects)}, "
        f"actions={len(model2.actions)}, "
        f"object_arcs={len(model2.object_arcs)}"
    )
    print()


def _maybe_export_drawio(
    system,
    scenario_name: str,
    export_drawio_arg: str | None,
    base_risk_strs: list[str],
):
    if not export_drawio_arg:
        return None
    custom_path = _optional_export_path(export_drawio_arg)
    assignment_kwargs = _visualization_assignments(system)
    drawio_path = export_template_propagation_drawio(
        scenario_name=scenario_name,
        risk_strings=base_risk_strs,
        output_file=custom_path,
        **assignment_kwargs,
    )
    dimension_paths = export_template_propagation_drawio_per_dimension(
        scenario_name=scenario_name,
        risk_strings=base_risk_strs,
        output_file=custom_path,
        **assignment_kwargs,
    )
    print(f"Holistic model draw.io exported to: {drawio_path}")
    _print_dimension_exports("Dimension-specific draw.io files exported:", dimension_paths)
    return drawio_path


def _maybe_export_model_png(export_model_png_arg: str | None) -> None:
    if not export_model_png_arg:
        return
    custom_path = _optional_export_path(export_model_png_arg)
    try:
        png_path = export_reference_model_png(output_file=custom_path)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"PNG export failed: {exc}")
        print()
        return
    print(f"Reference model PNG exported to: {png_path}")
    print()


def _maybe_export_scenario_png(
    system,
    scenario_name: str,
    export_png_arg: str | None,
    existing_drawio_path,
    base_risk_strs: list[str],
) -> None:
    if not export_png_arg:
        return

    source_drawio = existing_drawio_path
    if source_drawio is None:
        source_drawio = export_template_propagation_drawio(
            scenario_name=scenario_name,
            risk_strings=base_risk_strs,
            **_visualization_assignments(system),
        )

    dimension_drawio_paths = export_template_propagation_drawio_per_dimension(
        scenario_name=scenario_name,
        risk_strings=base_risk_strs,
        **_visualization_assignments(system),
    )

    custom_path = _optional_export_path(export_png_arg)
    try:
        png_path = export_drawio_xml_to_png(source_drawio, output_file=custom_path)
        dimension_png_paths = {}
        for dimension in SECURITY_DIMENSIONS:
            dimension_drawio = dimension_drawio_paths[dimension]
            dimension_png_paths[dimension] = export_drawio_xml_to_png(
                dimension_drawio,
                output_file=_dimension_png_output_path(custom_path, dimension),
            )
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"PNG export failed: {exc}")
        print()
        return
    print(f"Holistic model PNG exported to: {png_path}")
    _print_dimension_exports("Dimension-specific PNG files exported:", dimension_png_paths)


def _maybe_export_drawio_per_stage(
    system,
    scenario_name: str,
    export_drawio_per_stage_arg: str | None,
    base_risk_strs: list[str],
    states,
    development_cycles: int,
    feedback: bool,
) -> None:
    if not export_drawio_per_stage_arg:
        return

    output_dir = _optional_export_path(export_drawio_per_stage_arg)
    exported_paths = export_template_propagation_drawio_per_stage(
        scenario_name=scenario_name,
        risk_strings=base_risk_strs,
        states=states,
        development_cycles=development_cycles,
        feedback=feedback,
        output_dir=output_dir,
        **_visualization_assignments(system),
    )

    if not exported_paths:
        print("No per-stage draw.io files were generated.")
        print()
        return

    print("Per-stage draw.io files exported:")
    for path in exported_paths:
        print(f"  - {path}")
    print()


def _print_base_findings(base_violation_strs: list[str], aggregated_risk_strs: list[str]) -> None:
    if base_violation_strs:
        print("\nScenario-level structural findings:")
        for violation in base_violation_strs:
            print(f"  - {violation}")
    else:
        print("\nScenario-level structural findings: none")

    if aggregated_risk_strs:
        print("Aggregated propagation risks (all steps):")
        for risk in aggregated_risk_strs:
            print(f"  - {risk}")
    else:
        print("Aggregated propagation risks: none")


def _print_state_rows(states) -> None:
    for state in states:
        if state.stage == "Feedback":
            continue
        print(f"\n[{state.stage}] Step {state.step_index}: {state.action}")
        if state.violations:
            print("  Structural findings: see scenario-level summary")
        else:
            print("  No structural violations")

        if state.risks:
            print("  Delta risks (this step):")
            for risk in state.risks:
                print(f"    + {risk}")
        else:
            print("  No propagation risks")


def _emit_propagation_log(states, output_dir: Path, scenario_name: str, has_custom_scenario: bool) -> None:
    print("\n" + "=" * 80)
    log_path = output_dir / f"{_scenario_stem(scenario_name, has_custom_scenario)}_log.txt"
    propagation_events = log_propagation_events(
        states,
        output_file=str(log_path),
    )
    print_propagation_summary(propagation_events, log_path=str(log_path))


def main() -> None:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    parser = _build_parser()
    args = parser.parse_args()

    if args.list_scenarios:
        _print_available_scenarios()
        return

    # Fast path: export provided XML model to PNG without running simulation.
    if (
        args.export_model_png
        and not args.scenario
        and args.export_drawio is None
        and args.export_png is None
        and args.cycles == 1
        and not args.no_feedback
    ):
        _maybe_export_model_png(args.export_model_png)
        return

    try:
        system, scenario_name = _load_system(args.scenario)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    base_violation_strs, static_risk_strs = build_analysis_snapshot(system)

    _print_system_summary(system, scenario_name)
    _maybe_export_model_png(args.export_model_png)

    print("=== Model 2.0 Colored Petri Net Simulation with Analysis ===")
    states = run_cpn_cycles(
        system,
        development_cycles=max(1, args.cycles),
        feedback=not args.no_feedback,
        base_violation_strs=base_violation_strs,
    )

    # Aggregate per-step delta risks from all states for visualization.
    # These are marking-based and already reflect downstream receiver filtering.
    aggregated_risk_strs = exclude_feedback_risks(aggregate_risk_strings(states))

    # Prepend initialization-time risks from static analysis so they appear
    # colored in stage-0 diagrams before the first CPN step fires.
    # .Initialize actions are never fired in CPN, so their risks must come
    # from the structural analysis of the initial arc attributes.
    init_risk_strs = [r for r in static_risk_strs if ".Initialize/" in r]
    if init_risk_strs:
        aggregated_risk_strs = init_risk_strs + aggregated_risk_strs

    _print_base_findings(base_violation_strs, aggregated_risk_strs)
    _print_state_rows(states)
    drawio_path = _maybe_export_drawio(system, scenario_name, args.export_drawio, aggregated_risk_strs)
    _maybe_export_scenario_png(system, scenario_name, args.export_png, drawio_path, aggregated_risk_strs)
    _maybe_export_drawio_per_stage(
        system=system,
        scenario_name=scenario_name,
        export_drawio_per_stage_arg=args.export_drawio_per_stage,
        base_risk_strs=aggregated_risk_strs,
        states=states,
        development_cycles=max(1, args.cycles),
        feedback=not args.no_feedback,
    )
    _maybe_export_gif(system, scenario_name, states, args.export_gif)
    _emit_propagation_log(states, output_dir, scenario_name, args.scenario is not None)


if __name__ == "__main__":
    main()
