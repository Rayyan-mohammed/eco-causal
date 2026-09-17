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
