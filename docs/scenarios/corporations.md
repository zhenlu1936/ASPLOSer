# Scenario 1: Corporate Governed Assistant

## Composition Note

This document describes the composed runtime state after applying `corporations.yaml` on top of the default system.

This scenario represents a corporation-operated assistant under formal governance, controlled releases, and managed platform operations.

## Overview

Scenario 1 models a corporate baseline with high trust among internal roles, strong correctness, and only limited continuity degradation caused by enterprise infrastructure dependencies.

### Node

Overrides and inferred highlights:

- DataWorkers credibility: Trusted
- InferenceModule credibility: Trusted
- Maintainers credibility: Trusted
- OutsideEnv credibility: Trusted
- OutsideEnv continuity: **MixedContinuity**
- PostprocessingModule credibility: Trusted
- PreprocessingModule credibility: Trusted
- Users credibility: Trusted

### Edge

Key overridden edges:

- D2.Delopy (ModelAppAndDepI -> InferenceModule): continuity **MixedContinuity**
- O1.Input (Users -> InputO): continuity **MixedContinuity**
- O4.Postprocess (OutputI -> Users): continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario docs/scenarios/corporations.yaml --no-feedback --cycles 1
```

