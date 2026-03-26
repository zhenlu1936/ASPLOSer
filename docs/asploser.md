# Syntactic Definition

System ::= (graph: SystemGraph, security: SecurityObjectives)

### Graph

- SystemGraph ::= {nodes: Set<Node>, edges: Set<Edge>}

### Node

- Node ::= SubjectNode | ObjectNode
- SubjectNode ::= (type: SubjectNodeType, attributes: SubjectNodeAttributes)
- ObjectNode ::= (type: ObjectNodeType, attributes: ObjectNodeAttributes)
- SubjectNodeType ::= Agent | Participant
- ObjectNodeType ::= Asset | Source

### Edge

- Edge ::= (edge: EdgeCore, attributes: EdgeAttributes)
- EdgeCore ::= (source: Node, target: Node, type: EdgeType, name: EdgeName)
- EdgeType ::= InteractionEdge | StructureEdge
- InteractionEdge ::= Act | ActedOnBy | Respond
- StructureEdge ::= ComponentOf

### Attribute

- SubjectNodeAttributes ::= {credibility: Credibility, correctness: Correctness, continuity: Continuity}
- ObjectNodeAttributes ::= {confidentiality: Confidentiality, correctness: Correctness, continuity: Continuity}
- EdgeAttributes ::= {confidentiality: Confidentiality, correctness: Correctness, continuity: Continuity}

- Confidentiality ::= Confidential | MixedConfidentiality | NonConfidential
- Correctness ::= Correct | MixedCorrectness | Incorrect
- Continuity ::= Continuous | MixedContinuity | Discontinuous
- Credibility ::= Trusted | MixedCredibility | Untrusted

### Security Objective

- SecurityObjectives ::= {confidentiality: ConfidentialityObjective, integrity: IntegrityObjective, availability: AvailabilityObjective}

- ConfidentialityObjective is jointly determined by Confidentiality and Credibility.
- IntegrityObjective is jointly determined by Correctness and Credibility.
- AvailabilityObjective is jointly determined by Continuity and Credibility.

### System Instance

- Agent ::= IntelligentSystem | PreprocessingModule | InferenceModule | PostprocessingModule
- Participant ::= User | ModelDeveloper | AppDeveloper | Maintainer | DataWorker | OperatingEnvironment
- Source ::= ModelHub | AppHub | DependencyHub
- Asset ::= RawData | ProcessedData | ModelPretrained | ModelTrained | Model | ApplicationProgrammed | Application | Dependency | InputQuery | InputToken | OutputToken | OutputMaterialized

edges := {

- ((RawData, DataWorker, ActedOnBy, "1.Process"), {...}),
- ((DataWorker, ProcessedData, Act, "1.Process"), {...}),
- ((ProcessedData, ModelDeveloper, ActedOnBy, "2.Train"), {...}),
- ((ModelPretrained, ModelDeveloper, ActedOnBy, "2.Train"), {...}),
- ((ModelDeveloper, ModelTrained, Act, "2.Train"), {...}),
- ((ModelTrained, ModelDeveloper, ActedOnBy, "3.Upload"), {...}),
- ((ModelDeveloper, ModelHub, Act, "3.Upload"), {...}),
- ((ModelHub, Maintainer, ActedOnBy, "4.Download"), {...}),
- ((Maintainer, Model, Act, "4.Download"), {...}),
- ((AppDeveloper, ApplicationProgrammed, Act, "5.Program"), {...}),
- ((ApplicationProgrammed, AppDeveloper, ActedOnBy, "6.Upload"), {...}),
- ((AppDeveloper, AppHub, Act, "6.Upload"), {...}),
- ((AppHub, Maintainer, ActedOnBy, "7.Download"), {...}),
- ((Maintainer, Application, Act, "7.Download"), {...}),
- ((DependencyHub, Maintainer, ActedOnBy, "8.Download"), {...}),
- ((Maintainer, Dependency, Act, "8.Download"), {...}),
- ((Model, Maintainer, ActedOnBy, "9.Assemble"), {...}),
- ((Application, Maintainer, ActedOnBy, "9.Assemble"), {...}),
- ((Dependency, Maintainer, ActedOnBy, "9.Assemble"), {...}),
- ((Maintainer, IntelligentSystem, Act, "9.Assemble"), {...}),
- ((User, InputQuery, Act, "10.Propose"), {...}),
- ((InputQuery, PreprocessingModule, ActedOnBy, "11.Pre-Process"), {...}),
- ((PreprocessingModule, InputToken, Act, "11.Pre-Process"), {...}),
- ((InputToken, InferenceModule, ActedOnBy, "12.Inference"), {...}),
- ((InferenceModule, OutputToken, Act, "12.Inference"), {...}),
- ((OutputToken, PostprocessingModule, ActedOnBy, "13.Post-Process"), {...}),
- ((PostprocessingModule, OutputMaterialized, Act, "13.Post-Process"), {...}),
- ((PreprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {...}),
- ((InferenceModule, IntelligentSystem, ComponentOf, "ComponentOf"), {...}),
- ((PostprocessingModule, IntelligentSystem, ComponentOf, "ComponentOf"), {...}),
- ((IntelligentSystem, OperatingEnvironment, ComponentOf, "ComponentOf"), {...}),
- ((OutputMaterialized, User, Respond, "R1.Respond"), {...}),
- ((OutputMaterialized, OperatingEnvironment, Respond, "R2.Respond"), {...}),
- ((OperatingEnvironment, IntelligentSystem, Respond, "R3.Respond"), {...}),
- ((User, DataWorker, Respond, "R4.Respond"), {...}),
- ((User, ModelDeveloper, Respond, "R5.Respond"), {...}),
- ((User, AppDeveloper, Respond, "R6.Respond"), {...}),
- ((User, Maintainer, Respond, "R7.Respond"), {...})

}

# Semantic Definition

### Attribute Semantics

Confidentiality: the degree to which information is protected against unauthorized disclosure.
- For a subject: whether the subject refrains from accessing object information without authorization.
- For an object: whether the information embodied in the object cannot be accessed without authorization.
- For an edge: whether the corresponding action cannot be observed, intercepted, or disclosed without authorization.

Correctness: the degree to which behavior conforms to intended functionality and applicable safety requirements.
- For a subject: whether the subject performs actions correctly and in compliance with safety requirements.
- For an object: whether the object remains correct and compliant with safety requirements.
- For an edge: whether the corresponding action is executed correctly and in compliance with safety requirements.

Continuity: the degree to which availability and operability are maintained without interruption.
- For a subject: whether the subject can continue to perform actions without interruption.
- For an object: whether the object remains accessible without interruption.
- For an edge: whether the corresponding action can continue to be performed without interruption.

Credibility: the degree to which a subject can be trusted not to misuse accessible resources or undermine system properties.
- A credible subject does not misuse exposed non-confidential information, exploit correctness violations, or deliberately induce discontinuities.
- If a subject is untrusted, its correctness and continuity cannot exceed the mixed level, and it may intentionally behave incorrectly or discontinuously whenever doing so serves its interests.

Mixed-level rule:
- If an attribute is assigned the mixed level, its concrete manifestation is not fixed to either the high or the low level; within a particular interaction, operation, or context, it may exhibit either behavior.

### Propagation Intuition

Confidentiality propagation:
- Exposure propagates across nodes and edges when the relevant subject is untrusted, the relevant object is non-confidential, and the relevant edge is non-confidential.

Correctness propagation:
- Incorrectness propagates across nodes and edges when a relevant node is incorrect and a relevant subject is untrusted.

Continuity propagation:
- If a required node or edge is discontinuous, the corresponding system operation is blocked.

### Structural Constraints

<!-- a lesson: user should not determine the security levels of the IS, which may be higher than the inferenced ones.-->

Component upper-bound rule:
- If a subject s1 is a component of a subject s2, then, for every shared security dimension, the attribute level of s2 shall not exceed that of s1.

Dependency upper-bound rule:
- If subject s depends on objects o1, ..., on to perform its intended function, then the relevant attribute levels of s shall not exceed the corresponding attribute levels of o1, ..., on.

Inference rule for core agents:
- The correctness and continuity of IntelligentSystem, PreprocessingModule, InferenceModule, and PostprocessingModule are inferred from their dependency assets rather than assigned directly.
- IntelligentSystem correctness and continuity are upper-bounded by Model, Application, and Dependency.
- PreprocessingModule correctness and continuity are upper-bounded by Application and Dependency.
- InferenceModule correctness and continuity are upper-bounded by Model, Application, and Dependency.
- PostprocessingModule correctness and continuity are upper-bounded by Application and Dependency.
- The credibility of these subjects remains explicitly designated by the scenario.

Instance constraints:
- IntelligentSystem depends on Model, Application, and Dependency.
- PreprocessingModule depends on Application and Dependency.
- InferenceModule depends on Model, Application, and Dependency.
- PostprocessingModule depends on Application and Dependency.

### Metrics

Confidentiality:
- the extent to which an object's information is protected from access by unauthorized subjects

Integrity:
- the extent to which a subject produces correct objects compliant with safety requirements, and accessed objects remain correct and uncompromised

Availability:
- the extent to which authorized subjects retain reliable and uninterrupted access to objects

# SSA

```c++
// SDLC?

IntelligentSystem.Components = {
    PreprocessingModule,
    InferenceModule,
    PostprocessingModule
};

OperatingEnvironment.Components = {
    IntelligentSystem
};

do {
  // Development Stage
  // or Initiation - Development - Implementation Stage in SDLC 
  ProcessedData = DataWorker.Process(RawData);
  ModelTrained = ModelDeveloper.Train(ProcessedData, ModelPretrained);
  ApplicationProgrammed = AppDeveloper.Program();
  // There should be an alpha test or not?
  ModelHub = ModelDeveloper.Upload(ModelTrained);
  AppHub = AppDeveloper.Upload(ApplicationProgrammed);

  // Deployment Stage
  // or Operations Stage in SDLC
  Model = Maintainer.Download(ModelHub);
  Application = Maintainer.Download(AppHub);
  Dependency = Maintainer.Download(DependencyHub);
  IntelligentSystem = Maintainer.Assemble(Model, Application, Dependency);

  // Inference Stage
  InputQuery = User.Propose();
  InputToken = PreprocessingModule.PreProcess(InputQuery);
  OutputToken = InferenceModule.Inference(InputToken);
  OutputMaterialized = PostprocessingModule.PostProcess(OutputToken);

  // Response Stage
  User = OutputMaterialized.Respond(User);
  OperatingEnvironment = OutputMaterialized.Respond(OperatingEnvironment);
  
  // Feedback Stage
  // or Disposal Stage in SDLC
  if (Feedback) {
    DataWorker = User.Respond(DataWorker);
    ModelDeveloper = User.Respond(ModelDeveloper);
    AppDeveloper = User.Respond(AppDeveloper);
    Maintainer = User.Respond(Maintainer);
  }
  
  DevelopmentCycles--;
} While (DevelopmentCycles);
```