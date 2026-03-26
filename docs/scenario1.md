# Scenario 1: Single-User Private Mobile Pipeline

## Composition Note

This document describes the composed system after applying the overrides from
`scenario1.yaml` to the default ASPLOSER graph.

The YAML file is not a standalone full graph definition. It extends the default
system with the override-based scenario schema described in
`README_framework.md`.

## Overview

A single end user owns private raw data and uses a private single-user development and deployment pipeline to build a personalized DNN application for local mobile inference.

- The roles DataWorker, ModelDeveloper, AppDeveloper, and Maintainer are all instantiated as distinct roles in the lifecycle, although in practice they may be played by the same person.

- ModelHub, AppHub, and DependencyHub are private repositories under the same single-user setting rather than public distribution platforms, so they are treated as Confidential, Correct, and Continuous.

- The pretrained model is also private within this scenario. The final intelligent system runs on a mobile device for the same user.

- Compared with the previous version, this is a more ideal setting: raw data is assumed to have been curated before preparation, the mobile OS and runtime stack are assumed benign and well maintained, and deployment artifacts are assumed properly packaged and verified.

- Mobile execution still occurs on an edge device and may still be affected by practical runtime interruption such as battery, scheduling, or transient resource pressure, so a small number of continuity-related attributes remain mixed.

### Node

nodes := {

- (Agent/IntelligentSystem, {credibility: Trusted, correctness: Correct, continuity: **MixedContinuity**}),
  (Agent/PreprocessingModule, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Agent/InferenceModule, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Agent/PostprocessingModule, {credibility: Trusted, correctness: Correct, continuity: Continuous}),

- (Participant/User, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/ModelDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/AppDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/Maintainer, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/DataWorker, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/OperatingEnvironment, {credibility: Trusted, correctness: Correct, continuity: **MixedContinuity**}),

- (Source/ModelHub, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Source/AppHub, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Source/DependencyHub, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),

- (Asset/RawData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ProcessedData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ModelPretrained, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ModelTrained, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Model, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ApplicationProgrammed, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Application, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Dependency, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/InputQuery, {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  (Asset/InputToken, {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  (Asset/OutputToken, {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  (Asset/OutputMaterialized, {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**})

}

### Edge

edges := {

- ((RawData, DataWorker, ActedOnBy, "1.Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((DataWorker, ProcessedData, Act, "1.Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ProcessedData, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelPretrained, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelDeveloper, ModelTrained, Act, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelTrained, ModelDeveloper, ActedOnBy, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelDeveloper, ModelHub, Act, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelHub, Maintainer, ActedOnBy, "4.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Maintainer, Model, Act, "4.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((AppDeveloper, ApplicationProgrammed, Act, "5.Program"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ApplicationProgrammed, AppDeveloper, ActedOnBy, "6.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((AppDeveloper, AppHub, Act, "6.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((AppHub, Maintainer, ActedOnBy, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Maintainer, Application, Act, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((DependencyHub, Maintainer, ActedOnBy, "8.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Maintainer, Dependency, Act, "8.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Model, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Application, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Dependency, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((Maintainer, IntelligentSystem, Act, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((User, InputQuery, Act, "10.Propose"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((InputQuery, PreprocessingModule, ActedOnBy, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((PreprocessingModule, InputToken, Act, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((InputToken, InferenceModule, ActedOnBy, "12.Inference"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((InferenceModule, OutputToken, Act, "12.Inference"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((OutputToken, PostprocessingModule, ActedOnBy, "13.Post-Process"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((PostprocessingModule, OutputMaterialized, Act, "13.Post-Process"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((PreprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((InferenceModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((PostprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((IntelligentSystem, OperatingEnvironment, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((OutputMaterialized, User, Respond, "R1.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((OutputMaterialized, OperatingEnvironment, Respond, "R2.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((OperatingEnvironment, IntelligentSystem, Respond, "R3.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((User, DataWorker, Respond, "R4.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((User, ModelDeveloper, Respond, "R5.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((User, AppDeveloper, Respond, "R6.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((User, Maintainer, Respond, "R7.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous})

}

## Usage

Run scenario1:

```bash
python3 main.py --scenario scenario1.yaml --cycles 1 --no-feedback
```