# Scenario 1: Private Mobile Single-User Pipeline

## Composition Note

This document describes the composed runtime state after applying `scenario1.yaml` on top of the default system.

The scenario keeps a mostly trusted private pipeline and introduces limited continuity degradation for runtime interaction.

## Overview

Scenario 1 models a private deployment where most subjects are trusted and most object channels remain confidential.

The main non-high behavior is continuity at selected deployment/operation edges.

### Node

Overrides and inferred highlights:

- PreprocessingModule credibility: Trusted
- InferenceModule credibility: Trusted
- PostprocessingModule credibility: Trusted
- User credibility: Trusted
- Maintainer credibility: Trusted
- DataWorker credibility: Trusted
- OperatingEnvironment continuity: **MixedContinuity**

Object-side highlights:

- InputQuery continuity: **MixedContinuity**
- InputToken continuity: **MixedContinuity**
- OutputToken continuity: **MixedContinuity**
- OutputMaterialized continuity: **MixedContinuity**

### Edge

Key overridden edges:

- 9.Assemble (Maintainer -> IntelligentSystem, Act): continuity **MixedContinuity**
- 10.Propose (User -> InputQuery, Act): continuity **MixedContinuity**
- 11.Pre-Process (InputQuery -> PreprocessingModule, ActedOnBy): continuity **MixedContinuity**
- 11.Pre-Process (PreprocessingModule -> InputToken, Act): continuity **MixedContinuity**
- 12.Inference (InputToken -> InferenceModule, ActedOnBy): continuity **MixedContinuity**
- 12.Inference (InferenceModule -> OutputToken, Act): continuity **MixedContinuity**
- 13.Post-Process (OutputToken -> PostprocessingModule, ActedOnBy): continuity **MixedContinuity**
- 13.Post-Process (PostprocessingModule -> OutputMaterialized, Act): continuity **MixedContinuity**
- R1.Respond (OutputMaterialized -> User, Respond): continuity **MixedContinuity**
- R2.Respond (OutputMaterialized -> OperatingEnvironment, Respond): continuity **MixedContinuity**
- R3.Respond (OperatingEnvironment -> IntelligentSystem, Respond): continuity **MixedContinuity**

## Usage

```bash
python3 main.py --scenario scenario1.yaml --no-feedback --cycles 1
```