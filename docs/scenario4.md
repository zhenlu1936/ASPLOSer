# Scenario 4: Static Packaged Deployment Without Feedback Loop

## Composition Note

This document describes the composed system after applying the overrides from
`scenario4.yaml` to the default ASPLOSER graph.

The YAML file is not a standalone full graph definition. It extends the default
system with the override-based scenario schema described in
`README_framework.md`.

## Overview

Scenario 4 models a packaged deployment variant where `6.Upload` is omitted and
feedback edges `R4` to `R7` are removed.

### Node

nodes := {

- (Agent/IntelligentSystem, {credibility: **MixedCredibility**, correctness: Correct, continuity: Continuous}),
  (Agent/PreprocessingModule, {credibility: **MixedCredibility**, correctness: Correct, continuity: Continuous}),
  (Agent/InferenceModule, {credibility: **MixedCredibility**, correctness: Correct, continuity: Continuous}),
  (Agent/PostprocessingModule, {credibility: **MixedCredibility**, correctness: Correct, continuity: Continuous}),

- (Participant/User, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/ModelDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/AppDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/Maintainer, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/DataWorker, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/OperatingEnvironment, {credibility: Trusted, correctness: Correct, continuity: **MixedContinuity**}),

- (Source/ModelHub, {confidentiality: **MixedConfidentiality**, correctness: Correct, continuity: Continuous}),
  (Source/AppHub, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Source/DependencyHub, {confidentiality: **NonConfidential**, correctness: Correct, continuity: Continuous}),

- (Asset/RawData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ProcessedData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ModelPretrained, {confidentiality: **MixedConfidentiality**, correctness: Correct, continuity: Continuous}),
  (Asset/ModelTrained, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Model, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ApplicationProgrammed, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Application, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Dependency, {confidentiality: **NonConfidential**, correctness: Correct, continuity: Continuous}),
  (Asset/InputQuery, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/InputToken, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/OutputToken, {confidentiality: **MixedConfidentiality**, correctness: Correct, continuity: Continuous}),
  (Asset/OutputMaterialized, {confidentiality: **MixedConfidentiality**, correctness: Correct, continuity: Continuous})

}

### Edge

edges := {

- ((RawData, DataWorker, ActedOnBy, "1.Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((DataWorker, ProcessedData, Act, "1.Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ProcessedData, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelPretrained, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelDeveloper, ModelTrained, Act, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelTrained, ModelDeveloper, ActedOnBy, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelDeveloper, ModelHub, Act, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelHub, Maintainer, ActedOnBy, "4.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Maintainer, Model, Act, "4.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((AppDeveloper, ApplicationProgrammed, Act, "5.Program"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((AppHub, Maintainer, ActedOnBy, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Maintainer, Application, Act, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((DependencyHub, Maintainer, ActedOnBy, "8.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Maintainer, Dependency, Act, "8.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Model, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Application, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Dependency, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Maintainer, IntelligentSystem, Act, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  ((User, InputQuery, Act, "10.Propose"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InputQuery, PreprocessingModule, ActedOnBy, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PreprocessingModule, InputToken, Act, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InputToken, InferenceModule, ActedOnBy, "12.Inference"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InferenceModule, OutputToken, Act, "12.Inference"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((OutputToken, PostprocessingModule, ActedOnBy, "13.Post-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PostprocessingModule, OutputMaterialized, Act, "13.Post-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PreprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InferenceModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PostprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((IntelligentSystem, OperatingEnvironment, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  ((OutputMaterialized, User, Respond, "R1.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((OutputMaterialized, OperatingEnvironment, Respond, "R2.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  ((OperatingEnvironment, IntelligentSystem, Respond, "R3.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**})

}

## Usage

Run scenario4:

```bash
python3 main.py --scenario scenario4.yaml --cycles 1 --no-feedback
```

Expected structural differences vs default:

- removed operation pair: `6.Upload` (`ActedOnBy` + `Act`)
- removed feedback edges: `R4.Respond`, `R5.Respond`, `R6.Respond`, `R7.Respond`
