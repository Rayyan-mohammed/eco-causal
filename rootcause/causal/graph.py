import json
import operator as op
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import networkx as nx

_OPERATORS = {
    "gt": op.gt,
    "gte": op.ge,
    "lt": op.lt,
    "lte": op.le,
    "eq": op.eq,
}


@dataclass
class EdgeCheckResult:
    source: str
    target: str
    exists: bool
    edge: Optional[dict] = None
    condition_satisfied: Optional[bool] = None  # None = no structured condition, or not evaluable from given context
    note: str = ""


class CausalGraph:
    """Loads the expert-curated causal map and answers existence, direction,
    and condition questions about a claimed chain of variables."""

    def __init__(self, data: dict):
        self.nodes_by_id = {n["id"]: n for n in data["nodes"]}
        self.graph = nx.MultiDiGraph()
        for node in data["nodes"]:
            self.graph.add_node(node["id"], **node)
        for edge in data["edges"]:
            self.graph.add_edge(edge["source"], edge["target"], key=edge["id"], **edge)

    @classmethod
    def from_file(cls, path: Path) -> "CausalGraph":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    def node_exists(self, node_id: str) -> bool:
        return node_id in self.nodes_by_id

    def get_edges(self, source: str, target: str) -> list[dict]:
        if not self.graph.has_edge(source, target):
            return []
        return [dict(attrs) for attrs in self.graph.get_edge_data(source, target).values()]

    def edge_exists(self, source: str, target: str) -> bool:
        return self.graph.has_edge(source, target)

    def reverse_edge_exists(self, source: str, target: str) -> bool:
        """True if the relationship exists but only in the opposite direction."""
        return self.graph.has_edge(target, source)

    def check_condition(self, edge: dict, context: dict) -> Optional[bool]:
        """Returns True/False if the edge's structured condition can be evaluated
        against the given context, or None if there's no structured condition
        or the required variable wasn't supplied."""
        condition_check = edge.get("condition_check")
        if not condition_check:
            return None
        variable = condition_check["variable"]
        if variable not in context or context[variable] is None:
            return None
        operator_fn = _OPERATORS[condition_check["operator"]]
        return operator_fn(context[variable], condition_check["value"])

    def label(self, node_id: str) -> str:
        """Human-readable label for a node id, e.g. 'soil_organic_carbon' ->
        'soil organic carbon', for building explanations a non-engineer can read."""
        node = self.nodes_by_id.get(node_id)
        return node["label"].lower() if node else node_id

    def check_edge(self, source: str, target: str, context: dict) -> EdgeCheckResult:
        if not self.edge_exists(source, target):
            if self.reverse_edge_exists(source, target):
                return EdgeCheckResult(
                    source, target, exists=False,
                    note=f"the evidence I have runs the other way — {self.label(target)} affects {self.label(source)}, not the reverse.",
                )
            return EdgeCheckResult(
                source, target, exists=False,
                note=f"I don't have a documented link between {self.label(source)} and {self.label(target)}.",
            )

        edges = self.get_edges(source, target)
        # If multiple edges exist between the same pair, prefer one whose condition is satisfied.
        best_edge = edges[0]
        best_satisfied = self.check_condition(best_edge, context)
        for candidate in edges[1:]:
            satisfied = self.check_condition(candidate, context)
            if satisfied is True:
                best_edge, best_satisfied = candidate, satisfied
                break

        note = ""
        if best_satisfied is False:
            note = f"this only holds under a condition that doesn't apply here: {best_edge.get('condition') or 'unspecified condition'}."
        elif best_satisfied is None and best_edge.get("condition"):
            note = f"this depends on a condition I couldn't check from what you've told me: {best_edge['condition']}."

        return EdgeCheckResult(
            source, target, exists=True, edge=best_edge,
            condition_satisfied=best_satisfied, note=note,
        )

    def node_catalog(self) -> list[dict]:
        """Compact list for prompting the extraction step with valid variable ids."""
        return [
            {"id": n["id"], "label": n["label"], "domain": n["domain"]}
            for n in self.nodes_by_id.values()
        ]
