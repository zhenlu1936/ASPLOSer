# Scenario 4: SolarWinds Orion Supply-Chain Compromise

## Composition Note

This document describes the composed runtime state after applying `solarwinds-orion-supply-chain-compromise.yaml` on top of the default system.

This scenario is inspired by the 2020 SolarWinds Orion incident, where trusted software release channels were abused to deliver tainted updates.

## Overview

Scenario 4 focuses on release-pipeline trust collapse: artifacts and deployment pathways appear legitimate but carry downgraded confidentiality, correctness, and continuity that propagate across stages.

### Node

Overrides and inferred highlights:

- AppDevelopers credibility: **MixedCredibility**
- AppDevelopers correctness: **MixedCorrectness**
- Maintainers credibility: **MixedCredibility**
- Maintainers correctness: **MixedCorrectness**
- Maintainers continuity: **MixedContinuity**
- OutsideEnv credibility: **Untrusted**
- OutsideEnv correctness: **MixedCorrectness**
- OutsideEnv continuity: **MixedContinuity**
- AppUploadedO confidentiality: **NonConfidential**
- AppUploadedO correctness: **MixedCorrectness**
- AppUploadedO continuity: **MixedContinuity**
- ModelUploadedO confidentiality: **NonConfidential**
- ModelUploadedO correctness: **MixedCorrectness**
- DependenciesUploadedO confidentiality: **NonConfidential**
- DependenciesUploadedO correctness: **MixedCorrectness**

### Edge

Key overridden edges:

- A2.Upload (AppDevelopers -> AppProgrammedO): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**
- A3.Download (AppHub -> AppUploadedO): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**
- M6.Download (ModelDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- D2.Delopy (ModelAppAndDepI -> InferenceModule): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- O4.Postprocess (OutputI -> Users): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario docs/scenarios/solarwinds-orion-supply-chain-compromise.yaml --no-feedback --cycles 1
```
