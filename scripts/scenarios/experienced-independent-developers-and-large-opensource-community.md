# Scenario 3: Experienced Independent Developers And Large Open Source Community

## Composition Note

This document describes the composed runtime state after applying `experienced-independent-developers-and-large-opensource-community.yaml` on top of the default system.

This scenario models a mature open ecosystem led by experienced independent developers and supported by large open-source communities.

## Overview

Scenario 3 represents strong engineering competence and broad peer review, where correctness and continuity remain high while confidentiality is intentionally lower for public artifacts.

### Node

Overrides and inferred highlights:

- AppDevelopers credibility: Trusted
- DataWorkers credibility: Trusted
- Maintainers credibility: Trusted
- OutsideEnv credibility: **MixedCredibility**
- OutsideEnv correctness: Correct
- OutsideEnv continuity: **MixedContinuity**
- A3.Download confidentiality: **NonConfidential**
- A3.Download correctness: Correct
- D2.Delopy continuity: **MixedContinuity**
- M6.Download confidentiality: **NonConfidential**
- M6.Download correctness: Correct
- M6.Download continuity: Continuous
- O4.Postprocess confidentiality: **NonConfidential**
- O4.Postprocess correctness: Correct
- O4.Postprocess continuity: Continuous
- P2.Download confidentiality: **NonConfidential**
- P2.Download correctness: Correct
- P2.Download continuity: Continuous

### Edge

No edge overrides.

## Usage

```bash
python3 main.py --scenario scripts/scenarios/experienced-independent-developers-and-large-opensource-community.yaml --no-feedback --cycles 1
```

