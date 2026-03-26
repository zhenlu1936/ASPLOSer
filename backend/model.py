from __future__ import annotations

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
