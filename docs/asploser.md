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
- Users,
- OutsideEnv

}

### 5.2 Action Nodes X (Rectangular)

M := {

- M0.Initialize,
- M1.Collection,
- M2.Process,
- M3.Download,
- M4.Train,
- M5.Upload,
- M6.Download

}

A := {

- A0.Initialize,
- A1.Program,
- A2.Upload,
- A3.Download

}

P := {

- P0.Initialize,
- P1.Upload,
- P2.Download

}

D := {

- D0.Initialize,
- D1.Delopy,
- D2.Delopy,
- D3.Delopy

}

O := {

- O0.Initialize,
- O1.Input,
- O2.Preprocess,
- O3.Infer,
- O4.Postprocess

}

F := {

- F1.Feedback (instanced multiple times in the picture)

}

actions := M ∪ A ∪ P ∪ D ∪ O ∪ F

## 6. Complete Arc List

Arc format:

- (object, src, dst)

All arcs below are object arcs (single arc type).

### 6.1 M Arcs

arcs_M := {

- (RawDataP, M0.Initialize, DataWorkers),
- (ModelSpecP, M0.Initialize, ModelDevelopers),
- (PretrainedModelDeclarationP, M0.Initialize, ModelHub),
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
- (ModelDownloadedI, M6.Download, Maintainers)

}

### 6.2 A Arcs

arcs_A := {

- (AppSpecP, A0.Initialize, AppDevelopers),
- (AppSpecO, AppDevelopers, A1.Program),
- (AppProgrammedI, A1.Program, AppDevelopers),
- (AppProgrammedO, AppDevelopers, A2.Upload),
- (AppUploadedI, A2.Upload, AppHub),
- (AppUploadedO, AppHub, A3.Download),
- (AppDownloadedI, A3.Download, Maintainers)

}

### 6.3 P Arcs

arcs_P := {

- (DependencyProgrammedP, P0.Initialize, DependencyDevelopers),
- (DependencyProgrammedO, DependencyDevelopers, P1.Upload),
- (DependenciesUploadedI, P1.Upload, DependencyHub),
- (DependenciesUploadedO, DependencyHub, P2.Download),
- (DependenciesDownloadedI, P2.Download, Maintainers),
- (DependencyDeclarationI, A1.Program, DependencyHub)

}

### 6.4 D Arcs

arcs_D := {

- (OperatingEnvP, D0.Initialize, Maintainers),
- (AppAndDepO, Maintainers, D1.Delopy),
- (ModelAppAndDepO, Maintainers, D2.Delopy),
- (AppAndDepO, Maintainers, D3.Delopy),
- (AppAndDepI, D1.Delopy, PreprocessingModule),
- (ModelAppAndDepI, D2.Delopy, InferenceModule),
- (AppAndDepI, D3.Delopy, PostprocessingModule)

}

### 6.5 O Arcs

arcs_O := {

- (ProposalP, O0.Initialize, Users),
- (ProposalMaterializedP, O0.Initialize, OutsideEnv),
- (InputO, Users, O1.Input),
- (InputMaterializedO, OutsideEnv, O1.Input),
- (InputI, O1.Input, PreprocessingModule),
- (InputTokensO, PreprocessingModule, O2.Preprocess),
- (InputTokensI, O2.Preprocess, InferenceModule),
- (OutputTokensO, InferenceModule, O3.Infer),
- (OutputTokensI, O3.Infer, PostprocessingModule),
- (OutputO, PostprocessingModule, O4.Postprocess),
- (OutputI, O4.Postprocess, Users),
- (OutputMaterializedI, O4.Postprocess, OutsideEnv)

}

### 6.6 F Arcs

arcs_F := {

- (OutputFeedbackO, Users, F1.Feedback),
- (FeedbackI, F1.Feedback, ModelDevelopers),
- (FeedbackI, F1.Feedback, AppDevelopers),
- (FeedbackI, F1.Feedback, DependencyDevelopers),
- (FeedbackI, F1.Feedback, Maintainers)

}

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