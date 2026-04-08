---
name: asploser-framework
description: "Use when modifying the ASPLOSER framework, adding or refining scenarios, updating framework documentation, improving propagation analysis, refining exported diagrams, or validating output conventions and CLI smoke tests."
---

# ASPLOSER Framework Skill

## Purpose

Use this skill for ASPLOSER Model 2.0 framework code, scenarios, propagation behavior, visualization export, and framework docs.

## Project Context

- Entrypoint: `python3 main.py`
- Core package: `backend/`
- Primary specification: `docs/asploser.md`
- Scenario files: `scenario*.yaml`
- Scenario docs: `docs/scenario*.md`
- Generated artifacts: `output/`

## Core Rules

1. `docs/asploser.md` is authoritative. Code, docs, and outputs must match it.
2. Enforce Model 2.0 semantics:
  - round nodes are subjects
  - rectangular nodes are actions
  - arcs are objects (single arc type)
  - no object nodes and no extra arc classes
  - static object-arc attribute assignment is initialize-only; post-initialize updates follow firing semantics
3. Prefer framework-level fixes. Remove duplication and dead code.
4. Keep dependencies clean: shared contracts, no circular imports.
5. No dedicated test files unless explicitly requested. Use CLI smoke tests.
6. Keep generated artifacts only in `output/`:
  - `output/<scenario>_propagation_log.txt`
  - `output/<scenario>_pic.md`
  - `output/<scenario>_pic.svg`
7. Log quality is mandatory:
  - 1-based step labels
  - full execution events
  - cycle-aware event lines and per-cycle summaries
8. No legacy compatibility:
  - no alias keys, fallback parsing, or deprecated shims
  - remove replaced schema/API forms in the same change
  - fail fast on legacy inputs with clear errors
9. Naming must be concise and final:
  - no temporary/migration names (`new_*`, `old_*`, `tmp*`, `legacy_*`, `draft`, `final_final`)
  - no history-encoded names
  - use no-space identifiers for model names (`DataWorkers`, `O1.Input`, `PreprocessingModule`)
  - complete renames in one change

## Scenario Conventions

### Base schema

Scenario YAML files are override-based and should extend:

```yaml
base: default
```

Supported keys:

- `node_overrides`
- `initialize_edge_default_attributes`
- `edge_pair_omissions`
- `initialize_edge_overrides`
- `dependency_overrides`

Schema policy:

- Keys and field names must be concise and legacy-free.
- Do not add compatibility aliases for old scenario keys.

### Edge-pair omissions

Use `edge_pair_omissions` to remove operation pairs from the default graph.

Example:

```yaml
edge_pair_omissions:
  - name: "A2.Upload"
  - name: "D2.Delopy"
    source: Maintainers
    target: InferenceModule
    types: ["Act"]
```

Interpretation:

- `name` is required
- `types` is optional and only filters omission matches in the runtime implementation
- omissions are applied before `initialize_edge_overrides`

### Inference rule

These subjects infer correctness and continuity from dependencies:

- `IntelligentSystem <= Model + Application + Dependency`
- `PreprocessingModule <= Application + Dependency`
- `InferenceModule <= Model + Application + Dependency`
- `PostprocessingModule <= Application + Dependency`

Credibility remains scenario-designated.

### Scenario doc format

All scenario docs (`docs/scenario*.md`) must use this order:

1. `## Composition Note`
2. `## Overview`
3. `### Node`
4. `### Edge`
5. `## Usage`

In `Node` and `Edge`, every non-high security value must be bold:

- Non-high credibility examples: `Untrusted`, `MixedCredibility`, `Mixed`
- Non-high correctness examples: `Incorrect`, `MixedCorrectness`
- Non-high continuity examples: `Discontinuous`, `MixedContinuity`
- Non-high confidentiality examples: `NonConfidential`, `MixedConfidentiality`, `Public`

## Visualization Conventions

- Prioritize readability over raw completeness.
- Keep semantic behavior unchanged when simplifying visual edges.
- Treat the current model picture labels and structure as authoritative for visual naming and layout intent.
- Do not hardcode visualization guidance to legacy or outdated action IDs.

## Validation Checklist

After framework changes, run this smoke suite:

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

4. Initialize non-fully-trusted arcs scenario

```bash
python3 main.py --scenario scenario5.yaml --no-feedback --cycles 1
```

5. Diagram export

```bash
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1 --export-picture
```

6. Multi-cycle check

```bash
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 3
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 2
```

7. Cycle-aware log sanity check

```bash
grep '^Cycle' output/scenario1_propagation_log.txt | head -5
sed -n '1,40p' output/scenario3_propagation_log.txt
```