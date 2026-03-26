# ASPLOSER Framework

This repository provides a runnable implementation of the ASPLOSER framework based on `asploser.md`.

## Included

- Formal graph model with subject and object nodes and typed edges
- Attribute system for confidentiality, correctness, continuity, and credibility
- Default system instance aligned with the specified entities and edges
- Structural constraint checks:
  - component upper-bound rule
  - dependency upper-bound rule
- Propagation-risk analysis
- SSA execution-loop simulation covering development, deployment, inference, response, and feedback stages
- YAML scenario loading with override-based definitions to avoid duplicating the full graph specification
- Scenario support for omitting selected operation edge pairs

## Files

- `backend/model.py`: core schema and enums
- `backend/instance.py`: default system instance derived from the specification
- `backend/analysis.py`: objective computation and rule checks
- `backend/simulator.py`: SSA cycle simulation
- `backend/scenario_loader.py`: YAML scenario loading, overrides, and edge-pair omission support
- `main.py`: CLI entrypoint

## Run

```bash
python3 main.py
python3 main.py --cycles 2
python3 main.py --cycles 2 --no-feedback
python3 main.py --list-scenarios
python3 main.py --scenario scenario1.yaml
python3 main.py --scenario scenario2.yaml
python3 main.py --scenario scenario4.yaml
python3 main.py --scenario scenario3.yaml --export-picture
```

## Scenario YAML

Supported scenario keys:

- `node_overrides`: replace node attributes by name
- `edge_default_attributes`: apply a default attribute patch to all edges
- `edge_pair_omissions`: remove selected operation edge pairs before overrides are applied
- `edge_overrides`: patch matching edges after omissions
- `dependency_overrides`: replace dependency sets for inferred subjects

### `edge_pair_omissions`

Use this field when a scenario should remove an operation pair without redefining the entire graph.

```yaml
edge_pair_omissions:
  - name: "6.Upload"
  - name: "9.Assemble"
    source: Maintainer
    target: IntelligentSystem
    types: ["Act"]
```

Notes:

- `name` is required.
- `types` defaults to `["Act", "ActedOnBy"]`.
- `source` and `target` are optional filters.
- Omissions are applied before `edge_overrides`.

## Notes

- Objective and propagation calculations are intentionally explicit to keep the framework easy to inspect and extend.
- Default node and edge attributes can be adjusted in `backend/instance.py` to explore alternative security scenarios.