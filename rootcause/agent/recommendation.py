from rootcause.llm import chat

RECOMMENDATION_SYSTEM = (
    "You are ROOTCAUSE, an environmental and biodiversity advisory assistant. You reason across soil "
    "health, land use, biodiversity, climate, and human impact.\n"
    "Given retrieved source excerpts, correlation classifications of the user's site conditions, and the "
    "conversation so far, draft ONE recommendation.\n"
    "Your recommendation MUST:\n"
    "- Name a specific action.\n"
    "- Explain the mechanism connecting at least two environmental variables (e.g. 'X increases Y, which increases Z').\n"
    "- State which metric improves and over what time horizon.\n"
    "- Cite the source(s) you drew on, using the citation string given with each retrieved excerpt.\n"
    "Be concise, 150-250 words. Do not fabricate a citation that is not present in the retrieved excerpts, "
    "and do not claim an effect the retrieved excerpts do not support."
)


def _build_user_prompt(user_text: str, retrieved: list[dict], correlations: list[dict], known_variables: dict) -> str:
    context_lines = [f"[{r['domain']}] {r['text']}\nCitation: {r['citation']}" for r in retrieved]
    correlation_lines = [
        f"- {c['variable']} = {c['value']} {c['unit']}: classified as '{c['label']}' — {c['note']}"
        for c in correlations
    ]
    return (
        f"User message: {user_text}\n\n"
        f"Known site variables: {known_variables}\n\n"
        "Correlation classifications:\n" + ("\n".join(correlation_lines) or "None available") + "\n\n"
        "Retrieved source excerpts:\n" + ("\n\n".join(context_lines) or "None retrieved")
    )


def draft_recommendation(
    user_text: str,
    retrieved: list[dict],
    correlations: list[dict],
    known_variables: dict,
    history: list[dict],
    revision_note: str | None = None,
) -> str:
    prompt = _build_user_prompt(user_text, retrieved, correlations, known_variables)
    if revision_note:
        prompt += f"\n\nYour previous draft was rejected by the causal consistency checker: {revision_note}\nRevise the recommendation to avoid that invalid step, using only relationships supported by the retrieved excerpts."
    messages = history + [{"role": "user", "content": prompt}]
    return chat(messages, system=RECOMMENDATION_SYSTEM, max_tokens=4096)
