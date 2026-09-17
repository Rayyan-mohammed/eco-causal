from rootcause.agent.tools import classify_value, correlate


def test_classify_low_soil_organic_carbon():
    result = classify_value("soil_organic_carbon", 0.3)
    assert result["label"] == "critically_low"


def test_classify_good_soil_organic_carbon():
    result = classify_value("soil_organic_carbon", 3.0)
    assert result["label"] == "good"


def test_classify_semi_arid_rainfall():
    result = classify_value("rainfall_level", 450)
    assert result["label"] == "semi_arid"


def test_classify_unknown_variable_returns_none():
    assert classify_value("not_a_real_variable", 5) is None


def test_correlate_only_classifies_numeric_known_variables():
    results = correlate({
        "soil_organic_carbon": 0.4,
        "rainfall_level": 900,
        "land_use": "monoculture wheat",  # non-numeric, should be skipped
    })
    variables = {r["variable"] for r in results}
    assert variables == {"soil_organic_carbon", "rainfall_level"}
