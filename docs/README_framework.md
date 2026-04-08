# ASPLOSER Framework Overview (Model 2.0)

ASPLOSER is a runnable framework for analyzing AI system security propagation using a Model 2.0 Colored Petri Net (CPN).

## What The Framework Implements

- Node-to-place mapping for subjects and objects
- Operation-to-transition mapping for lifecycle actions
- Color sets derived from security attributes:
  - subject token colors: credibility, correctness, continuity
  - object token colors: confidentiality, correctness, continuity
  - edge colors: confidentiality, correctness, continuity
- Stage-ordered transition firing across:
  - Development
  - Deployment
  - Operation
  - Feedback (optional)
- Structural validation:
  - component upper-bound rule
  - dependency upper-bound rule
  - inferred-attribute constraints for core agents
- Propagation-risk reporting and cycle-aware event logs

## Core Modules

- `backend/model.py`: unified Model 2.0 data model (core enums/schema plus subject/action/object-arc projection)
- `backend/instance.py`: default node/edge/dependency instance and inferred subject attribute setup
- `backend/simulator.py`: CPN execution engine (`run_cpn_cycles`)
- `backend/analysis.py`: structural checks, propagation risks, and log generation
- `backend/scenario_loader.py`: scenario loading and override application
- `backend/visualization.py`: draw.io and PNG propagation export
- `main.py`: CLI entrypoint

## CLI Usage

```bash
python3 main.py --list-scenarios
python3 main.py --scenario scripts/scenarios/corporations.yaml --no-feedback --cycles 1
python3 main.py --scenario scripts/scenarios/inexperienced-users-and-insecure-community.yaml --no-feedback --cycles 1
python3 main.py --scenario scripts/scenarios/experienced-independent-developers-and-large-opensource-community.yaml --no-feedback --cycles 1 --export-drawio
python3 main.py --scenario scripts/scenarios/log4shell-dependency-exploit-wave.yaml --no-feedback --cycles 1 --export-drawio
python3 main.py --scenario scripts/scenarios/corporations.yaml --cycles 2 --export-drawio-per-stage
python3 main.py --export-model-png
python3 main.py --scenario scripts/scenarios/corporations.yaml --no-feedback --cycles 1 --export-drawio --export-png
```

PNG export note:

- XML-to-PNG export requires draw.io CLI in PATH (`drawio`, `draw.io`, or `diagrams`).

## Scenario Override Schema

Supported YAML keys:

- `subject_overrides`
- `action_overrides`
- `object_initialization_overrides`

Schema intent:

- `subject_overrides` applies to round subject nodes only.
- `action_overrides` applies to all object arcs that carry the named action.
- `object_initialization_overrides` is limited to initialize-time `P` objects and should be used only when an initialization object differs from the action-wide default.

Initialize rule:

- Static edge attributes are assigned only in the initialize phase (before cycle execution).
- After initialization, edge attributes evolve through action firing semantics in the simulator.

## Output Artifacts

- propagation log: `output/<scenario>_log.txt`
- diagram draw.io: `output/<scenario>_pic.drawio`
- dimension-specific draw.io files:
  - `output/<scenario>_pic_confidentiality.drawio`
  - `output/<scenario>_pic_integrity.drawio`
  - `output/<scenario>_pic_availability.drawio`
- per-cycle stage draw.io set (5 files each cycle):
  - `output/<scenario>_pic_cycle<k>_stage0_initial.drawio`
  - `output/<scenario>_pic_cycle<k>_stage1_development.drawio`
  - `output/<scenario>_pic_cycle<k>_stage2_deployment.drawio`
  - `output/<scenario>_pic_cycle<k>_stage3_operation.drawio`
  - `output/<scenario>_pic_cycle<k>_stage4_feedback.drawio`
- diagram PNG from scenario draw.io: `output/<scenario>_pic.png`
- dimension-specific PNG files:
  - `output/<scenario>_pic_confidentiality.png`
  - `output/<scenario>_pic_integrity.png`
  - `output/<scenario>_pic_availability.png`
- diagram PNG from provided model XML: `output/model.png`

Per-stage draw.io export note:

- Use `--export-drawio-per-stage` to generate five draw.io files for each cycle.
- Optional argument sets output directory, for example:
  - `python3 main.py --scenario scripts/scenarios/corporations.yaml --cycles 1 --export-drawio-per-stage output`

## Visualization Rules

- Neutral action boxes do not keep template-only emphasis colors; they are unfilled unless colored by current rules.
- Initialize action boxes are always green entry points.
- Propagated risk colors:
  - high: red
  - medium: yellow
- Assigned risk colors:
  - high: purple
  - medium: blue
- Subject coloring is separate from object-arc label coloring and only escalates assigned subjects to propagated red when severity rises above the assigned baseline.
- Feedback boxes follow the same neutral-or-risk coloring rule as other action boxes.
- Dimension-specific exports are the primary way to inspect confidentiality, integrity, and availability views independently.

## Extension Guidance

- Keep model behavior aligned with `docs/asploser.md`
- Prefer framework-level refactors over scenario-specific patches
- Preserve cycle-aware logging and stage ordering when changing execution behavior

## Picture Alignment Note

- Treat `docs/asploser.md` as the normative source for runtime naming and semantics.
- Treat `docs/model.drawio` and generated files in `output/` as visualization artifacts that may use different display labels.
- Do not hardcode policy rules to specific picture-only action IDs.
- Scenario docs are generated from YAML inputs under `scripts/scenarios/`; copies under `docs/scenarios/` should not diverge from the active framework behavior.