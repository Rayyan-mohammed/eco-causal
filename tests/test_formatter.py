from rootcause.agent.checker import CheckerVerdict
from rootcause.agent.recommendation import RecommendationDraft
from rootcause.output.formatter import format_response


def make_draft(**overrides) -> RecommendationDraft:
    defaults = dict(
        action="Convert part of the field to agroforestry.",
        mechanism="Agroforestry adoption increases soil moisture retention, which supports pollinator abundance.",
        impacted_metrics=["soil moisture retention", "pollinator abundance"],
        time_horizon="1-2 years",
    )
    defaults.update(overrides)
    return RecommendationDraft(**defaults)


def test_accepted_response_has_no_checker_note_appended():
    draft = make_draft()
    verdict = CheckerVerdict(status="accepted", confidence="high", explanation="fully supported")
    result = format_response(draft, verdict, retrieved=[])

    assert "Consistency check" not in result["text"]
    assert result["impacted_metrics"] == ["soil moisture retention", "pollinator abundance"]
    assert result["time_horizon"] == "1-2 years"
    assert result["checker_status"] == "accepted"


def test_downgraded_response_appends_note_and_keeps_structured_fields():
    draft = make_draft()
    verdict = CheckerVerdict(status="downgraded", confidence="low", explanation="condition not met")
    result = format_response(draft, verdict, retrieved=[])

    assert "Consistency check: downgraded" in result["text"]
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
