from pydantic import BaseModel, Field

from rootcause.llm import parse_structured


class RecommendationDraft(BaseModel):
    action: str = Field(description="The specific action recommended, one or two sentences.")
    mechanism: str = Field(
        description=(
            "Prose explanation of the causal mechanism connecting at least two environmental "
            "variables, in the form 'X increases Y, which increases Z'. Name the variables "
            "explicitly and don't hedge — this text is what gets checked against the causal map."
        )
    )
    impacted_metrics: list[str] = Field(
        description="The environmental metrics/variables expected to improve, in plain language (e.g. 'pollinator abundance', 'soil organic carbon')."
    )
    time_horizon: str = Field(
        description="Expected time horizon for the improvement to become measurable, e.g. '3-6 months', '1-2 years'."
    )


RECOMMENDATION_SYSTEM = (
    "You are ROOTCAUSE, an environmental and biodiversity advisory assistant. You reason across soil "
    "health, land use, biodiversity, climate, and human impact.\n"
    "Given retrieved source excerpts, correlation classifications of the user's site conditions, and the "
    "conversation so far, produce ONE recommendation as structured output.\n"
    "Ground the mechanism you describe in the retrieved excerpts — do not claim an effect the excerpts "
    "do not support. Name the environmental variables explicitly in the mechanism field (e.g. 'agroforestry "
    "adoption increases soil moisture retention, which supports pollinator abundance') so the causal chain "
    "can be verified against the sourced map.\n"
    "Before finalizing, check any numeric threshold or condition mentioned in the retrieved excerpts "
    "(a rainfall cutoff, a pH threshold, a climate band, etc.) against the 'Known site variables' given "
    "to you. If the site's actual values fall outside a condition a mechanism depends on, that mechanism "
    "will fail verification — choose a different intervention that actually fits this site's real numbers "
    "instead of one that only works in general."
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
) -> RecommendationDraft:
    prompt = _build_user_prompt(user_text, retrieved, correlations, known_variables)
    if revision_note:
        prompt += f"\n\nYour previous draft was rejected by the causal consistency checker: {revision_note}\nRevise the recommendation to avoid that invalid step, using only relationships supported by the retrieved excerpts."
    messages = history + [{"role": "user", "content": prompt}]
    return parse_structured(
        messages, RecommendationDraft, system=RECOMMENDATION_SYSTEM, max_tokens=3000, disable_thinking=False
    )
