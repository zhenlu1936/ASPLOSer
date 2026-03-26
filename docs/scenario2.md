# Scenario 2: Enterprise Cloud-Based Inference Pipeline

## Composition Note

This document describes the composed system after applying the overrides from
`scenario2.yaml` to the default ASPLOSER graph.

The YAML file is not a standalone full graph definition. It extends the default
system with the override-based scenario schema described in
`README_framework.md`.

## Overview

An enterprise organization uses a cloud-based ML pipeline with third-party model providers and public repositories. The system involves untrusted external partners and operates on shared cloud infrastructure with mixed reliability guarantees.

- ModelDeveloper, AppDeveloper, and DataWorker are internal trusted team members, but Maintainer may be a third-party cloud service provider with limited trustworthiness.

- ModelHub and AppHub are public repositories (e.g., Hugging Face, GitHub) accessible by anyone, so they are treated as having lower confidentiality guarantees.

- The pretrained model comes from external sources and cannot be fully trusted for correctness.

- The intelligent system runs on shared cloud infrastructure (Kubernetes cluster) without strict hardware isolation, leading to mixed continuity guarantees at deployment boundaries.

- The OperatingEnvironment represents a multi-tenant cloud platform that could be subject to noise, contention, or service degradation.

- User interactions occur through a web API that crosses network boundaries with potential packet loss or network interruption.

### Node

nodes := {

- (Agent/IntelligentSystem, {credibility: **Mixed**, correctness: Correct, continuity: **MixedContinuity**}),
  (Agent/PreprocessingModule, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Agent/InferenceModule, {credibility: **Mixed**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Agent/PostprocessingModule, {credibility: Trusted, correctness: Correct, continuity: Continuous}),

- (Participant/User, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/ModelDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/AppDeveloper, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/Maintainer, {credibility: **Mixed**, correctness: Correct, continuity: **MixedContinuity**}),
  (Participant/DataWorker, {credibility: Trusted, correctness: Correct, continuity: Continuous}),
  (Participant/OperatingEnvironment, {credibility: Trusted, correctness: Correct, continuity: **MixedContinuity**}),

- (Source/ModelHub, {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Source/AppHub, {confidentiality: **Public**, correctness: Correct, continuity: Continuous}),
  (Source/DependencyHub, {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),

- (Asset/RawData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ProcessedData, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ModelPretrained, {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Asset/ModelTrained, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Model, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/ApplicationProgrammed, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Application, {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
  (Asset/Dependency, {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),
  (Asset/InputQuery, {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  (Asset/InputToken, {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
  (Asset/OutputToken, {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
  (Asset/OutputMaterialized, {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**})

}

### Edge

edges := {

- ((RawData, DataWorker, ActedOnBy, "1.Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((DataWorker, ProcessedData, Act, "1.Process"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ProcessedData, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelPretrained, ModelDeveloper, ActedOnBy, "2.Train"), {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),
- ((ModelDeveloper, ModelTrained, Act, "2.Train"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelTrained, ModelDeveloper, ActedOnBy, "3.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ModelDeveloper, ModelHub, Act, "3.Upload"), {confidentiality: **Public**, correctness: Correct, continuity: Continuous}),
- ((ModelHub, Maintainer, ActedOnBy, "4.Download"), {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),
- ((Maintainer, Model, Act, "4.Download"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((AppDeveloper, ApplicationProgrammed, Act, "5.Program"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((ApplicationProgrammed, AppDeveloper, ActedOnBy, "6.Upload"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((AppDeveloper, AppHub, Act, "6.Upload"), {confidentiality: **Public**, correctness: Correct, continuity: Continuous}),
- ((AppHub, Maintainer, ActedOnBy, "7.Download"), {confidentiality: **Public**, correctness: Correct, continuity: Continuous}),
- ((Maintainer, Application, Act, "7.Download"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((DependencyHub, Maintainer, ActedOnBy, "8.Download"), {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: Continuous}),
- ((Maintainer, Dependency, Act, "8.Download"), {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((Model, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((Application, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((Dependency, Maintainer, ActedOnBy, "9.Assemble"), {confidentiality: **Public**, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((Maintainer, IntelligentSystem, Act, "9.Assemble"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((User, InputQuery, Act, "10.Propose"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((InputQuery, PreprocessingModule, ActedOnBy, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((PreprocessingModule, InputToken, Act, "11.Pre-Process"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((InputToken, InferenceModule, ActedOnBy, "12.Inference"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((InferenceModule, OutputToken, Act, "12.Inference"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((OutputToken, PostprocessingModule, ActedOnBy, "13.Post-Process"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((PostprocessingModule, OutputMaterialized, Act, "13.Post-Process"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((PreprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((InferenceModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((PostprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((IntelligentSystem, OperatingEnvironment, ComponentOf, "ComponentOf"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((OutputMaterialized, User, Respond, "R1.Respond"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((OutputMaterialized, OperatingEnvironment, Respond, "R2.Respond"), {confidentiality: Confidential, correctness: **MixedCorrectness**, continuity: **MixedContinuity**}),
- ((OperatingEnvironment, IntelligentSystem, Respond, "R3.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**}),
- ((User, DataWorker, Respond, "R4.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((User, ModelDeveloper, Respond, "R5.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((User, AppDeveloper, Respond, "R6.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: Continuous}),
- ((User, Maintainer, Respond, "R7.Respond"), {confidentiality: Confidential, correctness: Correct, continuity: **MixedContinuity**})

}

## Usage

Run scenario2:

```bash
python3 main.py --scenario scenario2.yaml --cycles 1 --no-feedback
```
