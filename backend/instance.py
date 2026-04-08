from __future__ import annotations

"""Default system instance construction aligned with Model 2.0 docs."""

from dataclasses import replace

from .model import (
    ActionNode,
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
    classify_action_stage,
    level_to_enum_member,
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


def _action(name: str) -> ActionNode:
    return ActionNode(name=name, stage=classify_action_stage(name))


def infer_subject_attributes_from_assets(system: System) -> None:
    """Infer key subject correctness/continuity from dependency assets.

    Rules (correctness/continuity upper-bounded by dependent assets):
    - InferenceModule <= Model, Application, Dependency
    - PreprocessingModule <= Application, Dependency
    - InferenceModule <= Model, Application, Dependency
    - PostprocessingModule <= Application, Dependency
    """
    graph = system.graph
    infer_targets = {
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
            correctness=level_to_enum_member(Correctness, inferred_correctness_level),
            continuity=level_to_enum_member(Continuity, inferred_continuity_level),
        )
        graph.nodes[subject_name] = replace(node, subject_attributes=inferred_attrs)


def build_default_system() -> System:
    graph = SystemGraph()

    subjects = [
        _subject("DataWorkers", "Participant", Credibility.TRUSTED),
        _subject("ModelDevelopers", "Participant", Credibility.TRUSTED),
        _subject("ModelHub", "Source", Credibility.TRUSTED),
        _subject("Maintainers", "Participant", Credibility.TRUSTED),
        _subject("AppDevelopers", "Participant", Credibility.TRUSTED),
        _subject("AppHub", "Source", Credibility.TRUSTED),
        _subject("DependencyDevelopers", "Participant", Credibility.TRUSTED),
        _subject("DependencyHub", "Source", Credibility.TRUSTED),
        _subject("PreprocessingModule", "Agent", Credibility.TRUSTED),
        _subject("InferenceModule", "Agent", Credibility.TRUSTED),
        _subject("PostprocessingModule", "Agent", Credibility.TRUSTED),
        _subject("Users", "Participant", Credibility.TRUSTED),
        _subject("OutsideEnv", "Participant", Credibility.TRUSTED),
    ]

    objects = [
        _object("RawDataO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("UnstructuredDataI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("UnstructuredDataO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ProcessedDataI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelMaterialO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelToBeUploadI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelToBeUploadO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelUploadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelUploadedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelDownloadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("PretrainedModelDownloadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("PretrainedModelDownloadedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("RawDataP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelSpecP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("PretrainedModelDeclarationP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppSpecO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppProgrammedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppProgrammedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppUploadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppUploadedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppDownloadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppSpecP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("DependencyProgrammedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("DependenciesUploadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("DependenciesUploadedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("DependenciesDownloadedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("DependencyProgrammedP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("DependencyDeclarationI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OperatingEnvP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppAndDepO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelAppAndDepO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("AppAndDepI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ModelAppAndDepI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ProposalP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("ProposalMaterializedP", "Asset", Confidentiality.CONFIDENTIAL),
        _object("InputO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("InputMaterializedO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("InputI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("InputTokensO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("InputTokensI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputTokensO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputTokensI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputMaterializedI", "Asset", Confidentiality.CONFIDENTIAL),
        _object("OutputFeedbackO", "Asset", Confidentiality.CONFIDENTIAL),
        _object("FeedbackI", "Asset", Confidentiality.CONFIDENTIAL),
    ]

    for node in subjects + objects:
        graph.add_node(node)

    for action_name in [
        "M0.Initialize",
        "M1.Collection",
        "M2.Process",
        "M3.Download",
        "M4.Train",
        "M5.Upload",
        "M6.Download",
        "A0.Initialize",
        "A1.Program",
        "A2.Upload",
        "A3.Download",
        "P0.Initialize",
        "P1.Upload",
        "P2.Download",
        "D0.Initialize",
        "D1.Delopy",
        "D2.Delopy",
        "D3.Delopy",
        "O0.Initialize",
        "O1.Input",
        "O2.Preprocess",
        "O3.Infer",
        "O4.Postprocess",
        "F1.Feedback",
    ]:
        graph.add_action(_action(action_name))

    # Full Model 2.0 arc catalog: (object_name, src, dst)
    # where src/dst are subject or action identifiers.
    arc_specs = [
        ("RawDataP", "M0.Initialize", "DataWorkers"),
        ("ModelSpecP", "M0.Initialize", "ModelDevelopers"),
        ("PretrainedModelDeclarationP", "M0.Initialize", "ModelHub"),
        ("RawDataO", "DataWorkers", "M1.Collection"),
        ("UnstructuredDataI", "M1.Collection", "DataWorkers"),
        ("UnstructuredDataO", "DataWorkers", "M2.Process"),
        ("ProcessedDataI", "M2.Process", "ModelDevelopers"),
        ("PretrainedModelDownloadedI", "ModelHub", "M3.Download"),
        ("PretrainedModelDownloadedO", "M3.Download", "ModelDevelopers"),
        ("ModelMaterialO", "ModelDevelopers", "M4.Train"),
        ("ModelToBeUploadI", "M4.Train", "ModelDevelopers"),
        ("ModelToBeUploadO", "ModelDevelopers", "M5.Upload"),
        ("ModelUploadedI", "M5.Upload", "ModelHub"),
        ("ModelUploadedO", "ModelHub", "M6.Download"),
        ("ModelDownloadedI", "M6.Download", "Maintainers"),
        ("AppSpecP", "A0.Initialize", "AppDevelopers"),
        ("AppSpecO", "AppDevelopers", "A1.Program"),
        ("AppProgrammedI", "A1.Program", "AppDevelopers"),
        ("AppProgrammedO", "AppDevelopers", "A2.Upload"),
        ("AppUploadedI", "A2.Upload", "AppHub"),
        ("AppUploadedO", "AppHub", "A3.Download"),
        ("AppDownloadedI", "A3.Download", "Maintainers"),
        ("DependencyProgrammedP", "P0.Initialize", "DependencyDevelopers"),
        ("DependencyProgrammedO", "DependencyDevelopers", "P1.Upload"),
        ("DependenciesUploadedI", "P1.Upload", "DependencyHub"),
        ("DependenciesUploadedO", "DependencyHub", "P2.Download"),
        ("DependenciesDownloadedI", "P2.Download", "Maintainers"),
        ("DependencyDeclarationI", "A1.Program", "DependencyHub"),
        ("OperatingEnvP", "D0.Initialize", "Maintainers"),
        ("AppAndDepO", "Maintainers", "D1.Delopy"),
        ("ModelAppAndDepO", "Maintainers", "D2.Delopy"),
        ("AppAndDepO", "Maintainers", "D3.Delopy"),
        ("AppAndDepI", "D1.Delopy", "PreprocessingModule"),
        ("ModelAppAndDepI", "D2.Delopy", "InferenceModule"),
        ("AppAndDepI", "D3.Delopy", "PostprocessingModule"),
        ("ProposalP", "O0.Initialize", "Users"),
        ("ProposalMaterializedP", "O0.Initialize", "OutsideEnv"),
        ("InputO", "Users", "O1.Input"),
        ("InputMaterializedO", "OutsideEnv", "O1.Input"),
        ("InputI", "O1.Input", "PreprocessingModule"),
        ("InputTokensO", "PreprocessingModule", "O2.Preprocess"),
        ("InputTokensI", "O2.Preprocess", "InferenceModule"),
        ("OutputTokensO", "InferenceModule", "O3.Infer"),
        ("OutputTokensI", "O3.Infer", "PostprocessingModule"),
        ("OutputO", "PostprocessingModule", "O4.Postprocess"),
        ("OutputI", "O4.Postprocess", "Users"),
        ("OutputMaterializedI", "O4.Postprocess", "OutsideEnv"),
        ("OutputFeedbackO", "Users", "F1.Feedback"),
        ("FeedbackI", "F1.Feedback", "ModelDevelopers"),
        ("FeedbackI", "F1.Feedback", "AppDevelopers"),
        ("FeedbackI", "F1.Feedback", "DependencyDevelopers"),
        ("FeedbackI", "F1.Feedback", "Maintainers"),
    ]

    default_attrs = _default_edge_attrs()
    subject_names = {node.name for node in subjects}
    for object_name, src, dst in arc_specs:
        if src in subject_names:
            source_name = src
            target_name = object_name
            action_name = dst
        elif dst in subject_names:
            source_name = object_name
            target_name = dst
            action_name = src
        else:
            raise ValueError(f"Invalid arc endpoints for object {object_name}: src={src}, dst={dst}")

        graph.add_edge(
            Edge(
                source=source_name,
                target=target_name,
                type=EdgeType.OBJECT_ARC,
                name=object_name,
                action=action_name,
                attributes=default_attrs,
            )
        )

    dependencies = {
        "PreprocessingModule": {"AppAndDepI"},
        "InferenceModule": {"ModelAppAndDepI"},
        "PostprocessingModule": {"AppAndDepI"},
    }

    system = System(graph=graph, dependencies=dependencies)
    infer_subject_attributes_from_assets(system)
    return system
