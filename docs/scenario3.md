# Scenario 3: Compromised Release Incident

## Composition Note

This document describes the composed runtime state after applying `scenario3.yaml` on top of the default system.

This scenario models a supply-chain compromise where untrusted contributors and tainted artifacts propagate risks across deployment and runtime.

## Overview

Scenario 3 emphasizes cascading confidentiality and availability risk propagation under degraded trust and discontinuous release operations.

### Node

Overrides and inferred highlights:

- AppDevelopers credibility: **Untrusted**
- AppDevelopers correctness: **MixedCorrectness**
- AppDevelopers continuity: **MixedContinuity**
- AppUploadedO confidentiality: **NonConfidential**
- AppUploadedO correctness: **MixedCorrectness**
- DataWorkers credibility: **Untrusted**
- DataWorkers correctness: **MixedCorrectness**
- DataWorkers continuity: **MixedContinuity**
- DependenciesUploadedO confidentiality: **NonConfidential**
- DependenciesUploadedO correctness: **MixedCorrectness**
- DependenciesUploadedO continuity: **MixedContinuity**
- Maintainers credibility: **Untrusted**
- Maintainers correctness: **MixedCorrectness**
- Maintainers continuity: **Discontinuous**
- ModelUploadedO confidentiality: **NonConfidential**
- ModelUploadedO correctness: **MixedCorrectness**
- OutsideEnv credibility: **MixedCredibility**
- OutsideEnv correctness: **MixedCorrectness**
- OutsideEnv continuity: **MixedContinuity**

### Edge

Key overridden edges:

- M2.Process (DataWorkers -> UnstructuredDataO): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**
- M6.Download (ModelDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- P2.Download (DependenciesDownloadedI -> Maintainers): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- D2.Delopy (ModelAppAndDepI -> InferenceModule): correctness **MixedCorrectness**, continuity **Discontinuous**
- O4.Postprocess (OutputI -> Users): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**

## Usage

```bash
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1
```

