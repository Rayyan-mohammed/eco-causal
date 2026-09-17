"""ROOTCAUSE evaluation harness (blueprint Section 9).

Offline mode (default, no API key needed): replays the hand-labeled claims in
test_scenarios.json directly through the Causal Consistency Checker and
reports checker precision/recall against the answer key. This is a
white-box regression check of the checker logic against the causal map.

Live mode (--live, requires GEMINI_API_KEY): runs each scenario's prompt
through the actual pipeline and compares the three conditions from Section 9.2
(LLM-only, RAG-grounded, ROOTCAUSE full). Uses the free Gemini API tier by
default, so this is free to run (subject to Google's free-tier rate limits).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rootcause.agent.checker import check_chain
from rootcause.causal.graph import CausalGraph
from rootcause.config import CAUSAL_MAP_PATH

SCENARIOS_PATH = Path(__file__).resolve().parent / "test_scenarios.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_scenarios() -> list[dict]:
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_offline(scenarios: list[dict], graph: CausalGraph) -> dict:
    rows = []
    for scenario in scenarios:
        for claim in scenario["claims"]:
            chain = [tuple(pair) for pair in claim["chain"]]
            verdict = check_chain(chain, graph, scenario["known_variables"])
            rows.append({
                "scenario_id": scenario["id"],
                "domain": scenario["domain"],
                "chain": claim["chain"],
                "expected": claim["expected"],
                "actual": verdict.status,
                "match": verdict.status == claim["expected"],
                "explanation": verdict.explanation,
            })

    total = len(rows)
    matches = sum(r["match"] for r in rows)

    accepted_expected = [r for r in rows if r["expected"] == "accepted"]
    accepted_correct = sum(r["match"] for r in accepted_expected)

    invalid_expected = [r for r in rows if r["expected"] in ("downgraded", "rejected")]
    flagged_as_invalid = [r for r in rows if r["actual"] in ("downgraded", "rejected")]
    true_positives = sum(1 for r in rows if r["expected"] in ("downgraded", "rejected") and r["actual"] in ("downgraded", "rejected"))

    precision = true_positives / len(flagged_as_invalid) if flagged_as_invalid else float("nan")
    recall = true_positives / len(invalid_expected) if invalid_expected else float("nan")

    summary = {
        "total_claims": total,
        "exact_match_rate": matches / total,
        "causal_validity_rate": accepted_correct / len(accepted_expected) if accepted_expected else float("nan"),
        "checker_precision": precision,
        "checker_recall": recall,
        "mismatches": [r for r in rows if not r["match"]],
    }
    return summary


def print_offline_report(summary: dict) -> None:
    print(f"Total claims evaluated: {summary['total_claims']}")
    print(f"Exact-match rate (checker verdict == answer key): {summary['exact_match_rate']:.1%}")
    print(f"Causal validity rate (accepted-expected claims correctly accepted): {summary['causal_validity_rate']:.1%}")
    print(f"Checker precision (of claims flagged invalid, how many truly are): {summary['checker_precision']:.1%}")
    print(f"Checker recall (of truly invalid claims, how many were flagged): {summary['checker_recall']:.1%}")
    if summary["mismatches"]:
        print(f"\n{len(summary['mismatches'])} mismatch(es) against the answer key:")
        for m in summary["mismatches"]:
            print(f"  [{m['scenario_id']}] {m['chain']} expected={m['expected']} actual={m['actual']} :: {m['explanation']}")
    else:
        print("\nNo mismatches — checker verdicts match the hand-labeled answer key exactly.")


def run_live(scenarios: list[dict]) -> None:
    from rootcause.agent.checker import check_chain as _check
    from rootcause.agent.extraction import extract_causal_chain
    from rootcause.agent.pipeline import RootcausePipeline
    from rootcause.agent.recommendation import draft_recommendation
    from rootcause.agent.state import ConversationState
    from rootcause.agent.tools import correlate, retrieve
    from rootcause.llm import chat

    pipeline = RootcausePipeline()
    results = []

    for scenario in scenarios:
        known_variables = scenario["known_variables"]
        user_text = scenario["scenario_text"]

        llm_only = chat(
            [{"role": "user", "content": user_text}],
            system="You are an environmental advisory assistant. Answer from your own knowledge, no retrieval available.",
            max_tokens=600,
        )

        retrieved = retrieve(user_text, n_results=4)
        rag_only = draft_recommendation(user_text, retrieved, [], known_variables, [])

        state = ConversationState()
        state.known_variables = dict(known_variables)
        full_result = pipeline.handle_turn(state, user_text)

        results.append({
            "scenario_id": scenario["id"],
            "domain": scenario["domain"],
            "llm_only": llm_only,
            "rag_grounded": rag_only,
            "rootcause_full": full_result,
        })

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / "live_run.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Wrote {len(results)} live scenario results to {out_path}")
    print("Manual or LLM-judge scoring against the answer key is the next step per blueprint Section 9.3 (this script does not auto-score free-text LLM-only/RAG-grounded output).")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run the full 3-condition live comparison (requires GEMINI_API_KEY, free tier).")
    args = parser.parse_args()

    scenarios = load_scenarios()

    if args.live:
        run_live(scenarios)
        return

    graph = CausalGraph.from_file(CAUSAL_MAP_PATH)
    summary = run_offline(scenarios, graph)
    print_offline_report(summary)


if __name__ == "__main__":
    main()
