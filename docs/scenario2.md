# Scenario 2: Enterprise Cloud Multi-Tenant Pipeline

## Composition Note

This document describes the composed runtime state after applying `scenario2.yaml` on top of the default system.

Scenario 2 emphasizes public supply-chain channels and mixed reliability in enterprise cloud deployment.

## Overview

Scenario 2 introduces non-confidential channels and mixed correctness/continuity on key model, dependency, and deployment paths.

### Node

Overrides and inferred highlights:

- Maintainer continuity: **MixedContinuity**
- OperatingEnvironment correctness: **MixedCorrectness**
- OperatingEnvironment continuity: **MixedContinuity**

Object-side highlights:

- ModelHub confidentiality: **NonConfidential**
- ModelHub correctness: **MixedCorrectness**
- AppHub confidentiality: **NonConfidential**
- DependencyHub confidentiality: **NonConfidential**
- DependencyHub correctness: **MixedCorrectness**

### Edge

Key overridden edges:

- 4.Download (ModelHub -> Maintainer, ActedOnBy): confidentiality **NonConfidential**, correctness **MixedCorrectness**
- 8.Download (DependencyHub -> Maintainer, ActedOnBy): confidentiality **NonConfidential**, correctness **MixedCorrectness**
- 9.Assemble (Maintainer -> IntelligentSystem, Act): continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario scenario2.yaml --no-feedback --cycles 1
```