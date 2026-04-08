# Scenario 4: Foundation Model Release Pipeline Compromise

## Composition Note

This document describes the composed runtime state after applying `solarwinds-orion-supply-chain-compromise.yaml` on top of the default system.

This scenario models an AI release-pipeline compromise in which trusted model, application, and dependency distribution channels publish tainted artifacts that appear legitimate to downstream deployment teams.

## Overview

Scenario 4 focuses on AI release-pipeline trust collapse: model and application artifacts look authentic but carry downgraded confidentiality, correctness, and continuity that propagate into deployed inference services.

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
- A2.Upload confidentiality: **NonConfidential**
- A2.Upload correctness: **MixedCorrectness**
- A2.Upload continuity: **MixedContinuity**
- A3.Download confidentiality: **NonConfidential**
- A3.Download correctness: **MixedCorrectness**
- A3.Download continuity: **MixedContinuity**
- D2.Delopy confidentiality: **NonConfidential**
- D2.Delopy correctness: **MixedCorrectness**
- D2.Delopy continuity: **Discontinuous**
- M6.Download confidentiality: **NonConfidential**
- M6.Download correctness: **MixedCorrectness**
- M6.Download continuity: **Discontinuous**
- O4.Postprocess confidentiality: **NonConfidential**
- O4.Postprocess correctness: **MixedCorrectness**
- O4.Postprocess continuity: **MixedContinuity**
- P2.Download confidentiality: **NonConfidential**
- P2.Download correctness: **MixedCorrectness**

### Edge

No edge overrides.

## Usage

```bash
python3 main.py --scenario scripts/scenarios/solarwinds-orion-supply-chain-compromise.yaml --no-feedback --cycles 1
```

