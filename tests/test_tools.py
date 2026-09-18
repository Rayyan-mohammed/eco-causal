from rootcause.agent.tools import classify_climate_zone, classify_value, correlate


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


def test_classify_climate_zone_tropical():
    assert classify_climate_zone(5.0)["label"] == "tropical"


def test_classify_climate_zone_temperate():
    assert classify_climate_zone(45.0)["label"] == "temperate"


def test_classify_climate_zone_polar():
    assert classify_climate_zone(70.0)["label"] == "polar/subpolar"


def test_classify_climate_zone_handles_southern_hemisphere():
    # -30 (southern hemisphere subtropics) should classify the same as +30
    assert classify_climate_zone(-30.0)["label"] == classify_climate_zone(30.0)["label"]


def test_correlate_includes_latitude_as_climate_zone():
    results = correlate({"latitude": 17.4, "longitude": 78.5})
    lat_result = next(r for r in results if r["variable"] == "latitude")
    assert lat_result["label"] == "tropical"
