# ASPLOSER Model 2.0

This document is the complete specification of the rewritten ASPLOSER model.

Normative note:

- This specification is authoritative for runtime naming and semantics.
- The maintained template diagram files are `docs/model.drawio` and derived exports under `output/`.
- Visualization files may use display labels that differ from runtime identifiers, but they must preserve Model 2.0 semantics.

Model 2.0 uses a single-arc-type object-arc Petri net:

- Round nodes are subjects.
- Rectangular nodes are actions.
- Arcs are objects.
- There is only one arc type.

## 1. Formal Definition

The system is:

$$
\mathcal{S} = (U, X, E, \Sigma_U, \Sigma_E, M_0, R)
$$

where:

- $U$ is the subject-node set (round nodes).
- $X$ is the action-node set (rectangular nodes).
- $E$ is the object-arc set (single arc type only).
- $\Sigma_U$ is the subject color domain.
- $\Sigma_E$ is the object-arc color domain.
- $M_0$ is the initial marking/color assignment.
- $R$ is the rule set (firing, structural constraints, objective aggregation).

### 1.1 Subject Nodes

Each subject node is:

$$
u = (name, role, credibility, correctness, continuity)$$

with role in {Agent, Participant}.

### 1.2 Action Nodes

Each action node is:

$$x = (name, stage)$$

with stage in {M, A, P, D, O, F}.

### 1.3 Object Arcs

Each object arc is:

$$e = (object, src, dst, confidentiality, correctness, continuity)$$

Constraints:

- Exactly one arc type exists: object arc.
- Every arc endpoint pair is bipartite: one endpoint in $U$, the other in $X$.
- No object nodes are allowed.

## 2. Color Domains

Security levels are ordered:

$$High > Mixed > Low$$

Subject color domain:

$$\Sigma_U = (credibility, correctness, continuity)$$

Object-arc color domain:

$$\Sigma_E = (confidentiality, correctness, continuity)$$

Enumerations:

- Confidentiality: Confidential, MixedConfidentiality, NonConfidential
- Correctness: Correct, MixedCorrectness, Incorrect
- Continuity: Continuous, MixedContinuity, Discontinuous
- Credibility: Trusted, MixedCredibility, Untrusted

## 3. Firing Semantics

For an action firing context with acting subject $u$ and required input arcs $e_1, \dots, e_n$, each produced arc $e_{out}$ is updated by:

$$
correctness(e_{out}) = \min\{correctness(u), correctness(e_1), \dots, correctness(e_n)\}
$$

$$
continuity(e_{out}) = \min\{continuity(u), continuity(e_1), \dots, continuity(e_n)\}
$$

$$
confidentiality(e_{out}) = \min\{credibility(u), confidentiality(e_1), \dots, confidentiality(e_n)\}
$$

## 4. Subprocess Partition

The six subprocesses are:

- M: model subprocess
- A: application subprocess
- P: dependency subprocess
- D: deployment subprocess
- O: operation subprocess
- F: feedback subprocess

## 5. Complete Node List

### 5.1 Subject Nodes U (Round)

subjects := {

- DataWorkers,
- ModelDevelopers,
- ModelHub,
- Maintainers,
- AppDevelopers,
- AppHub,
- DependencyDevelopers,
- DependencyHub,
- PreprocessingModule,
- InferenceModule,
- PostprocessingModule,
- User,
- ExternalEnv

}

### 5.2 Action Nodes X (Rectangular)

M := {

- M01.Initialize,
- M02.Initialize,
- M03.Initialize,
- M1.Collection,
- M2.Process,
- M3.Download,
- M4.Train,
- M5.Upload,
- M6.Download

}

A := {

- A01.Initialize,
- A1.Program,
- A2.Upload,
- A3.Download

}

P := {

- P01.Initialize,
- P1.Upload,
- P2.Download

}

D := {

- D01.Initialize,
- D1.Deploy,
- D2.Deploy,
- D3.Deploy

}

O := {

- O01.Initialize,
- O02.Initialize,
- O1.InputUser,
- O2.InputEnv,
- O3.Preprocess,
- O4.Infer,
- O5.PostprocessEnv,
- O6.PostprocessUser

}

F := {

- MF1.Feedback,
- MF2.Feedback,
- MF3.Feedback,
- AF1.Feedback,
- AF2.Feedback,
- PF1.Feedback,
- PF2.Feedback,
- DF1.Feedback,
- OF1.Feedback,
- OF2.Feedback,
- OF3.Feedback,
- OF4.Feedback

}

actions := M ∪ A ∪ P ∪ D ∪ O ∪ F

## 6. Complete Arc List

Arc format:

- (object, src, dst)

All arcs below are object arcs (single arc type).

### 6.1 M Arcs

arcs_M := {

- (RawDataP, M01.Initialize, DataWorkers),
- (ModelSpecP, M02.Initialize, ModelDevelopers),
- (PretrainedModelDeclarationP, M03.Initialize, ModelHub),
- (RawDataO, DataWorkers, M1.Collection),
- (UnstructuredDataI, M1.Collection, DataWorkers),
- (UnstructuredDataO, DataWorkers, M2.Process),
- (ProcessedDataI, M2.Process, ModelDevelopers),
- (PretrainedModelDownloadedI, ModelHub, M3.Download),
- (PretrainedModelDownloadedO, M3.Download, ModelDevelopers),
- (ModelMaterialO, ModelDevelopers, M4.Train),
- (ModelToBeUploadI, M4.Train, ModelDevelopers),
- (ModelToBeUploadO, ModelDevelopers, M5.Upload),
- (ModelUploadedI, M5.Upload, ModelHub),
- (ModelUploadedO, ModelHub, M6.Download),
- (ModelDownloadedI, M6.Download, Maintainers),
- (Feedback, DataWorkers, MF1.Feedback),
- (Feedback, MF1.Feedback, DataWorkers),
- (Feedback, ModelDevelopers, MF2.Feedback),
- (Feedback, MF2.Feedback, ModelDevelopers),
- (Feedback, ModelHub, MF3.Feedback),
- (Feedback, MF3.Feedback, ModelHub)

}

### 6.2 A Arcs

arcs_A := {

- (AppSpecP, A01.Initialize, AppDevelopers),
- (AppSpecO, AppDevelopers, A1.Program),
- (AppProgrammedI, A1.Program, AppDevelopers),
- (AppProgrammedO, AppDevelopers, A2.Upload),
- (AppUploadedI, A2.Upload, AppHub),
- (AppUploadedO, AppHub, A3.Download),
- (AppDownloadedI, A3.Download, Maintainers),
- (DependencyDeclarationI, A1.Program, DependencyHub),
- (Feedback, AppDevelopers, AF1.Feedback),
- (Feedback, AF1.Feedback, AppDevelopers),
- (Feedback, AppHub, AF2.Feedback),
- (Feedback, AF2.Feedback, AppHub)

}

### 6.3 P Arcs

arcs_P := {

- (DependencyProgrammedP, P01.Initialize, DependencyDevelopers),
- (DependencyProgrammedO, DependencyDevelopers, P1.Upload),
- (DependenciesUploadedI, P1.Upload, DependencyHub),
- (DependenciesUploadedO, DependencyHub, P2.Download),
- (DependenciesDownloadedI, P2.Download, Maintainers),
- (Feedback, DependencyDevelopers, PF1.Feedback),
- (Feedback, PF1.Feedback, DependencyDevelopers),
- (Feedback, DependencyHub, PF2.Feedback),
- (Feedback, PF2.Feedback, DependencyHub)

}

### 6.4 D Arcs

arcs_D := {

- (OperatingEnvP, D01.Initialize, Maintainers),
- (AppAndDepO, Maintainers, D1.Deploy),
- (ModelAppAndDepO, Maintainers, D2.Deploy),
- (AppAndDepO, Maintainers, D3.Deploy),
- (AppAndDepI, D1.Deploy, PreprocessingModule),
- (ModelAppAndDepI, D2.Deploy, InferenceModule),
- (AppAndDepI, D3.Deploy, PostprocessingModule),
- (Feedback, Maintainers, DF1.Feedback),
- (Feedback, DF1.Feedback, Maintainers)

}

### 6.5 O Arcs

arcs_O := {

- (ProposalMaterializedP, O01.Initialize, ExternalEnv),
- (ProposalP, O02.Initialize, User),
- (InputUserO, User, O1.InputUser),
- (InputEnvI, O1.InputUser, ExternalEnv),
- (InputEnvO, ExternalEnv, O2.InputEnv),
- (InputI, O2.InputEnv, PreprocessingModule),
- (InputTokensO, PreprocessingModule, O3.Preprocess),
- (InputTokensI, O3.Preprocess, InferenceModule),
- (OutputTokensO, InferenceModule, O4.Infer),
- (OutputTokensI, O4.Infer, PostprocessingModule),
- (OutputEnvO, PostprocessingModule, O5.PostprocessEnv),
- (OutputEnvI, O5.PostprocessEnv, ExternalEnv),
- (OutputUserO, PostprocessingModule, O6.PostprocessUser),
- (OutputUserI, O6.PostprocessUser, User),
- (Feedback, PreprocessingModule, OF1.Feedback),
- (Feedback, OF1.Feedback, PreprocessingModule),
- (Feedback, InferenceModule, OF2.Feedback),
- (Feedback, OF2.Feedback, InferenceModule),
- (Feedback, PostprocessingModule, OF3.Feedback),
- (Feedback, OF3.Feedback, PostprocessingModule),
- (Feedback, User, OF4.Feedback)

}

### 6.6 F Arcs

arcs_F is empty; all feedback arcs are distributed across arcs_M, arcs_A, arcs_P, arcs_D, and arcs_O above.

Total arc set:

$$E = arcs_M \cup arcs_A \cup arcs_P \cup arcs_D \cup arcs_O \cup arcs_F$$

## 7. Structural Constraints

### 7.1 Dependency Upper Bound

If subject $u$ depends on object-arc set $D(u)$, then:

$$
correctness(u) \le \min\{correctness(e) \mid e \in D(u)\}
$$

$$
continuity(u) \le \min\{continuity(e) \mid e \in D(u)\}
$$

### 7.2 Core Inference Rules

- PreprocessingModule <= AppAndDepI
- InferenceModule <= ModelAppAndDepI
- PostprocessingModule <= AppAndDepI

Credibility is scenario-designated.

## 8. Security Objective Aggregation

- Confidentiality objective: minimum confidentiality level across executed object arcs under connected subject credibility.
- Integrity objective: minimum correctness level across executed object arcs and participating subjects.
- Availability objective: minimum continuity level across required executed object arcs.

## 9. Visualization And Reporting Rules

- The renderer colors propagated high risk in red and propagated medium risk in yellow.
- Explicitly assigned initialize-time risk remains visually distinct from propagated risk:
	- assigned high risk uses purple
	- assigned medium risk uses blue
- Initialize actions are entry points and are always rendered in green.
- Initialize-created objects are not treated as green visualization nodes; they follow the normal assigned or propagated risk palette.
- Subject coloring follows the same severity ordering, but assigned subjects keep assigned colors only at their assigned baseline. If a connected propagated state raises an assigned subject to high severity, the subject is rendered with propagated red.
- Subject-driven recoloring is directional: only outgoing arcs from inferred module subjects inherit propagated subject state.
- Feedback actions are part of the model, but propagation analysis summaries and execution logs stop before the Feedback stage when feedback execution is disabled.
- Runtime stages are ordered as Development, Deployment, Operation, then Feedback.

## 10. Normative Modeling Rules

- Use only subject nodes and action nodes.
- Use only object arcs.
- Keep all endpoints bipartite between subject and action.
- Do not add object nodes.
- Do not add extra arc classes.
- Static object-arc attribute assignment is allowed only in initialize actions; subsequent updates must follow firing semantics.

This document is the authoritative Model 2.0 rewrite.