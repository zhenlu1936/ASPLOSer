from __future__ import annotations

"""Unified Model 2.0 data model: core schema and projection helpers."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Type


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
    OBJECT_ARC = "ObjectArc"


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
    action: str
    attributes: EdgeAttributes


@dataclass(frozen=True)
class ActionNode:
    name: str
    stage: str


@dataclass
class SystemGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    actions: Dict[str, ActionNode] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        self.nodes[node.name] = node

    def add_action(self, action: ActionNode) -> None:
        self.actions[action.name] = action

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
    token = action_name.split(".", 1)[0]
    if token.startswith("M"):
        return "Development"
    if token.startswith(("A", "P", "D")):
        return "Deployment"
    if token.startswith("O"):
        return "Response" if action_name.startswith("O4.") else "Inference"
    if token.startswith("F"):
        return "Feedback"
    return "Other"


def classify_action_stage(action_name: str) -> str:
    """Public helper for assigning action stage names from action ids."""
    return _classify_stage(action_name)


def stage_sort_key(action_name: str) -> tuple[int, int]:
    """Stable stage-aware sort key for action identifiers."""
    stage_order = {
        "Development": 0,
        "Deployment": 1,
        "Inference": 2,
        "Response": 3,
        "Feedback": 4,
        "Other": 5,
    }
    stage = _classify_stage(action_name)
    token = action_name.split(".", 1)[0]
    numeric_suffix = token[1:] if len(token) > 1 else ""
    number = int(numeric_suffix) if numeric_suffix.isdigit() else 999
    return (stage_order.get(stage, 100), number)


def level_to_enum_member(enum_cls: Type[_LeveledEnum], level_value: int) -> _LeveledEnum:
    """Reverse-map a security level value back to its enum member."""
    for member in enum_cls:
        if member.level().value == level_value:
            return member
    raise ValueError(f"No {enum_cls.__name__} member for level={level_value}")


def are_opposite_node_types(source: Node, target: Node) -> bool:
    """Return whether endpoints are bipartite (subject-to-object or object-to-subject)."""
    return source.is_subject != target.is_subject


def is_object_to_subject_edge(edge: Edge, graph: SystemGraph) -> bool:
    source = graph.nodes[edge.source]
    target = graph.nodes[edge.target]
    return are_opposite_node_types(source, target) and (not source.is_subject) and target.is_subject


def is_subject_to_object_edge(edge: Edge, graph: SystemGraph) -> bool:
    source = graph.nodes[edge.source]
    target = graph.nodes[edge.target]
    return are_opposite_node_types(source, target) and source.is_subject and (not target.is_subject)


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

    for action in graph.actions.values():
        net.actions[action.name] = ActionNode2(
            name=action.name,
            stage=action.stage,
        )

    for edge in graph.edges:

        attrs = edge.attributes
        action_name = edge.action
        if action_name not in net.actions:
            raise ValueError(f"Edge references undefined action node: {action_name}")

        src_is_subject = edge.source in net.subjects
        tgt_is_subject = edge.target in net.subjects

        if (not src_is_subject) and tgt_is_subject:
            # object -> subject (input object consumed by action)
            net.object_arcs.append(
                ObjectArc2(
                    name=f"{action_name}:{edge.name}:in",
                    object_name=edge.name,
                    src=edge.target,
                    dst=action_name,
                    confidentiality=attrs.confidentiality,
                    correctness=attrs.correctness,
                    continuity=attrs.continuity,
                )
            )
        elif src_is_subject and (not tgt_is_subject):
            # subject -> object (output object produced by action)
            net.object_arcs.append(
                ObjectArc2(
                    name=f"{action_name}:{edge.name}:out",
                    object_name=edge.name,
                    src=action_name,
                    dst=edge.source,
                    confidentiality=attrs.confidentiality,
                    correctness=attrs.correctness,
                    continuity=attrs.continuity,
                )
            )
        else:
            # subject-subject fallbacks are mapped as action outputs to the target subject.
            subject_endpoint = edge.target if tgt_is_subject else edge.source
            if subject_endpoint in net.subjects:
                net.object_arcs.append(
                    ObjectArc2(
                        name=f"{action_name}:{edge.name}:resp",
                        object_name=edge.name,
                        src=action_name,
                        dst=subject_endpoint,
                        confidentiality=attrs.confidentiality,
                        correctness=attrs.correctness,
                        continuity=attrs.continuity,
                    )
                )

    return net
