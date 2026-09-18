import re
from typing import Literal

from pydantic import BaseModel, Field

from rootcause.llm import parse_structured


class RecommendationDraft(BaseModel):
    action: str = Field(
        description=(
            "The specific action recommended, one or two sentences. State only WHAT to do — "
            "reasoning, thresholds and caveats belong in the mechanism, not here."
        )
    )
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
        description=(
            "Expected time for the improvement to become measurable, ALWAYS as a numeric range in months "
            "or years, e.g. '3-6 months', '2-3 years'. Never a vague phrase like 'multiple seasons'."
        )
    )
    horizon: Literal["short", "medium", "long"] = Field(
        description=(
            "Classify time_horizon: short = up to 1 year, medium = over 1 up to 5 years, long = over 5 "
            "years. (The system recomputes this from time_horizon; it is only a fallback.)"
        )
    )
    expected_effect: str = Field(
        description=(
            "A measurable estimate of the improvement, using ONLY figures that appear in the retrieved "
            "excerpts, stated with the study they come from and the units/conditions they apply to "
            "(e.g. 'cover crops average ~0.32 Mg C/ha/yr of soil carbon gain (Poeplau & Don 2015)'). "
            "If no retrieved excerpt quantifies the effect, write exactly: "
            "'Not quantified in the retrieved evidence.' Never invent, round up, or extrapolate a number."
        )
    )


_UNIT_YEARS = {"month": 1 / 12, "year": 1.0}
_HORIZON_RE = re.compile(r"(\d+(?:\.\d+)?)(?:\s*(?:-|–|to)\s*(\d+(?:\.\d+)?))?\s*(month|year)s?", re.IGNORECASE)


def classify_horizon(time_horizon: str) -> str | None:
    """short / medium / long from the numeric range in the model's own
    time_horizon text, using its upper bound (the time by which the effect
    should be measurable). Deterministic on purpose: the model labels
    'multiple seasons' as 'long', which is not a judgment worth trusting.
    Returns None if no numeric range is present, so the caller can fall back."""
    match = _HORIZON_RE.search(time_horizon or "")
    if not match:
        return None
    upper = float(match.group(2) or match.group(1))
    years = upper * _UNIT_YEARS[match.group(3).lower()]
    if years <= 1:
        return "short"
    return "medium" if years <= 5 else "long"


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
    "instead of one that only works in general.\n"
    "When the user's concern is biodiversity, the mechanism must reach at least one biodiversity indicator "
    "(pollinator abundance, natural pest predator abundance, species richness, habitat connectivity, or bird "
    "diversity) and, where the excerpts support it, connect at least three variables spanning at least two "
    "domains (for example land use -> soil health -> biodiversity). Prefer an intervention that acts on "
    "several of the user's stated conditions at once over single-lever advice.\n"
    "Never invent a bridging step to reach a target indicator: every arrow in the mechanism must be a "
    "relationship the retrieved excerpts actually state. A shorter chain of documented steps is better than a "
    "longer chain that contains a guess.\n"
    "For expected_effect: if a retrieved excerpt reports a measured figure for the intervention you recommend, "
    "you MUST report it, naming the study and what it measures (a rate, a stock difference, a percentage). "
    "Only write 'Not quantified in the retrieved evidence.' when no retrieved excerpt does. Never invent a "
    "number. Use the site's own numbers to say whether a reported figure plausibly "
    "transfers (for example, a result reported for a different climate or system should be flagged as such)."
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
