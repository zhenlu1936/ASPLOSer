---
name: asploser-framework
description: "Use when modifying the ASPLOSER framework, adding or refining scenarios, updating framework documentation, improving propagation analysis, refining exported diagrams, or validating output conventions and CLI smoke tests."
---

# ASPLOSER Framework Skill

## Purpose

Use this skill for framework code changes, scenario updates, propagation/logging behavior, diagram export behavior, and framework documentation maintenance.

## Project Context

- Entrypoint: `python3 main.py`
- Core package: `backend/`
- Primary specification: `asploser.md`
- Scenario files: `scenario*.yaml`
- Scenario docs: `docs/scenario*.md`
- Generated artifacts: `output/`

## Core Rules

### 1. Keep docs and behavior aligned

- Treat `asploser.md` as the semantic/spec reference.
- Do not leave silent mismatch between code and documentation.
- Scenario docs must match current runtime behavior and output paths.

### 2. Reduce redundancy

- Prefer small reusable helpers over repeated inline logic.
- Consolidate duplicated parsing, rendering, routing, and formatting paths.
- Remove dead code after refactors.

### 3. Reduce coupling

- Depend on stable shared contracts, not peer module internals.
- Prefer one-way dependencies between modules and avoid circular imports.
- If two modules share the same data shape, define it once in a neutral module.
- Keep public APIs stable while reorganizing internals.

### 4. Testing policy

- Use lightweight smoke tests through the CLI or inline Python commands.
- Do not create dedicated test files unless explicitly requested.

### 5. Output location policy

- Keep generated artifacts under `output/`.
- Log path: `output/<scenario>_propagation_log.txt`
- Diagram markdown: `output/<scenario>_pic.md`
- Diagram image: `output/<scenario>_pic.svg`

### 6. Simulation and log readability

- Execution steps are 1-based (`Step 1`, not `Step 0`).
- Propagation logs must include all execution events.
- Multi-cycle logs must include cycle context (`Cycle N`) on event lines and per-cycle summaries.

## Scenario Conventions

### Base schema

Scenario YAML files are override-based and should extend:

```yaml
base: default
```

Supported keys:

- `node_overrides`
- `edge_default_attributes`
- `edge_pair_omissions`
- `edge_overrides`
- `dependency_overrides`

### Edge-pair omissions

Use `edge_pair_omissions` to remove operation pairs from the default graph.

Example:

```yaml
edge_pair_omissions:
  - name: "6.Upload"
  - name: "9.Assemble"
    source: Maintainer
    target: IntelligentSystem
    types: ["Act"]
```

Interpretation:

- `name` is required
- `types` defaults to `Act` + `ActedOnBy`
- omissions are applied before `edge_overrides`

### Inference rule

The following subjects infer correctness and continuity from dependencies:

- `IntelligentSystem <= Model + Application + Dependency`
- `PreprocessingModule <= Application + Dependency`
- `InferenceModule <= Model + Application + Dependency`
- `PostprocessingModule <= Application + Dependency`

Credibility remains scenario-designated.

### Scenario doc format

All scenario docs (`docs/scenario*.md`) should use the same section schema and order:

1. `## Composition Note`
2. `## Overview`
3. `### Node`
4. `### Edge`
5. `## Usage`

In `Node` and `Edge` blocks, every non-high security value should be bold:

- Non-high credibility examples: `Untrusted`, `MixedCredibility`, `Mixed`
- Non-high correctness examples: `Incorrect`, `MixedCorrectness`
- Non-high continuity examples: `Discontinuous`, `MixedContinuity`
- Non-high confidentiality examples: `NonConfidential`, `MixedConfidentiality`, `Public`

## Visualization Conventions

- Keep the exported picture easy to understand, not merely complete.
- Prefer layered structure similar to `model4.0.png`.
- Use duplicated role cards when that improves readability.
- Reduce twisted edges by pruning non-essential visual connectors.
- Preserve semantic intent such as:
  - upper Users card for `R4` to `R7`
  - lower Users card for `10.Propose` and `R1.Respond`
- The picture generator may simplify visualization edges, but must not alter the underlying system model.

## Validation Checklist

After framework changes, run this compact smoke suite:

1. Scenario discovery

```bash
python3 main.py --list-scenarios
```

2. Clean baseline

```bash
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 1
```

3. Adversarial propagation scenario

```bash
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1
```

4. Diagram export

```bash
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1 --export-picture
```

5. Multi-cycle check

```bash
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 3
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 2
```

6. Cycle-aware log sanity check

```bash
grep '^Cycle' output/scenario1_propagation_log.txt | head -5
sed -n '1,40p' output/scenario3_propagation_log.txt
```