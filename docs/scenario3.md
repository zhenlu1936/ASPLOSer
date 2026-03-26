# Scenario 3: Adversarial Supply Chain with Risk Propagation

## Composition Note

This document describes the composed system after applying the overrides from
`scenario3.yaml` to the default ASPLOSER graph.

The YAML file is not a standalone full graph definition. It extends the default
system with the override-based scenario schema described in
`README_framework.md`.

## Overview

Scenario 3 models an adversarial supply chain where untrusted participants and
public-facing edges introduce both confidentiality and availability propagation
risks.

### Node

nodes := {

- (Agent/IntelligentSystem, {credibility: **MixedCredibility**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Agent/PreprocessingModule, {credibility: Trusted, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Agent/InferenceModule, {credibility: Trusted, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Agent/PostprocessingModule, {credibility: Trusted, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),

- (Participant/User, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/ModelDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/AppDeveloper, {credibility: **Untrusted**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Participant/Maintainer, {credibility: **Untrusted**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  (Participant/DataWorker, {credibility: **Untrusted**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Participant/OperatingEnvironment, {credibility: **MixedCredibility**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),

- (Source/ModelHub, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Source/AppHub, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Source/DependencyHub, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),

- (Asset/RawData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ProcessedData, {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Asset/ModelPretrained, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Asset/ModelTrained, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Model, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ApplicationProgrammed, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Asset/Application, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Asset/Dependency, {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Asset/InputQuery, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/InputToken, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/OutputToken, {confidentiality: **MixedConfidentiality**, correctness: Correct, continuity: Continuous}),
  (Asset/OutputMaterialized, {confidentiality: **MixedConfidentiality**, correctness: Correct, continuity: Continuous})

}

### Edge

edges := {

- ((RawData, DataWorker, ActedOnBy, "1.Process"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((DataWorker, ProcessedData, Act, "1.Process"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((ProcessedData, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((ModelPretrained, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((ModelDeveloper, ModelTrained, Act, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelTrained, ModelDeveloper, ActedOnBy, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelDeveloper, ModelHub, Act, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((ModelHub, Maintainer, ActedOnBy, "4.Download"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((Maintainer, Model, Act, "4.Download"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((AppDeveloper, ApplicationProgrammed, Act, "5.Program"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((ApplicationProgrammed, AppDeveloper, ActedOnBy, "6.Upload"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((AppDeveloper, AppHub, Act, "6.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((AppHub, Maintainer, ActedOnBy, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((Maintainer, Application, Act, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((DependencyHub, Maintainer, ActedOnBy, "8.Download"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((Maintainer, Dependency, Act, "8.Download"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((Model, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((Application, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((Dependency, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((Maintainer, IntelligentSystem, Act, "9.Assemble"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((User, InputQuery, Act, "10.Propose"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InputQuery, PreprocessingModule, ActedOnBy, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PreprocessingModule, InputToken, Act, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InputToken, InferenceModule, ActedOnBy, "12.Inference"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((InferenceModule, OutputToken, Act, "12.Inference"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  ((OutputToken, PostprocessingModule, ActedOnBy, "13.Post-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PostprocessingModule, OutputMaterialized, Act, "13.Post-Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PreprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((InferenceModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((PostprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((IntelligentSystem, OperatingEnvironment, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((OutputMaterialized, User, Respond, "R1.Respond"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((OutputMaterialized, OperatingEnvironment, Respond, "R2.Respond"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((OperatingEnvironment, IntelligentSystem, Respond, "R3.Respond"), {confidentiality: **NonConfidential**, correctness: **MixedCorrectness**, continuity: **Discontinuous**}),
  ((User, DataWorker, Respond, "R4.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((User, ModelDeveloper, Respond, "R5.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((User, AppDeveloper, Respond, "R6.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  ((User, Maintainer, Respond, "R7.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous})

}

## Usage

Run scenario3:

```bash
python3 main.py --scenario scenario3.yaml --cycles 1 --no-feedback
```

Expected behavior:

- propagation risks are detected
- detailed log is generated at `output/scenario3_propagation_log.txt`
