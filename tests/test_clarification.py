from rootcause.agent.clarification import build_clarification_question, missing_required_variables


def test_all_missing_when_no_variables_known():
    missing = missing_required_variables({})
    assert set(missing) == {"soil_organic_carbon", "rainfall_level", "land_use"}


def test_none_missing_when_all_supplied():
    missing = missing_required_variables({
        "soil_organic_carbon": 1.2, "rainfall_level": 500, "land_use": "monoculture wheat",
    })
    assert missing == []


def test_partial_missing():
    missing = missing_required_variables({"soil_organic_carbon": 1.2})
    assert set(missing) == {"rainfall_level", "land_use"}


def test_clarification_question_covers_each_missing_variable():
    question = build_clarification_question(["rainfall_level", "land_use"])
    assert "rainfall" in question.lower()
    assert "land use" in question.lower()
