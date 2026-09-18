from rootcause.agent.checker import CheckerVerdict
from rootcause.agent.recommendation import RecommendationDraft


def _plain_language_note(verdict: CheckerVerdict) -> str:
    """Builds a note a non-engineer can read, using the friendly per-edge
    explanations rather than the technical `explanation` string (which stays
    precise on purpose — it's also what gets fed back to the model to fix a
    rejected draft, where exact variable names and directions help more than
    plain language would)."""
    problem_notes = [r.note for r in verdict.edge_results if r.note]
    detail = " ".join(problem_notes) if problem_notes else verdict.explanation
    if verdict.status == "downgraded":
        return f"Most of this checks out against my sourced evidence, but one part needs a caveat: {detail}"
    return f"I want to be upfront: {detail} So please treat this as unverified rather than a confident recommendation."


def format_response(draft: RecommendationDraft, verdict: CheckerVerdict, retrieved: list[dict]) -> dict:
    """Assembles the challenge's required output shape: recommendation,
    impacted metrics, time horizon, confidence level, and citation — as
    separate structured fields, not just prose the caller has to re-parse."""
    citations = sorted({r["citation"] for r in retrieved if r.get("citation") and r["citation"] != "Uncited"})

    text = f"{draft.action}\n\n{draft.mechanism}"
    if verdict.status != "accepted":
        icon = "⚠️" if verdict.status == "downgraded" else "❌"
        text += f"\n\n{icon} {_plain_language_note(verdict)}"

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
        "edge_results": verdict.edge_results,
    }
