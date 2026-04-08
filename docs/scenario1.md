# Scenario 1: Regulated Private Assistant

## Composition Note

This document describes the composed runtime state after applying `scenario1.yaml` on top of the default system.

This scenario represents a regulated enterprise assistant deployed in a private environment with trusted operators and controlled releases.

## Overview

Scenario 1 models a conservative production baseline where confidentiality and correctness are generally high, while runtime continuity may occasionally degrade due to network and service dependencies.

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
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 1
```

