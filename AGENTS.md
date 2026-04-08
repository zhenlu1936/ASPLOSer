# AGENTS Guide

This repository contains the ASPLOSER framework.

## Purpose

Use this file as the human-facing project guide for how agent work should be carried out in this workspace.

The authoritative machine-routed instructions live in:

- `.github/copilot-instructions.md`
- `.github/skills/asploser-framework/SKILL.md`

## When To Use The ASPLOSER Skill

Load and follow the `asploser-framework` skill when working on:

- framework code under `backend/`
- scenario files such as `scenario*.yaml`
- scenario documentation under `docs/`
- propagation analysis and validation behavior
- diagram export or visualization behavior
- CLI smoke-test and output conventions

## When To Use The Customization Skill

Load and follow the `agent-customization` skill when creating, updating, reviewing, or debugging customization files such as:

- `AGENTS.md`
- `copilot-instructions.md`
- `SKILL.md`
- `*.instructions.md`
- `*.prompt.md`
- `*.agent.md`

## Project Rules

- Keep framework behavior aligned with `asploser.md` and the scenario docs.
- Keep all model descriptions aligned with Model 2.0:
	round nodes = subjects, rectangular nodes = actions, arcs = objects.
- Prefer framework-level fixes over scenario-specific hacks.
- Reduce redundancy when touching parsing, routing, rendering, or validation logic.
- Do not create dedicated test files unless explicitly requested.
- Prefer CLI smoke tests and inline validation.
- Keep generated artifacts under `output/`.

## Expected Output Locations

- propagation logs: `output/<scenario>_log.txt`
- diagram draw.io: `output/<scenario>_pic.drawio`
- diagram png: `output/<scenario>_pic.png`
- model png: `output/model.png`

## Typical Validation Commands

```bash
python3 main.py --list-scenarios
python3 main.py --scenario scripts/scenarios/corporations.yaml --no-feedback --cycles 1
python3 main.py --scenario scripts/scenarios/inexperienced-users-and-insecure-community.yaml --no-feedback --cycles 1
python3 main.py --scenario scripts/scenarios/experienced-independent-developers-and-large-opensource-community.yaml --no-feedback --cycles 1 --export-drawio
python3 main.py --scenario scripts/scenarios/log4shell-dependency-exploit-wave.yaml --no-feedback --cycles 1 --export-drawio
python3 main.py --export-model-png
python3 main.py --scenario scripts/scenarios/corporations.yaml --no-feedback --cycles 1 --export-drawio --export-png
```

## Editing Style

- Keep changes focused and minimally invasive.
- Update documentation when behavior, schema, or outputs change.
- If a new capability is added, provide at least one example scenario or documented example.