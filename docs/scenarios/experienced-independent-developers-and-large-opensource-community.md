# Scenario 3: Experienced Independent Developers And Large Open Source Community

## Composition Note

This document describes the composed runtime state after applying `experienced-independent-developers-and-large-opensource-community.yaml` on top of the default system.

This scenario models a mature open ecosystem led by experienced independent developers and supported by large open-source communities.

## Overview

Scenario 3 represents strong engineering competence and broad peer review, where correctness and continuity remain high while confidentiality is intentionally lower for public artifacts.

### Node

Overrides and inferred highlights:

- AppDevelopers credibility: Trusted
- AppUploadedO confidentiality: **NonConfidential**
- AppUploadedO correctness: Correct
- DataWorkers credibility: Trusted
- DependenciesUploadedO confidentiality: **NonConfidential**
- DependenciesUploadedO correctness: Correct
- Maintainers credibility: Trusted
- ModelUploadedO confidentiality: **NonConfidential**
- ModelUploadedO correctness: Correct
- OutsideEnv credibility: **MixedCredibility**
- OutsideEnv correctness: Correct
- OutsideEnv continuity: **MixedContinuity**

### Edge

Key overridden edges:

- M6.Download (ModelDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness Correct, continuity Continuous
- P2.Download (DependenciesDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness Correct, continuity Continuous
- D2.Delopy (ModelAppAndDepI -> InferenceModule): continuity **MixedContinuity**
- O4.Postprocess (OutputI -> Users): confidentiality **NonConfidential**, correctness Correct, continuity Continuous

## Usage

```bash
python3 main.py --scenario docs/scenarios/experienced-independent-developers-and-large-opensource-community.yaml --no-feedback --cycles 1
```

