import pytest

from rootcause.knowledge.vectorstore import KnowledgeStore


@pytest.fixture(scope="module")
def store():
    s = KnowledgeStore()
    s.build_index(rebuild=True)
    return s


def test_index_has_chunks_from_all_domains(store):
    assert store.count() >= 25


def test_query_returns_relevant_semi_arid_chunk(store):
    results = store.query("cover crop in a semi-arid low rainfall region", n_results=3)
    assert len(results) == 3
    domains = {r["domain"] for r in results}
    assert "climate" in domains or "soil_health" in domains
    all_text = " ".join(r["text"].lower() for r in results)
    assert "semi-arid" in all_text or "rainfall" in all_text


def test_results_carry_citations(store):
    results = store.query("pollinator decline from pesticide use", n_results=2)
    for r in results:
        assert r["citation"] != "Uncited"


def test_gather_evidence_merges_intervention_queries_and_survives_planner_failure(store, monkeypatch):
    """Retrieval is two-stage: base query + one query per candidate intervention,
    merged and de-duplicated. If the planning call fails, the turn must still
    retrieve (degrading to the base query), not fail."""
    from rootcause.agent import retrieval

    site = {"land_use": "monoculture wheat", "rainfall_level": 450, "soil_organic_carbon": 0.3}
    real_plan = retrieval.plan_interventions

    monkeypatch.setattr(retrieval, "plan_interventions", lambda *a, **k: ["agroforestry alley cropping"])
    retrieved, trace = retrieval.gather_evidence("biodiversity is declining", site, fallback="")
    ids = [h["id"] for h in retrieved]
    assert len(ids) == len(set(ids)), "merged results must be de-duplicated"
    assert len(retrieved) <= retrieval.MAX_CHUNKS
    assert trace["interventions"] == ["agroforestry alley cropping"]
    assert len(trace["queries"]) == 2
    assert any("Shi, Feng, Xu" in h["citation"] for h in retrieved), trace["passages"]

    def boom(*a, **k):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(retrieval, "plan_interventions", real_plan)  # real planner, failing model call
    monkeypatch.setattr(retrieval, "parse_structured", boom)
    retrieved, trace = retrieval.gather_evidence("biodiversity is declining", site, fallback="")
    assert trace["interventions"] == [] and len(trace["queries"]) == 1
    assert retrieved, "base query alone must still return evidence"
