"""ASPLOSER Model 2.0 framework package."""

from .instance import build_default_system
from .analysis import (
    build_analysis_snapshot,
    evaluate_risks_for_marking_delta,
    log_propagation_events,
    print_propagation_summary,
    PropagationEvent,
)
from .execution import ExecutionState
from .model import project_system_to_model2, ObjectArcPetriNet2
from .propagation import SECURITY_DIMENSIONS, aggregate_risk_strings, exclude_feedback_risks
from .scenario_loader import get_available_scenarios, load_scenario_from_file
from .simulator import run_cpn_cycles
from .visualization import (
    export_drawio_xml_to_png,
    export_propagation_gif_per_dimension,
    export_reference_model_png,
    export_template_propagation_drawio_per_dimension,
    export_template_propagation_drawio_per_stage,
    export_template_propagation_drawio,
)

__all__ = [
    "build_default_system",
    "build_analysis_snapshot",
    "evaluate_risks_for_marking_delta",
    "project_system_to_model2",
    "ObjectArcPetriNet2",
    "SECURITY_DIMENSIONS",
    "aggregate_risk_strings",
    "exclude_feedback_risks",
    "run_cpn_cycles",
    "ExecutionState",
    "load_scenario_from_file",
    "get_available_scenarios",
    "log_propagation_events",
    "print_propagation_summary",
    "PropagationEvent",
    "export_drawio_xml_to_png",
    "export_propagation_gif_per_dimension",
    "export_reference_model_png",
    "export_template_propagation_drawio_per_dimension",
    "export_template_propagation_drawio_per_stage",
    "export_template_propagation_drawio",
]
