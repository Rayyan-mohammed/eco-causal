from dataclasses import dataclass, field

from rootcause.causal.graph import CausalGraph, EdgeCheckResult


@dataclass
class CheckerVerdict:
    status: str  # "accepted" | "downgraded" | "rejected"
    confidence: str  # "high" | "medium" | "low"
    edge_results: list[EdgeCheckResult] = field(default_factory=list)
    explanation: str = ""


def check_chain(chain: list[tuple[str, str]], graph: CausalGraph, context: dict) -> CheckerVerdict:
    """Validates an extracted cause -> effect chain against the causal map.

    Checks, in order: (1) does each edge exist at all, (2) does its direction
    match the map, (3) is any attached condition satisfied by the supplied
    context. A failure at (1)/(2) rejects the chain; a failure at (3) downgrades
    it rather than rejecting outright, since the relationship itself is still
    documented — only its applicability here is in question.
    """
    if not chain:
        return CheckerVerdict(
            status="rejected",
            confidence="low",
            explanation="No checkable causal chain could be extracted from the recommendation.",
        )

    results = [graph.check_edge(source, target, context) for source, target in chain]

    missing = [r for r in results if not r.exists]
    failed_conditions = [r for r in results if r.exists and r.condition_satisfied is False]
    unverified_conditions = [
        r for r in results if r.exists and r.condition_satisfied is None and r.edge and r.edge.get("condition")
    ]

    if missing:
        notes = "; ".join(r.note for r in missing)
        return CheckerVerdict(
            status="rejected", confidence="low", edge_results=results,
            explanation=f"{len(missing)} step(s) in the claimed chain are not supported by the causal map in the direction claimed. {notes}",
        )

    if failed_conditions:
        notes = "; ".join(r.note for r in failed_conditions)
        return CheckerVerdict(
            status="downgraded", confidence="low", edge_results=results,
            explanation=f"The chain is directionally documented, but a required condition fails given the supplied site details. {notes}",
        )

    if unverified_conditions:
        notes = "; ".join(r.note for r in unverified_conditions)
        return CheckerVerdict(
            status="downgraded", confidence="medium", edge_results=results,
            explanation=f"The chain is documented, but at least one attached condition could not be verified from the information given. {notes}",
        )

    return CheckerVerdict(
        status="accepted", confidence="high", edge_results=results,
        explanation="Every step in the chain is documented in the causal map in the correct direction, and all attached conditions are satisfied.",
    )
