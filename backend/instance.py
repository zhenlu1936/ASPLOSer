from __future__ import annotations

from dataclasses import replace

from .model import (
    Confidentiality,
    Continuity,
    Correctness,
    Credibility,
    Edge,
    EdgeAttributes,
    EdgeType,
    Node,
    ObjectNodeAttributes,
    SubjectNodeAttributes,
    System,
    SystemGraph,
)


def _subject(name: str, type_name: str, credibility: Credibility) -> Node:
    """Create a subject node, applying semantic constraint: untrusted subjects cap to mixed C/C."""
    is_untrusted = credibility == Credibility.UNTRUSTED
    return Node(
        name=name,
        is_subject=True,
        type=type_name,
        subject_attributes=SubjectNodeAttributes(
            credibility=credibility,
            correctness=Correctness.MIXED_CORRECTNESS if is_untrusted else Correctness.CORRECT,
            continuity=Continuity.MIXED_CONTINUITY if is_untrusted else Continuity.CONTINUOUS,
        ),
    )


def _object(name: str, type_name: str, confidentiality: Confidentiality) -> Node:
    return Node(
        name=name,
        is_subject=False,
        type=type_name,
        object_attributes=ObjectNodeAttributes(
            confidentiality=confidentiality,
            correctness=Correctness.CORRECT,
            continuity=Continuity.CONTINUOUS,
        ),
    )


def _default_edge_attrs() -> EdgeAttributes:
    return EdgeAttributes(
        confidentiality=Confidentiality.CONFIDENTIAL,
        correctness=Correctness.CORRECT,
        continuity=Continuity.CONTINUOUS,
    )


def _enum_from_level(enum_cls, level_value: int):
    """Look up enum member by level value (0=low, 1=mixed, 2=high)."""
    for member in enum_cls:
        if member.level().value == level_value:
            return member
    raise ValueError(f"No {enum_cls.__name__} member for level={level_value}")


def infer_subject_attributes_from_assets(system: System) -> None:
    """Infer key subject correctness/continuity from dependency assets.

    Rules (correctness/continuity upper-bounded by dependent assets):
    - IntelligentSystem <= Model, Application, Dependency
    - PreprocessingModule <= Application, Dependency
    - InferenceModule <= Model, Application, Dependency
    - PostprocessingModule <= Application, Dependency
    """
    graph = system.graph
    infer_targets = {
        "IntelligentSystem",
        "PreprocessingModule",
        "InferenceModule",
        "PostprocessingModule",
    }

    for subject_name in infer_targets:
        node = graph.nodes.get(subject_name)
        if node is None or not node.is_subject:
            continue

        deps = system.dependencies.get(subject_name, set())
        if not deps:
            continue

        dep_objects = []
        for dep_name in deps:
            dep_node = graph.nodes.get(dep_name)
            if dep_node is not None and not dep_node.is_subject:
                dep_objects.append(dep_node.as_object())

        if not dep_objects:
            continue

        inferred_correctness_level = min(obj.correctness.level().value for obj in dep_objects)
        inferred_continuity_level = min(obj.continuity.level().value for obj in dep_objects)

        current = node.as_subject()
        inferred_attrs = SubjectNodeAttributes(
            credibility=current.credibility,
            correctness=_enum_from_level(Correctness, inferred_correctness_level),
            continuity=_enum_from_level(Continuity, inferred_continuity_level),
        )
        graph.nodes[subject_name] = replace(node, subject_attributes=inferred_attrs)


def build_default_system() -> System:
    graph = SystemGraph()

    subjects = [
        _subject("IntelligentSystem", "Agent", Credibility.MIXED_CREDIBILITY),
        _subject("PreprocessingModule", "Agent", Credibility.MIXED_CREDIBILITY),
        _subject("InferenceModule", "Agent", Credibility.MIXED_CREDIBILITY),
        _subject("PostprocessingModule", "Agent", Credibility.MIXED_CREDIBILITY),
        _subject("User", "Participant", Credibility.MIXED_CREDIBILITY),
        _subject("ModelDeveloper", "Participant", Credibility.TRUSTED),
        _subject("AppDeveloper", "Participant", Credibility.TRUSTED),
        _subject("Maintainer", "Participant", Credibility.MIXED_CREDIBILITY),
        _subject("DataWorker", "Participant", Credibility.MIXED_CREDIBILITY),
        _subject("OperatingEnvironment", "Participant", Credibility.MIXED_CREDIBILITY),
    ]

    objects = [
        _object("RawData", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ProcessedData", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelPretrained", "Asset", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("ModelTrained", "Asset", Confidentiality.CONFIDENTIAL),
        _object("Model", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ApplicationProgrammed", "Asset", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("Application", "Asset", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("Dependency", "Asset", Confidentiality.NON_CONFIDENTIAL),
        _object("InputQuery", "Asset", Confidentiality.CONFIDENTIAL),
        _object("InputToken", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputToken", "Asset", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("OutputMaterialized", "Asset", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("ModelHub", "Source", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("AppHub", "Source", Confidentiality.MIXED_CONFIDENTIALITY),
        _object("DependencyHub", "Source", Confidentiality.NON_CONFIDENTIAL),
    ]

    for node in subjects + objects:
        graph.add_node(node)

    # Core SSA and structural edges based on the document.
    # Each operation has: input(s) as ACTED_ON_BY, output as ACT
    edge_specs = [
        ("RawData", "DataWorker", EdgeType.ACTED_ON_BY, "1.Process"),
        ("DataWorker", "ProcessedData", EdgeType.ACT, "1.Process"),
        ("ProcessedData", "ModelDeveloper", EdgeType.ACTED_ON_BY, "2.Train"),
        ("ModelPretrained", "ModelDeveloper", EdgeType.ACTED_ON_BY, "2.Train"),
        ("ModelDeveloper", "ModelTrained", EdgeType.ACT, "2.Train"),
        ("ModelTrained", "ModelDeveloper", EdgeType.ACTED_ON_BY, "3.Upload"),
        ("ModelDeveloper", "ModelHub", EdgeType.ACT, "3.Upload"),
        ("ModelHub", "Maintainer", EdgeType.ACTED_ON_BY, "4.Download"),
        ("Maintainer", "Model", EdgeType.ACT, "4.Download"),
        ("AppDeveloper", "ApplicationProgrammed", EdgeType.ACT, "5.Program"),
        ("ApplicationProgrammed", "AppDeveloper", EdgeType.ACTED_ON_BY, "6.Upload"),
        ("AppDeveloper", "AppHub", EdgeType.ACT, "6.Upload"),
        ("AppHub", "Maintainer", EdgeType.ACTED_ON_BY, "7.Download"),
        ("Maintainer", "Application", EdgeType.ACT, "7.Download"),
        ("DependencyHub", "Maintainer", EdgeType.ACTED_ON_BY, "8.Download"),
        ("Maintainer", "Dependency", EdgeType.ACT, "8.Download"),
        ("Model", "Maintainer", EdgeType.ACTED_ON_BY, "9.Assemble"),
        ("Application", "Maintainer", EdgeType.ACTED_ON_BY, "9.Assemble"),
        ("Dependency", "Maintainer", EdgeType.ACTED_ON_BY, "9.Assemble"),
        ("Maintainer", "IntelligentSystem", EdgeType.ACT, "9.Assemble"),
        ("User", "InputQuery", EdgeType.ACT, "10.Propose"),
        ("InputQuery", "PreprocessingModule", EdgeType.ACTED_ON_BY, "11.Pre-Process"),
        ("PreprocessingModule", "InputToken", EdgeType.ACT, "11.Pre-Process"),
        ("InputToken", "InferenceModule", EdgeType.ACTED_ON_BY, "12.Inference"),
        ("InferenceModule", "OutputToken", EdgeType.ACT, "12.Inference"),
        ("OutputToken", "PostprocessingModule", EdgeType.ACTED_ON_BY, "13.Post-Process"),
        ("PostprocessingModule", "OutputMaterialized", EdgeType.ACT, "13.Post-Process"),
        ("PreprocessingModule", "IntelligentSystem", EdgeType.COMPONENT_OF, "ComponentOf"),
        ("InferenceModule", "IntelligentSystem", EdgeType.COMPONENT_OF, "ComponentOf"),
        ("PostprocessingModule", "IntelligentSystem", EdgeType.COMPONENT_OF, "ComponentOf"),
        ("IntelligentSystem", "OperatingEnvironment", EdgeType.COMPONENT_OF, "ComponentOf"),
        ("OutputMaterialized", "User", EdgeType.RESPOND, "R1.Respond"),
        ("OutputMaterialized", "OperatingEnvironment", EdgeType.RESPOND, "R2.Respond"),
        ("OperatingEnvironment", "IntelligentSystem", EdgeType.RESPOND, "R3.Respond"),
        ("User", "DataWorker", EdgeType.RESPOND, "R4.Respond"),
        ("User", "ModelDeveloper", EdgeType.RESPOND, "R5.Respond"),
        ("User", "AppDeveloper", EdgeType.RESPOND, "R6.Respond"),
        ("User", "Maintainer", EdgeType.RESPOND, "R7.Respond"),
    ]

    default_attrs = _default_edge_attrs()
    for src, tgt, e_type, name in edge_specs:
        graph.add_edge(
            Edge(
                source=src,
                target=tgt,
                type=e_type,
                name=name,
                attributes=default_attrs,
            )
        )

    dependencies = {
        "IntelligentSystem": {"Model", "Application", "Dependency"},
        "PreprocessingModule": {"Application", "Dependency"},
        "InferenceModule": {"Model", "Application", "Dependency"},
        "PostprocessingModule": {"Application", "Dependency"},
    }

    system = System(graph=graph, dependencies=dependencies)
    infer_subject_attributes_from_assets(system)
    return system
