from __future__ import annotations

import argparse
from pathlib import Path

from backend import (
    build_analysis_snapshot,
    build_default_system,
    export_holistic_picture,
    get_available_scenarios,
    load_scenario_from_file,
    log_propagation_events,
    print_propagation_summary,
    run_ssa_cycles,
)


def main() -> None:
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Run the ASPLOSER framework with scenario support")
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Path to scenario file (e.g., scenario1.yaml or scenario1.md)",
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
        "--export-picture",
        nargs="?",
        const="AUTO",
        type=str,
        default=None,
        help="Export holistic model picture (md + svg). Optional path overrides default <scenario>_pic.md",
    )
    args = parser.parse_args()

    if args.list_scenarios:
        scenarios = get_available_scenarios()
        print("Available scenarios:")
        for scenario in scenarios:
            print(f"  - {scenario}")
        return

    # Load scenario or use default
    if args.scenario:
        try:
            system = load_scenario_from_file(args.scenario)
            scenario_name = args.scenario
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
    else:
        system = build_default_system()
        scenario_name = "default (asploser)"

    print("=== ASPLOSER Framework ===")
    print(f"Scenario: {scenario_name}")
    print(f"Nodes: {len(system.graph.nodes)}")
    print(f"Edges: {len(system.graph.edges)}")
    print()

    if args.export_picture:
        custom_path = None if args.export_picture == "AUTO" else args.export_picture
        md_path, svg_path = export_holistic_picture(
            system,
            scenario_name=scenario_name,
            output_file=custom_path,
        )
        print(f"Holistic model markdown exported to: {md_path}")
        print(f"Holistic model image exported to: {svg_path}")
        print()

    print("=== Dynamic Simulation with Analysis ===")
    base_violation_strs, base_risk_strs = build_analysis_snapshot(system)
    states = run_ssa_cycles(
        system,
        development_cycles=max(1, args.cycles),
        feedback=not args.no_feedback,
        base_violation_strs=base_violation_strs,
        base_risk_strs=base_risk_strs,
    )

    for state in states:
        print(f"\n[{state.stage}] Step {state.step_index}: {state.action}")
        
        if state.violations:
            print("  Violations detected:")
            for violation in state.violations:
                print(f"    - {violation}")
        else:
            print("  No structural violations")
        
        if state.risks:
            print("  Security risks detected:")
            for risk in state.risks:
                print(f"    - {risk}")
        else:
            print("  No propagation risks")
    
    # Generate propagation log
    print("\n" + "="*80)
    log_path = output_dir / f"{Path(scenario_name).stem if args.scenario else 'default'}_propagation_log.txt"
    propagation_events = log_propagation_events(
        system,
        states,
        output_file=str(log_path),
    )
    print_propagation_summary(propagation_events, log_path=str(log_path))


if __name__ == "__main__":
    main()
