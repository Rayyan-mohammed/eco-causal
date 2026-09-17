from rootcause.agent.checker import CheckerVerdict
from rootcause.agent.recommendation import RecommendationDraft

_STATUS_NOTES = {
    "accepted": "This recommendation's causal reasoning was checked against the sourced causal map and fully supported.",
    "downgraded": "Confidence lowered by the Causal Consistency Checker: {explanation}",
    "rejected": "This recommendation was rejected by the Causal Consistency Checker: {explanation}",
}


def format_response(draft: RecommendationDraft, verdict: CheckerVerdict, retrieved: list[dict]) -> dict:
    """Assembles the challenge's required output shape: recommendation,
    impacted metrics, time horizon, confidence level, and citation — as
    separate structured fields, not just prose the caller has to re-parse."""
    citations = sorted({r["citation"] for r in retrieved if r.get("citation") and r["citation"] != "Uncited"})

    note = _STATUS_NOTES[verdict.status].format(explanation=verdict.explanation)
    text = f"{draft.action}\n\n{draft.mechanism}"
    if verdict.status != "accepted":
        text += f"\n\n[Consistency check: {verdict.status}, confidence: {verdict.confidence}] {note}"

    return {
        "text": text,
        "action": draft.action,
        "mechanism": draft.mechanism,
        "impacted_metrics": draft.impacted_metrics,
        "time_horizon": draft.time_horizon,
        "confidence": verdict.confidence,
        "checker_status": verdict.status,
        "checker_explanation": verdict.explanation,
        "citations": citations,
    }
