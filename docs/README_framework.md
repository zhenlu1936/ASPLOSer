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
  - Inference
  - Response
  - Feedback (optional)
- Structural validation:
  - component upper-bound rule
  - dependency upper-bound rule
  - inferred-attribute constraints for core agents
- Propagation-risk reporting and cycle-aware event logs

## Core Modules

- `backend/model.py`: data model and enums for attributes and graph elements
- `backend/model.py`: Model 2.0 projection with subjects (round), actions (rectangular), and one-type object arcs
- `backend/instance.py`: default node/edge/dependency instance and inferred subject attribute setup
- `backend/simulator.py`: CPN execution engine (`run_cpn_cycles`)
- `backend/analysis.py`: structural checks, propagation risks, and log generation
- `backend/scenario_loader.py`: scenario loading and override application
- `backend/visualization.py`: holistic diagram export
- `main.py`: CLI entrypoint

## CLI Usage

```bash
python3 main.py --list-scenarios
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 1
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1 --export-picture
```

## Scenario Override Schema

Supported YAML keys:

- `node_overrides`
- `edge_default_attributes`
- `edge_pair_omissions`
- `edge_overrides`
- `dependency_overrides`

`edge_pair_omissions` removes operation edge pairs before edge overrides are applied.

Example:

```yaml
edge_pair_omissions:
  - name: "6.Upload"
  - name: "9.Assemble"
    source: Maintainer
    target: IntelligentSystem
    types: ["Act"]
```

Semantics:

- `name` is required
- `types` defaults to `Act` and `ActedOnBy`
- `source` and `target` are optional filters

## Output Artifacts

- propagation log: `output/<scenario>_propagation_log.txt`
- diagram markdown: `output/<scenario>_pic.md`
- diagram image: `output/<scenario>_pic.svg`

## Extension Guidance

- Keep model behavior aligned with `docs/asploser.md`
- Prefer framework-level refactors over scenario-specific patches
- Preserve cycle-aware logging and stage ordering when changing execution behavior