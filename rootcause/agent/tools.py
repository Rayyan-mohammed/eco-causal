import json

from rootcause.config import REFERENCE_RANGES_PATH
from rootcause.knowledge.vectorstore import KnowledgeStore

_store: KnowledgeStore | None = None
_reference_ranges: dict | None = None


def get_knowledge_store() -> KnowledgeStore:
    global _store
    if _store is None:
        _store = KnowledgeStore()
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


def correlate(known_variables: dict) -> list[dict]:
    results = []
    for variable, value in known_variables.items():
        if isinstance(value, (int, float)):
            classification = classify_value(variable, value)
            if classification:
                results.append(classification)
    return results
