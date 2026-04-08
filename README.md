# ASPLOSER Framework

ASPLOSER is a runnable Model 2.0 framework for analyzing AI system security propagation with subject-action-object-arc semantics.

It includes:

- A Model 2.0 object-arc Petri net view:
	- round nodes as subjects
	- rectangular nodes as actions
	- arcs as objects (single arc type)
- Attribute-based security dimensions (confidentiality, correctness, continuity, credibility)
- Colored execution with level propagation and stage ordering (M/A/P/D/O/F)
- Initialize-phase static assignment for object-arc attributes, followed by semantic propagation
- Structural constraint checks and propagation-risk analysis
- Scenario-driven simulation via YAML overrides
- Diagram export and propagation logs under `output/`

## Repository Structure

- `main.py`: CLI entrypoint
- `backend/`: core framework implementation
- `scripts/scenarios/*.yaml`: predefined scenarios
- `docs/`: framework and scenario documentation
- `output/`: generated logs and diagram artifacts

## Quick Start

```bash
python3 main.py --list-scenarios
python3 main.py --scenario scripts/scenarios/corporations.yaml --no-feedback --cycles 1
python3 main.py --scenario scripts/scenarios/experienced-independent-developers-and-large-opensource-community.yaml --no-feedback --cycles 1 --export-drawio
python3 main.py --scenario scripts/scenarios/corporations.yaml --cycles 2 --export-drawio-per-stage
```

## Documentation

- Framework overview: `docs/README_framework.md`
- Detailed model and rationale: `docs/asploser.md`
- Scenario guides: `scripts/scenarios/corporations.md`, `scripts/scenarios/inexperienced-users-and-insecure-community.md`, `scripts/scenarios/experienced-independent-developers-and-large-opensource-community.md`, `scripts/scenarios/solarwinds-orion-supply-chain-compromise.md`, `scripts/scenarios/log4shell-dependency-exploit-wave.md`

## License

This project is licensed under the GNU General Public License v3.0.
See `LICENSE` for details.
