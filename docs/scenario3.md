# Scenario 3: Adversarial Supply Chain With Propagation Risks

## Composition Note

This document describes the composed runtime state after applying `scenario3.yaml` on top of the default system.

Scenario 3 is the adversarial reference case used for propagation-risk validation.

## Overview

Scenario 3 introduces untrusted participants, non-confidential channels, and discontinuous edges to trigger confidentiality and availability risks.

### Node

Overrides and inferred highlights:

- DataWorker credibility: **Untrusted**
- DataWorker correctness: **MixedCorrectness**
- DataWorker continuity: **MixedContinuity**
- AppDeveloper credibility: **Untrusted**
- AppDeveloper correctness: **MixedCorrectness**
- AppDeveloper continuity: **MixedContinuity**
- Maintainer credibility: **Untrusted**
- Maintainer correctness: **MixedCorrectness**
- Maintainer continuity: **Discontinuous**
- OperatingEnvironment credibility: **MixedCredibility**
- OperatingEnvironment correctness: **MixedCorrectness**
- OperatingEnvironment continuity: **MixedContinuity**

Object-side highlights:

- ModelHub confidentiality: **NonConfidential**
- ModelHub correctness: **MixedCorrectness**
- AppHub confidentiality: **NonConfidential**
- AppHub correctness: **MixedCorrectness**
- DependencyHub confidentiality: **NonConfidential**
- DependencyHub correctness: **MixedCorrectness**
- DependencyHub continuity: **MixedContinuity**

### Edge

Key overridden edges:

- 1.Process (DataWorker -> ProcessedData, Act): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**
- 4.Download (ModelHub -> Maintainer, ActedOnBy): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- 8.Download (Maintainer -> Dependency, Act): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**
- 9.Assemble (Maintainer -> IntelligentSystem, Act): correctness **MixedCorrectness**, continuity **Discontinuous**
- R1.Respond (OutputMaterialized -> User, Respond): confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **Discontinuous**

## Usage

```bash
python3 main.py --scenario scenario3.yaml --no-feedback --cycles 1
```

Expected result: propagation risks appear in `output/scenario3_propagation_log.txt`.