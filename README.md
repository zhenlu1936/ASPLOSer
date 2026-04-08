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
- `docs/scenarios/*.yaml`: predefined scenarios
- `docs/`: framework and scenario documentation
- `output/`: generated logs and diagram artifacts

## Quick Start

```bash
python3 main.py --list-scenarios
python3 main.py --scenario docs/scenarios/corporations.yaml --no-feedback --cycles 1
python3 main.py --scenario docs/scenarios/experienced-independent-developers-and-large-opensource-community.yaml --no-feedback --cycles 1 --export-picture
python3 main.py --scenario docs/scenarios/corporations.yaml --cycles 2 --export-drawio-per-stage
```

## Documentation

- Framework overview: `docs/README_framework.md`
- Detailed model and rationale: `docs/asploser.md`
- Scenario guides: `docs/scenarios/corporations.md`, `docs/scenarios/inexperienced-users-and-insecure-community.md`, `docs/scenarios/experienced-independent-developers-and-large-opensource-community.md`, `docs/scenarios/solarwinds-orion-supply-chain-compromise.md`, `docs/scenarios/log4shell-dependency-exploit-wave.md`

## License

This project is licensed under the GNU General Public License v3.0.
See `LICENSE` for details.
