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


def _asset(name: str) -> Node:
    return _object(name, "Asset", Confidentiality.CONFIDENTIAL)


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
        _subject("User", "Participant", Credibility.TRUSTED),
        _subject("ExternalEnv", "Participant", Credibility.TRUSTED),
    ]

    asset_names = [
        "RawDataO",
        "UnstructuredDataI",
        "UnstructuredDataO",
        "ProcessedDataI",
        "ModelMaterialO",
        "ModelToBeUploadI",
        "ModelToBeUploadO",
        "ModelUploadedI",
        "ModelUploadedO",
        "ModelDownloadedI",
        "PretrainedModelDownloadedI",
        "PretrainedModelDownloadedO",
        "RawDataP",
        "ModelSpecP",
        "PretrainedModelDeclarationP",
        "AppSpecO",
        "AppProgrammedI",
        "AppProgrammedO",
        "AppUploadedI",
        "AppUploadedO",
        "AppDownloadedI",
        "AppSpecP",
        "DependencyProgrammedO",
        "DependenciesUploadedI",
        "DependenciesUploadedO",
        "DependenciesDownloadedI",
        "DependencyProgrammedP",
        "DependencyDeclarationI",
        "OperatingEnvP",
        "AppAndDepO",
        "ModelAppAndDepO",
        "AppAndDepI",
        "ModelAppAndDepI",
        "ProposalP",
        "ProposalMaterializedP",
        "InputUserO",
        "InputEnvI",
        "InputEnvO",
        "InputI",
        "InputTokensO",
        "InputTokensI",
        "OutputTokensO",
        "OutputTokensI",
        "OutputEnvO",
        "OutputEnvI",
        "OutputUserO",
        "OutputUserI",
        "Feedback",
    ]
    objects = [_asset(name) for name in asset_names]

    for node in subjects + objects:
        graph.add_node(node)

    for action_name in [
        "M01.Initialize",
        "M02.Initialize",
        "M03.Initialize",
        "M1.Collection",
        "M2.Process",
        "M3.Download",
        "M4.Train",
        "M5.Upload",
        "M6.Download",
        "A01.Initialize",
        "A1.Program",
        "A2.Upload",
        "A3.Download",
        "P01.Initialize",
        "P1.Upload",
        "P2.Download",
        "D01.Initialize",
        "D1.Deploy",
        "D2.Deploy",
        "D3.Deploy",
        "O01.Initialize",
        "O02.Initialize",
        "O1.InputUser",
        "O2.InputEnv",
        "O3.Preprocess",
        "O4.Infer",
        "O5.PostprocessEnv",
        "O6.PostprocessUser",
        "MF1.Feedback",
        "MF2.Feedback",
        "MF3.Feedback",
        "AF1.Feedback",
        "AF2.Feedback",
        "PF1.Feedback",
        "PF2.Feedback",
        "DF1.Feedback",
        "OF1.Feedback",
        "OF2.Feedback",
        "OF3.Feedback",
        "OF4.Feedback",
    ]:
        graph.add_action(_action(action_name))

    # Full Model 2.0 arc catalog: (object_name, src, dst)
    # where src/dst are subject or action identifiers.
    arc_specs = [
        # M arcs
        ("RawDataP", "M01.Initialize", "DataWorkers"),
        ("ModelSpecP", "M02.Initialize", "ModelDevelopers"),
        ("PretrainedModelDeclarationP", "M03.Initialize", "ModelHub"),
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
        # A arcs
        ("AppSpecP", "A01.Initialize", "AppDevelopers"),
        ("AppSpecO", "AppDevelopers", "A1.Program"),
        ("AppProgrammedI", "A1.Program", "AppDevelopers"),
        ("AppProgrammedO", "AppDevelopers", "A2.Upload"),
        ("AppUploadedI", "A2.Upload", "AppHub"),
        ("AppUploadedO", "AppHub", "A3.Download"),
        ("AppDownloadedI", "A3.Download", "Maintainers"),
        ("DependencyDeclarationI", "A1.Program", "DependencyHub"),
        # P arcs
        ("DependencyProgrammedP", "P01.Initialize", "DependencyDevelopers"),
        ("DependencyProgrammedO", "DependencyDevelopers", "P1.Upload"),
        ("DependenciesUploadedI", "P1.Upload", "DependencyHub"),
        ("DependenciesUploadedO", "DependencyHub", "P2.Download"),
        ("DependenciesDownloadedI", "P2.Download", "Maintainers"),
        # D arcs
        ("OperatingEnvP", "D01.Initialize", "Maintainers"),
        ("AppAndDepO", "Maintainers", "D1.Deploy"),
        ("ModelAppAndDepO", "Maintainers", "D2.Deploy"),
        ("AppAndDepO", "Maintainers", "D3.Deploy"),
        ("AppAndDepI", "D1.Deploy", "PreprocessingModule"),
        ("ModelAppAndDepI", "D2.Deploy", "InferenceModule"),
        ("AppAndDepI", "D3.Deploy", "PostprocessingModule"),
        # O arcs
        ("ProposalMaterializedP", "O01.Initialize", "ExternalEnv"),
        ("ProposalP", "O02.Initialize", "User"),
        ("InputUserO", "User", "O1.InputUser"),
        ("InputEnvI", "O1.InputUser", "ExternalEnv"),
        ("InputEnvO", "ExternalEnv", "O2.InputEnv"),
        ("InputI", "O2.InputEnv", "PreprocessingModule"),
        ("InputTokensO", "PreprocessingModule", "O3.Preprocess"),
        ("InputTokensI", "O3.Preprocess", "InferenceModule"),
        ("OutputTokensO", "InferenceModule", "O4.Infer"),
        ("OutputTokensI", "O4.Infer", "PostprocessingModule"),
        ("OutputEnvO", "PostprocessingModule", "O5.PostprocessEnv"),
        ("OutputEnvI", "O5.PostprocessEnv", "ExternalEnv"),
        ("OutputUserO", "PostprocessingModule", "O6.PostprocessUser"),
        ("OutputUserI", "O6.PostprocessUser", "User"),
        # Feedback arcs (bidirectional per subprocess, except OF4 is unidirectional)
        ("Feedback", "DataWorkers", "MF1.Feedback"),
        ("Feedback", "MF1.Feedback", "DataWorkers"),
        ("Feedback", "ModelDevelopers", "MF2.Feedback"),
        ("Feedback", "MF2.Feedback", "ModelDevelopers"),
        ("Feedback", "ModelHub", "MF3.Feedback"),
        ("Feedback", "MF3.Feedback", "ModelHub"),
        ("Feedback", "AppDevelopers", "AF1.Feedback"),
        ("Feedback", "AF1.Feedback", "AppDevelopers"),
        ("Feedback", "AppHub", "AF2.Feedback"),
        ("Feedback", "AF2.Feedback", "AppHub"),
        ("Feedback", "DependencyDevelopers", "PF1.Feedback"),
        ("Feedback", "PF1.Feedback", "DependencyDevelopers"),
        ("Feedback", "DependencyHub", "PF2.Feedback"),
        ("Feedback", "PF2.Feedback", "DependencyHub"),
        ("Feedback", "Maintainers", "DF1.Feedback"),
        ("Feedback", "DF1.Feedback", "Maintainers"),
        ("Feedback", "PreprocessingModule", "OF1.Feedback"),
        ("Feedback", "OF1.Feedback", "PreprocessingModule"),
        ("Feedback", "InferenceModule", "OF2.Feedback"),
        ("Feedback", "OF2.Feedback", "InferenceModule"),
        ("Feedback", "PostprocessingModule", "OF3.Feedback"),
        ("Feedback", "OF3.Feedback", "PostprocessingModule"),
        ("Feedback", "User", "OF4.Feedback"),
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

    # Encode the canonical mapping from pipeline module subjects to the
    # operation action they drive.  Used for module-action attribute
    # inheritance analysis and GIF frame annotation.
    module_action_map = {
        "PreprocessingModule": "O3.Preprocess",
        "InferenceModule": "O4.Infer",
        "PostprocessingModule": "O5.PostprocessEnv",
    }

    system = System(graph=graph, dependencies=dependencies,
                    module_action_map=module_action_map)
    infer_subject_attributes_from_assets(system)
    return system
