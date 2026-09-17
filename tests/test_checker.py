from rootcause.agent.checker import check_chain
from rootcause.causal.graph import CausalGraph
from rootcause.config import CAUSAL_MAP_PATH


def load_graph():
    return CausalGraph.from_file(CAUSAL_MAP_PATH)


def test_empty_chain_is_rejected():
    graph = load_graph()
    verdict = check_chain([], graph, {})
    assert verdict.status == "rejected"


def test_fully_valid_chain_is_accepted():
    graph = load_graph()
    chain = [
        ("soil_organic_carbon", "soil_microbial_diversity"),
        ("soil_microbial_diversity", "soil_structure"),
    ]
    verdict = check_chain(chain, graph, {})
    assert verdict.status == "accepted"
    assert verdict.confidence == "high"


def test_unsupported_step_is_rejected():
    graph = load_graph()
    chain = [("pollinator_abundance", "deforestation_rate")]
    verdict = check_chain(chain, graph, {})
    assert verdict.status == "rejected"


def test_semi_arid_cover_crop_chain_is_downgraded():
    """The blueprint's headline example: a plausible chain (cover crop -> SOC ->
    microbial diversity -> pollinators) that fails a rainfall condition."""
    graph = load_graph()
    chain = [
        ("cover_crop_adoption", "soil_organic_carbon"),
        ("soil_organic_carbon", "soil_microbial_diversity"),
        ("soil_microbial_diversity", "pollinator_abundance"),
    ]
    verdict = check_chain(chain, graph, {"rainfall_level": 250})
    assert verdict.status == "downgraded"
    assert verdict.confidence == "low"


def test_same_chain_accepted_with_enough_rainfall():
    graph = load_graph()
    chain = [
        ("cover_crop_adoption", "soil_organic_carbon"),
        ("soil_organic_carbon", "soil_microbial_diversity"),
    ]
    verdict = check_chain(chain, graph, {"rainfall_level": 900})
    assert verdict.status == "accepted"


def test_unverified_condition_downgrades_with_medium_confidence():
    graph = load_graph()
    chain = [("cover_crop_adoption", "soil_organic_carbon")]
    verdict = check_chain(chain, graph, {})
    assert verdict.status == "downgraded"
    assert verdict.confidence == "medium"
