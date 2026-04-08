# Scenario 2: Hybrid Public Supply Chain

## Composition Note

This document describes the composed runtime state after applying `scenario2.yaml` on top of the default system.

This scenario captures an enterprise assistant that consumes model, app, and dependency artifacts from mixed-trust public registries.

## Overview

Scenario 2 models a mixed-trust release path where external artifacts can lower confidentiality, correctness, and continuity along the deployment chain.

### Node

Overrides and inferred highlights:

- AppUploadedO confidentiality: **NonConfidential**
- DependenciesUploadedO confidentiality: **NonConfidential**
- DependenciesUploadedO correctness: **MixedCorrectness**
- Maintainers continuity: **MixedContinuity**
- ModelUploadedO confidentiality: **NonConfidential**
- ModelUploadedO correctness: **MixedCorrectness**
- OutsideEnv credibility: Trusted
- OutsideEnv correctness: **MixedCorrectness**
- OutsideEnv continuity: **MixedContinuity**
- PostprocessingModule credibility: Trusted
- PreprocessingModule credibility: Trusted
- Users credibility: Trusted

### Edge

Key overridden edges:

- M6.Download (ModelDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**
- P2.Download (DependenciesDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**
- D2.Delopy (ModelAppAndDepI -> InferenceModule): continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario scenario2.yaml --no-feedback --cycles 1
```

