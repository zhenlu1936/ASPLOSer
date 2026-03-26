# Workspace Instructions

- For tasks that modify the ASPLOSER framework, scenario files, scenario documentation, propagation analysis, diagram export, or validation flows, load and follow the `asploser-framework` skill before making changes.
- For tasks that create, update, review, or debug customization files such as `SKILL.md`, `copilot-instructions.md`, `AGENTS.md`, `*.instructions.md`, `*.prompt.md`, or `*.agent.md`, load and follow the `agent-customization` skill first.
- Keep framework behavior aligned with `asploser.md` and the scenario docs.
- Prefer framework-level fixes and redundancy reduction over scenario-specific patches.
- Do not create dedicated test files unless explicitly requested; prefer CLI smoke tests and inline validation.
- Keep generated artifacts under `output/`.