"""Evidence gathering: how the knowledge base is queried for one turn.

Two-stage retrieval. A goal-only query ("biodiversity is declining") surfaces
passages about the *problem*; the user's real question is what to *do*. So the
model first proposes a few candidate interventions for these specific
conditions, and each is retrieved against as well. Results are merged and
de-duplicated, and a trace of what was asked and found is returned so the
pipeline's retrieval step is visible rather than a black box.
"""

from pydantic import BaseModel, Field

from rootcause.agent.tools import get_knowledge_store, site_descriptors
from rootcause.llm import parse_structured

BASE_RESULTS = 4
PER_INTERVENTION = 3
MAX_INTERVENTIONS = 3
MAX_CHUNKS = 8


class InterventionPlan(BaseModel):
    interventions: list[str] = Field(
        description=(
            "2 or 3 distinct candidate interventions, each a short noun phrase, e.g. "
            "'agroforestry alley cropping', 'legume intercropping', 'no-till with residue retention'."
        )
    )


_PLAN_SYSTEM = (
    "You decide what evidence an environmental advisory system should retrieve. Given the user's goal and "
    "site conditions, name 2 or 3 distinct candidate interventions that would plausibly help under THESE "
    "conditions (climate, soil carbon, land use). Include at least one that is not the most obvious choice. "
    "Do not propose an intervention that would clearly fail under the stated conditions (for example a "
    "water-intensive one on an arid site). Prefer interventions the knowledge base has evidence about "
    "(its topic list is provided); an intervention with no evidence behind it cannot be recommended."
)


def _kb_topics() -> list[str]:
    """Section titles of the indexed knowledge base — the vocabulary the planner
    should plan against, so it proposes interventions the evidence can speak to."""
    ids = get_knowledge_store().collection.get()["ids"]
    return sorted({chunk_id.split("::", 1)[-1] for chunk_id in ids})


def plan_interventions(concern: str | None, known_variables: dict, fallback: str) -> list[str]:
    """Candidate interventions to retrieve evidence for. Returns [] if planning
    fails, in which case retrieval degrades gracefully to the base query alone
    rather than failing the whole turn."""
    try:
        plan = parse_structured(
            [{
                "role": "user",
                "content": (
                    f"Goal: {concern or fallback}\nSite variables: {known_variables}\n"
                    f"Knowledge base topics: {'; '.join(_kb_topics())}"
                ),
            }],
            InterventionPlan,
            system=_PLAN_SYSTEM,
            max_tokens=500,
        )
    except Exception:
        return []
    return [i.strip() for i in plan.interventions if i.strip()][:MAX_INTERVENTIONS]


def _title(hit: dict) -> str:
    return hit["text"].split("\n", 1)[0]


def gather_evidence(concern: str | None, known_variables: dict, fallback: str) -> tuple[list[dict], dict]:
    """Returns (retrieved passages, trace of how they were found)."""
    store = get_knowledge_store()
    descriptors = site_descriptors(known_variables)
    base_query = ". ".join([concern or fallback, *descriptors])
    interventions = plan_interventions(concern, known_variables, fallback)

    queries = [base_query]
    merged: dict[str, dict] = {}

    def add(hits: list[dict]) -> None:
        for hit in hits:
            current = merged.get(hit["id"])
            if current is None or hit["distance"] < current["distance"]:
                merged[hit["id"]] = hit

    add(store.query(base_query, n_results=BASE_RESULTS))
    for intervention in interventions:
        query = ". ".join([intervention, *descriptors])
        queries.append(query)
        add(store.query(query, n_results=PER_INTERVENTION))

    retrieved = sorted(merged.values(), key=lambda h: h["distance"])[:MAX_CHUNKS]
    trace = {
        "interventions": interventions,
        "queries": queries,
        "passages": [
            {"title": _title(h), "domain": h["domain"], "distance": round(h["distance"], 3)} for h in retrieved
        ],
    }
    return retrieved, trace
