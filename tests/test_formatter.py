import pytest
from pydantic import ValidationError

from rootcause.agent.checker import CheckerVerdict
from rootcause.causal.graph import CausalGraph
from rootcause.config import CAUSAL_MAP_PATH
from rootcause.agent.recommendation import RecommendationDraft
from rootcause.output.formatter import format_response


def make_draft(**overrides) -> RecommendationDraft:
    defaults = dict(
        action="Convert part of the field to agroforestry.",
        mechanism="Agroforestry adoption increases soil moisture retention, which supports pollinator abundance.",
        impacted_metrics=["soil moisture retention", "pollinator abundance"],
        time_horizon="1-2 years",
        horizon="medium",
        expected_effect="Not quantified in the retrieved evidence.",
    )
    defaults.update(overrides)
    return RecommendationDraft(**defaults)


def test_accepted_response_has_no_checker_note_appended():
    draft = make_draft()
    verdict = CheckerVerdict(status="accepted", confidence="high", explanation="fully supported")
    result = format_response(draft, verdict, retrieved=[])

    assert "⚠️" not in result["text"] and "❌" not in result["text"]
    assert result["impacted_metrics"] == ["soil moisture retention", "pollinator abundance"]
    assert result["time_horizon"] == "1-2 years"
    assert result["checker_status"] == "accepted"


def test_downgraded_response_appends_plain_language_note_and_keeps_structured_fields():
    draft = make_draft()
    verdict = CheckerVerdict(status="downgraded", confidence="low", explanation="condition not met")
    result = format_response(draft, verdict, retrieved=[])

    assert "checks out against my sourced evidence" in result["text"]
    assert "condition not met" in result["text"]  # falls back to explanation when no edge_results are set
    assert result["confidence"] == "low"
    assert result["impacted_metrics"] == draft.impacted_metrics


def test_citations_deduplicated_and_sorted_from_retrieved():
    draft = make_draft()
    verdict = CheckerVerdict(status="accepted", confidence="high", explanation="ok")
    retrieved = [
        {"citation": "B source"},
        {"citation": "A source"},
        {"citation": "A source"},
        {"citation": "Uncited"},
    ]
    result = format_response(draft, verdict, retrieved)
    assert result["citations"] == ["A source", "B source"]


def test_horizon_must_be_short_medium_or_long():
    with pytest.raises(ValidationError):
        make_draft(horizon="eventually")


def test_horizon_and_expected_effect_are_passed_through():
    draft = make_draft(horizon="long", time_horizon="6-12 months", expected_effect="~0.32 Mg C/ha/yr (Poeplau & Don 2015)")
    verdict = CheckerVerdict(status="accepted", confidence="high", explanation="ok")
    result = format_response(draft, verdict, retrieved=[])
    assert result["horizon"] == "short"
    assert result["expected_effect"].startswith("~0.32")


def test_step_evidence_carries_each_documented_edges_own_citation():
    graph = CausalGraph.from_file(CAUSAL_MAP_PATH)
    results = [
        graph.check_edge("agroforestry_adoption", "soil_organic_carbon", {}),  # documented
        graph.check_edge("crop_diversity", "vegetation_cover", {}),  # NOT documented
    ]
    verdict = CheckerVerdict(status="rejected", confidence="low", edge_results=results, explanation="x")
    evidence = format_response(make_draft(), verdict, retrieved=[])["step_evidence"]

    # Only the documented step appears, and it cites the paper attached to that edge.
    assert len(evidence) == 1
    assert evidence[0]["cause"] == "agroforestry adoption"
    assert "Shi, Feng, Xu & Kuzyakov" in evidence[0]["citation"]


def test_classify_horizon_uses_upper_bound_of_the_numeric_range():
    from rootcause.agent.recommendation import classify_horizon

    assert classify_horizon("6-12 months") == "short"
    assert classify_horizon("2-3 years") == "medium"
    assert classify_horizon("5-10 years") == "long"
    assert classify_horizon("Multiple seasons") is None
