# Scenario 5: Disaster Recovery Bootstrap

## Composition Note

This document describes the composed runtime state after applying `scenario5.yaml` on top of the default system.

This scenario models post-incident bootstrap behavior where initialize-phase trust on edges is globally reduced until re-attestation.

## Overview

Scenario 5 applies broad non-high initialize-edge defaults and introduces a targeted deployment discontinuity to represent recovery-mode risk posture.

### Node

No node overrides.

### Edge

- Default initialize edge attributes: confidentiality **NonConfidential**, correctness **MixedCorrectness**, continuity **MixedContinuity**

Key overridden edges:

- D2.Delopy (ModelAppAndDepI -> InferenceModule): continuity **Discontinuous**

## Usage

```bash
python3 main.py --scenario scenario5.yaml --no-feedback --cycles 1
```

