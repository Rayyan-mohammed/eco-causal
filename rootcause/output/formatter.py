from rootcause.agent.checker import CheckerVerdict

_STATUS_NOTES = {
    "accepted": "This recommendation's causal reasoning was checked against the sourced causal map and fully supported.",
    "downgraded": "Confidence lowered by the Causal Consistency Checker: {explanation}",
    "rejected": "This recommendation was rejected by the Causal Consistency Checker: {explanation}",
}


def format_response(draft_text: str, verdict: CheckerVerdict, retrieved: list[dict]) -> dict:
    citations = sorted({r["citation"] for r in retrieved if r.get("citation") and r["citation"] != "Uncited"})

    note = _STATUS_NOTES[verdict.status].format(explanation=verdict.explanation)
    text = draft_text
    if verdict.status != "accepted":
        text += f"\n\n[Consistency check: {verdict.status}, confidence: {verdict.confidence}] {note}"

    return {
        "text": text,
        "recommendation": draft_text,
        "confidence": verdict.confidence,
        "checker_status": verdict.status,
        "checker_explanation": verdict.explanation,
        "citations": citations,
    }
