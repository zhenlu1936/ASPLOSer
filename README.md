# ASPLOSER Framework

ASPLOSER is a runnable framework for modeling and simulating AI system security propagation risks.

It includes:

- A formal graph model of subjects and objects with typed relationships
- Attribute-based security dimensions (confidentiality, correctness, continuity, credibility)
- Structural constraint checks and propagation-risk analysis
- Scenario-driven simulation via YAML overrides
- Diagram export and propagation logs under `output/`

## Repository Structure

- `main.py`: CLI entrypoint
- `backend/`: core framework implementation
- `scenario*.yaml`: predefined scenarios
- `docs/`: framework and scenario documentation
- `output/`: generated logs and diagram artifacts

## Quick Start

```bash
python3 main.py --list-scenarios
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 1
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1 --export-picture
```

## Documentation

- Framework overview: `docs/README_framework.md`
- Detailed model and rationale: `docs/asploser.md`
- Scenario guides: `docs/scenario1.md` to `docs/scenario4.md`

## License

This project is licensed under the GNU General Public License v3.0.
See `LICENSE` for details.
