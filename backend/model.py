from __future__ import annotations

"""Unified Model 2.0 data model: core schema and projection helpers."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class Level(Enum):
    LOW = 0
    MIXED = 1
    HIGH = 2


class _LeveledEnum(Enum):
    """Base class for enums that map to security levels."""

    def level(self) -> Level:
        return self._level_map()[self]

    @classmethod
    def _level_map(cls):
        raise NotImplementedError


class Confidentiality(_LeveledEnum):
    NON_CONFIDENTIAL = "NonConfidential"
    MIXED_CONFIDENTIALITY = "MixedConfidentiality"
    CONFIDENTIAL = "Confidential"

    @classmethod
    def _level_map(cls):
        return {
            cls.NON_CONFIDENTIAL: Level.LOW,
            cls.MIXED_CONFIDENTIALITY: Level.MIXED,
            cls.CONFIDENTIAL: Level.HIGH,
        }


class Correctness(_LeveledEnum):
    INCORRECT = "Incorrect"
    MIXED_CORRECTNESS = "MixedCorrectness"
    CORRECT = "Correct"

    @classmethod
    def _level_map(cls):
        return {
            cls.INCORRECT: Level.LOW,
            cls.MIXED_CORRECTNESS: Level.MIXED,
            cls.CORRECT: Level.HIGH,
        }


class Continuity(_LeveledEnum):
    DISCONTINUOUS = "Discontinuous"
    MIXED_CONTINUITY = "MixedContinuity"
    CONTINUOUS = "Continuous"

    @classmethod
    def _level_map(cls):
        return {
            cls.DISCONTINUOUS: Level.LOW,
            cls.MIXED_CONTINUITY: Level.MIXED,
            cls.CONTINUOUS: Level.HIGH,
        }


class Credibility(_LeveledEnum):
    UNTRUSTED = "Untrusted"
    MIXED_CREDIBILITY = "MixedCredibility"
    TRUSTED = "Trusted"

    @classmethod
    def _level_map(cls):
        return {
            cls.UNTRUSTED: Level.LOW,
            cls.MIXED_CREDIBILITY: Level.MIXED,
            cls.TRUSTED: Level.HIGH,
        }


class SubjectNodeType(Enum):
    AGENT = "Agent"
    PARTICIPANT = "Participant"


class ObjectNodeType(Enum):
    ASSET = "Asset"
    SOURCE = "Source"


class EdgeType(Enum):
    ACT = "Act"
    ACTED_ON_BY = "ActedOnBy"
    RESPOND = "Respond"
    COMPONENT_OF = "ComponentOf"


class SecurityGrade(Enum):
    LOW = "Low"
    MIXED = "Mixed"
    HIGH = "High"


@dataclass(frozen=True)
class SubjectNodeAttributes:
    credibility: Credibility
    correctness: Correctness
    continuity: Continuity


@dataclass(frozen=True)
class ObjectNodeAttributes:
    confidentiality: Confidentiality
    correctness: Correctness
    continuity: Continuity


@dataclass(frozen=True)
class EdgeAttributes:
    confidentiality: Confidentiality
    correctness: Correctness
    continuity: Continuity


@dataclass(frozen=True)
class Node:
    name: str
    is_subject: bool
    type: str
    subject_attributes: SubjectNodeAttributes | None = None
    object_attributes: ObjectNodeAttributes | None = None

    def as_subject(self) -> SubjectNodeAttributes:
        if self.subject_attributes is None:
            raise ValueError(f"Node {self.name} is not a subject.")
        return self.subject_attributes

    def as_object(self) -> ObjectNodeAttributes:
        if self.object_attributes is None:
            raise ValueError(f"Node {self.name} is not an object.")
        return self.object_attributes


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: EdgeType
    name: str
    attributes: EdgeAttributes


@dataclass
class SystemGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.source not in self.nodes:
            raise KeyError(f"Source node not found: {edge.source}")
        if edge.target not in self.nodes:
            raise KeyError(f"Target node not found: {edge.target}")
        self.edges.append(edge)

    def incoming(self, node_name: str, edge_type: EdgeType | None = None) -> List[Edge]:
        return [
            e
            for e in self.edges
            if e.target == node_name and (edge_type is None or e.type == edge_type)
        ]

    def outgoing(self, node_name: str, edge_type: EdgeType | None = None) -> List[Edge]:
        return [
            e
            for e in self.edges
            if e.source == node_name and (edge_type is None or e.type == edge_type)
        ]


@dataclass(frozen=True)
class SecurityObjectives:
    confidentiality: SecurityGrade
    integrity: SecurityGrade
    availability: SecurityGrade


@dataclass
class System:
    graph: SystemGraph
    dependencies: Dict[str, Set[str]]


@dataclass(frozen=True)
class SubjectNode2:
    name: str
    role: str
    credibility: str
    correctness: str
    continuity: str


@dataclass(frozen=True)
class ActionNode2:
    name: str
    stage: str


@dataclass(frozen=True)
class ObjectArc2:
    name: str
    object_name: str
    src: str
    dst: str
    confidentiality: Confidentiality
    correctness: Correctness
    continuity: Continuity


@dataclass
class ObjectArcPetriNet2:
    subjects: Dict[str, SubjectNode2] = field(default_factory=dict)
    actions: Dict[str, ActionNode2] = field(default_factory=dict)
    object_arcs: List[ObjectArc2] = field(default_factory=list)


def _classify_stage(action_name: str) -> str:
    if action_name.startswith("R"):
        if action_name in {"R1.Respond", "R2.Respond", "R3.Respond"}:
            return "Response"
        return "Feedback"
    try:
        prefix = int(action_name.split(".")[0])
    except (ValueError, IndexError):
        return "Other"
    if 1 <= prefix <= 3:
        return "Development"
    if 4 <= prefix <= 9:
        return "Deployment"
    if 10 <= prefix <= 13:
        return "Inference"
    return "Other"


def project_system_to_model2(system: System) -> ObjectArcPetriNet2:
    """Project graph into Model 2.0 shape: subjects + actions + object-arcs.

    This projection enforces one arc type (object arc) and a bipartite endpoint rule
    between subject and action nodes.
    """
    graph = system.graph
    net = ObjectArcPetriNet2()

    for node in graph.nodes.values():
        if not node.is_subject:
            continue
        s = node.as_subject()
        net.subjects[node.name] = SubjectNode2(
            name=node.name,
            role=node.type,
            credibility=s.credibility.value,
            correctness=s.correctness.value,
            continuity=s.continuity.value,
        )

    for edge in graph.edges:
        if edge.name == "ComponentOf":
            continue
        if edge.name not in net.actions:
            net.actions[edge.name] = ActionNode2(
                name=edge.name,
                stage=_classify_stage(edge.name),
            )

    for edge in graph.edges:
        if edge.name == "ComponentOf":
            continue

        attrs = edge.attributes
        action_name = edge.name

        if edge.type == EdgeType.ACTED_ON_BY:
            # object -> subject (input object consumed by action)
            if edge.target in net.subjects:
                net.object_arcs.append(
                    ObjectArc2(
                        name=f"{action_name}:{edge.source}:in",
                        object_name=edge.source,
                        src=edge.target,
                        dst=action_name,
                        confidentiality=attrs.confidentiality,
                        correctness=attrs.correctness,
                        continuity=attrs.continuity,
                    )
                )

        elif edge.type == EdgeType.ACT:
            # subject -> object (output object produced by action)
            if edge.source in net.subjects:
                net.object_arcs.append(
                    ObjectArc2(
                        name=f"{action_name}:{edge.target}:out",
                        object_name=edge.target,
                        src=action_name,
                        dst=edge.source,
                        confidentiality=attrs.confidentiality,
                        correctness=attrs.correctness,
                        continuity=attrs.continuity,
                    )
                )

        elif edge.type == EdgeType.RESPOND:
            # response object-flow represented as a single object arc
            subject_endpoint = edge.target if edge.target in net.subjects else edge.source
            if subject_endpoint in net.subjects:
                obj_name = edge.source if edge.source not in net.subjects else edge.target
                net.object_arcs.append(
                    ObjectArc2(
                        name=f"{action_name}:{obj_name}:resp",
                        object_name=obj_name,
                        src=action_name,
                        dst=subject_endpoint,
                        confidentiality=attrs.confidentiality,
                        correctness=attrs.correctness,
                        continuity=attrs.continuity,
                    )
                )

    return net
