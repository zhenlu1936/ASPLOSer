# Scenario 2: Inexperienced Users And Insecure Community

## Composition Note

This document describes the composed runtime state after applying `inexperienced-users-and-insecure-community.yaml` on top of the default system.

This scenario models an assistant exposed to inexperienced users and loosely governed community contributions with weak security hygiene.

## Overview

Scenario 2 emphasizes reduced trust, weaker artifact assurance, and discontinuous operations that can amplify confidentiality, correctness, and availability risks.

### Node

Overrides and inferred highlights:

- AppUploadedO confidentiality: **NonConfidential**
- AppUploadedO correctness: **MixedCorrectness**
- AppUploadedO continuity: **MixedContinuity**
- DependenciesUploadedO confidentiality: **NonConfidential**
- DependenciesUploadedO correctness: **MixedCorrectness**
- DependenciesUploadedO continuity: **MixedContinuity**
- Maintainers credibility: **MixedCredibility**
- Maintainers correctness: **MixedCorrectness**
- Maintainers continuity: **MixedContinuity**
- ModelUploadedO confidentiality: **NonConfidential**
- ModelUploadedO correctness: **MixedCorrectness**
- ModelUploadedO continuity: **MixedContinuity**
- OutsideEnv credibility: **Untrusted**
- OutsideEnv correctness: **MixedCorrectness**
- OutsideEnv continuity: **Discontinuous**
- PostprocessingModule credibility: **MixedCredibility**
- PreprocessingModule credibility: **MixedCredibility**
- Users credibility: **MixedCredibility**
- Users correctness: **MixedCorrectness**

### Edge

Key overridden edges:

- M6.Download (ModelDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- P2.Download (DependenciesDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- D2.Delopy (ModelAppAndDepI -> InferenceModule): correctness **MixedCorrectness**, continuity **Discontinuous**
- O4.Postprocess (OutputI -> Users): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario docs/scenarios/inexperienced-users-and-insecure-community.yaml --no-feedback --cycles 1
```

