import json

from rootcause.config import REFERENCE_RANGES_PATH
from rootcause.knowledge.vectorstore import KnowledgeStore

_store: KnowledgeStore | None = None
_reference_ranges: dict | None = None


def get_knowledge_store() -> KnowledgeStore:
    global _store
    if _store is None:
        _store = KnowledgeStore()
        if _store.count() == 0:
            # First run against a fresh chroma_db (e.g. a new cloud deploy,
            # where chroma_db/ is gitignored and doesn't exist yet) — build
            # the index automatically instead of requiring a manual step.
            _store.build_index()
    return _store


def retrieve(query: str, n_results: int = 4, domain: str | None = None) -> list[dict]:
    return get_knowledge_store().query(query, n_results=n_results, domain=domain)


def _load_reference_ranges() -> dict:
    global _reference_ranges
    if _reference_ranges is None:
        with open(REFERENCE_RANGES_PATH, encoding="utf-8") as f:
            _reference_ranges = json.load(f)["variables"]
    return _reference_ranges


def classify_value(variable: str, value: float) -> dict | None:
    """Correlation tool: maps a raw numeric input to a literature-derived band."""
    ranges = _load_reference_ranges()
    spec = ranges.get(variable)
    if not spec:
        return None
    for band in spec["bands"]:
        if value <= band["max"]:
            return {
                "variable": variable,
                "value": value,
                "unit": spec["unit"],
                "label": band["label"],
                "note": band["note"],
            }
    return None


def classify_climate_zone(latitude: float) -> dict:
    """Turns a geo-coordinate (the challenge's named bonus input) into an
    actual reasoning signal rather than an accepted-but-unused field: a rough
    latitude band with the agroclimatic implication that band carries."""
    abs_lat = abs(latitude)
    if abs_lat <= 23.5:
        zone, note = "tropical", (
            "near the equator — less seasonal temperature swing, but rainfall is often "
            "concentrated into a wet/dry season rather than spread evenly"
        )
    elif abs_lat <= 35:
        zone, note = "subtropical", (
            "subtropical latitude — prone to a pronounced dry season; don't assume "
            "moisture is ample without checking actual rainfall"
        )
    elif abs_lat <= 55:
        zone, note = "temperate", (
            "temperate latitude — typically more even year-round rainfall and stronger "
            "seasonal temperature swings than the tropics"
        )
    else:
        zone, note = "polar/subpolar", (
            "high latitude — a short growing season and seasonal extremes are usually "
            "the dominant constraint, ahead of most other factors"
        )
    return {"variable": "latitude", "value": latitude, "unit": "degrees", "label": zone, "note": note}


def correlate(known_variables: dict) -> list[dict]:
    results = []
    for variable, value in known_variables.items():
        if variable == "latitude" and isinstance(value, (int, float)):
            results.append(classify_climate_zone(value))
        elif isinstance(value, (int, float)):
            classification = classify_value(variable, value)
            if classification:
                results.append(classification)
    return results
