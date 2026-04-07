# ASPLOSER Model 2.0

This document is the complete specification of the rewritten ASPLOSER model.

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

- IntelligentSystem,
- PreprocessingModule,
- InferenceModule,
- PostprocessingModule,
- User,
- ModelDeveloper,
- AppDeveloper,
- Maintainer,
- DataWorker,
- OperatingEnvironment

}

### 5.2 Action Nodes X (Rectangular)

M := {

- 1.Process,
- 2.Train,
- 3.Upload,
- 4.Download

}

A := {

- 5.Program,
- 6.Upload,
- 7.Download

}

P := {

- 8.Download

}

D := {

- 9.Assemble

}

O := {

- 10.Propose,
- 11.Pre-Process,
- 12.Inference,
- 13.Post-Process,
- R1.Respond,
- R2.Respond,
- R3.Respond

}

F := {

- R4.Respond,
- R5.Respond,
- R6.Respond,
- R7.Respond

}

actions := M ∪ A ∪ P ∪ D ∪ O ∪ F

## 6. Complete Arc List

Arc format:

- (object, src, dst)

All arcs below are object arcs (single arc type).

### 6.1 M Arcs

arcs_M := {

- (RawData, DataWorker, 1.Process),
- (ProcessedData, 1.Process, ModelDeveloper),
- (ProcessedData, ModelDeveloper, 2.Train),
- (ModelPretrained, ModelDeveloper, 2.Train),
- (ModelTrained, 2.Train, ModelDeveloper),
- (ModelTrained, ModelDeveloper, 3.Upload),
- (ModelHub, 3.Upload, Maintainer),
- (ModelHub, Maintainer, 4.Download),
- (Model, 4.Download, Maintainer)

}

### 6.2 A Arcs

arcs_A := {

- (ProgramIntent, AppDeveloper, 5.Program),
- (ApplicationProgrammed, 5.Program, AppDeveloper),
- (ApplicationProgrammed, AppDeveloper, 6.Upload),
- (AppHub, 6.Upload, Maintainer),
- (AppHub, Maintainer, 7.Download),
- (Application, 7.Download, Maintainer)

}

### 6.3 P Arcs

arcs_P := {

- (DependencyHub, Maintainer, 8.Download),
- (Dependency, 8.Download, Maintainer)

}

### 6.4 D Arcs

arcs_D := {

- (Model, Maintainer, 9.Assemble),
- (Application, Maintainer, 9.Assemble),
- (Dependency, Maintainer, 9.Assemble),
- (IntelligentSystem, 9.Assemble, IntelligentSystem)

}

### 6.5 O Arcs

arcs_O := {

- (UserIntent, User, 10.Propose),
- (InputQuery, 10.Propose, PreprocessingModule),
- (InputQuery, PreprocessingModule, 11.Pre-Process),
- (InputToken, 11.Pre-Process, InferenceModule),
- (InputToken, InferenceModule, 12.Inference),
- (OutputToken, 12.Inference, PostprocessingModule),
- (OutputToken, PostprocessingModule, 13.Post-Process),
- (OutputMaterialized, 13.Post-Process, PostprocessingModule),
- (OutputMaterialized, PostprocessingModule, R1.Respond),
- (UserVisibleOutput, R1.Respond, User),
- (OutputMaterialized, PostprocessingModule, R2.Respond),
- (EnvVisibleOutput, R2.Respond, OperatingEnvironment),
- (EnvObservation, OperatingEnvironment, R3.Respond),
- (SystemFeedback, R3.Respond, IntelligentSystem)

}

### 6.6 F Arcs

arcs_F := {

- (UserFeedbackToDataWorker, User, R4.Respond),
- (DataWorkerFeedback, R4.Respond, DataWorker),
- (UserFeedbackToModelDeveloper, User, R5.Respond),
- (ModelDeveloperFeedback, R5.Respond, ModelDeveloper),
- (UserFeedbackToAppDeveloper, User, R6.Respond),
- (AppDeveloperFeedback, R6.Respond, AppDeveloper),
- (UserFeedbackToMaintainer, User, R7.Respond),
- (MaintainerFeedback, R7.Respond, Maintainer)

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

- IntelligentSystem <= Model, Application, Dependency
- PreprocessingModule <= Application, Dependency
- InferenceModule <= Model, Application, Dependency
- PostprocessingModule <= Application, Dependency

Credibility is scenario-designated.

## 8. Security Objective Aggregation

- Confidentiality objective: minimum confidentiality level across executed object arcs under connected subject credibility.
- Integrity objective: minimum correctness level across executed object arcs and participating subjects.
- Availability objective: minimum continuity level across required executed object arcs.

## 9. Normative Modeling Rules

- Use only subject nodes and action nodes.
- Use only object arcs.
- Keep all endpoints bipartite between subject and action.
- Do not add object nodes.
- Do not add extra arc classes.

This document is the authoritative Model 2.0 rewrite.