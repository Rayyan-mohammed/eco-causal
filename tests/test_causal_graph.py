from rootcause.causal.graph import CausalGraph
from rootcause.config import CAUSAL_MAP_PATH


def load_graph():
    return CausalGraph.from_file(CAUSAL_MAP_PATH)


def test_loads_expected_node_and_edge_counts():
    graph = load_graph()
    assert len(graph.nodes_by_id) >= 30
    assert graph.graph.number_of_edges() >= 40


def test_known_edge_exists():
    graph = load_graph()
    assert graph.edge_exists("soil_organic_carbon", "soil_microbial_diversity")


def test_unknown_edge_does_not_exist():
    graph = load_graph()
    result = graph.check_edge("pollinator_abundance", "deforestation_rate", context={})
    assert result.exists is False


def test_reverse_direction_is_flagged():
    graph = load_graph()
    # soil_microbial_diversity -> soil_structure is documented; the reverse is not a real edge
    result = graph.check_edge("soil_structure", "soil_microbial_diversity", context={})
    assert result.exists is False
    assert "reverse" in result.note.lower()


def test_cover_crop_condition_holds_in_wet_climate():
    graph = load_graph()
    result = graph.check_edge("cover_crop_adoption", "soil_organic_carbon", context={"rainfall_level": 900})
    assert result.exists is True
    assert result.condition_satisfied is True


def test_cover_crop_condition_fails_in_semi_arid_climate():
    """This is the exact failure mode from the blueprint: a plausible-sounding
    recommendation (cover crops raise soil carbon) that breaks down under a
    rainfall condition the checker must catch."""
    graph = load_graph()
    result = graph.check_edge("cover_crop_adoption", "soil_organic_carbon", context={"rainfall_level": 250})
    assert result.exists is True
    assert result.condition_satisfied is False


def test_agroforestry_is_the_valid_alternative_in_semi_arid_climate():
    graph = load_graph()
    result = graph.check_edge("agroforestry_adoption", "soil_moisture_retention", context={"rainfall_level": 250})
    assert result.exists is True
    assert result.condition_satisfied is True


def test_condition_unverified_without_context():
    graph = load_graph()
    result = graph.check_edge("cover_crop_adoption", "soil_organic_carbon", context={})
    assert result.exists is True
    assert result.condition_satisfied is None


def test_categorical_condition_satisfied_on_overgrazing():
    graph = load_graph()
    result = graph.check_edge("grazing_intensity", "soil_structure", context={"grazing_intensity": "high"})
    assert result.condition_satisfied is True


def test_categorical_condition_case_insensitive():
    graph = load_graph()
    result = graph.check_edge("grazing_intensity", "soil_structure", context={"grazing_intensity": "HIGH"})
    assert result.condition_satisfied is True


def test_categorical_condition_fails_on_low_grazing():
    graph = load_graph()
    result = graph.check_edge("grazing_intensity", "soil_structure", context={"grazing_intensity": "low"})
    assert result.condition_satisfied is False
