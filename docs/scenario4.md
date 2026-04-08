# Scenario 4: Emergency Offline Rollout

## Composition Note

This document describes the composed runtime state after applying `scenario4.yaml` on top of the default system.

This scenario models an emergency packaged rollout where selected upload and feedback loops are intentionally suspended.

## Overview

Scenario 4 focuses on continuity under constrained operations, with reduced interaction pathways and selective deployment-edge continuity degradation.

### Node

Overrides and inferred highlights:

- Maintainers credibility: Trusted
- OutsideEnv credibility: Trusted
- OutsideEnv continuity: **MixedContinuity**
- Users credibility: Trusted

### Edge

- Omitted operation edge pairs: A2.Upload; F1.Feedback (Users -> OutputFeedbackO); F1.Feedback (FeedbackI -> ModelDevelopers); F1.Feedback (FeedbackI -> AppDevelopers); F1.Feedback (FeedbackI -> DependencyDevelopers); F1.Feedback (FeedbackI -> Maintainers)

Key overridden edges:

- D2.Delopy (ModelAppAndDepI -> InferenceModule): continuity **MixedContinuity**
- O4.Postprocess (OutputMaterializedI -> OutsideEnv): continuity **MixedContinuity**
- O1.Input (OutsideEnv -> InputMaterializedO): continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario scenario4.yaml --no-feedback --cycles 1
```

