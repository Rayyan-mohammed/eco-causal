"""ROOTCAUSE evaluation harness (blueprint Section 9).

Offline mode (default, no API key needed): replays the hand-labeled claims in
test_scenarios.json directly through the Causal Consistency Checker and
reports checker precision/recall against the answer key. This is a
white-box regression check of the checker logic against the causal map.

Live mode (--live, requires GEMINI_API_KEY): runs each scenario's prompt
through the actual pipeline and compares the three conditions from Section 9.2
(LLM-only, RAG-grounded, ROOTCAUSE full). Uses the free Gemini API tier by
default, so this is free to run (subject to Google's free-tier rate limits).

Live mode checkpoints after every scenario to eval/results/live_run.json, so
a shutdown, lost wifi, or any other interruption never costs more than the
one scenario in flight — just rerun the same command and it picks up where
it left off. Pass --fresh to ignore the checkpoint and start over.
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


LIVE_RESULTS_PATH = RESULTS_DIR / "live_run.json"


def _atomic_write_json(path: Path, data) -> None:
    """Write via a temp file + rename so a mid-write shutdown or crash can
    never leave a half-written, corrupted results file behind."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    tmp_path.replace(path)


def _load_checkpoint(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)
    return {row["scenario_id"]: row for row in rows}


def run_live(scenarios: list[dict], fresh: bool = False) -> None:
    from rootcause.agent.pipeline import RootcausePipeline
    from rootcause.agent.recommendation import draft_recommendation
    from rootcause.agent.state import ConversationState
    from rootcause.agent.tools import retrieve
    from rootcause.llm import chat

    RESULTS_DIR.mkdir(exist_ok=True)
    done = {} if fresh else _load_checkpoint(LIVE_RESULTS_PATH)
    if done:
        print(f"Resuming: {len(done)}/{len(scenarios)} scenario(s) already completed in {LIVE_RESULTS_PATH}")

    pipeline = RootcausePipeline()
    remaining = [s for s in scenarios if s["id"] not in done]
    failed = []

    for scenario in remaining:
        known_variables = scenario["known_variables"]
        user_text = scenario["scenario_text"]
        print(f"[{scenario['id']}] running...", flush=True)

        try:
            llm_only = chat(
                [{"role": "user", "content": user_text}],
                system="You are an environmental advisory assistant. Answer from your own knowledge, no retrieval available.",
                max_tokens=2048,
            )
            retrieved = retrieve(user_text, n_results=4)
            rag_only = draft_recommendation(user_text, retrieved, [], known_variables, []).model_dump()

            state = ConversationState()
            state.known_variables = dict(known_variables)
            full_result = pipeline.handle_turn(state, user_text)
        except KeyboardInterrupt:
            print(f"\nInterrupted. {len(done)} scenario(s) saved to {LIVE_RESULTS_PATH} — rerun the same command to resume.")
            return
        except Exception as e:
            # A dropped connection, a transient 503, or a machine going to
            # sleep mid-call all land here: skip this scenario for now
            # without losing everything already completed, and retry it
            # automatically the next time this command runs.
            print(f"[{scenario['id']}] FAILED ({type(e).__name__}: {e}) — will retry on next run")
            failed.append(scenario["id"])
            continue

        done[scenario["id"]] = {
            "scenario_id": scenario["id"],
            "domain": scenario["domain"],
            "llm_only": llm_only,
            "rag_grounded": rag_only,
            "rootcause_full": full_result,
        }
        # Checkpoint after every scenario, not just at the end, so a shutdown
        # or lost connection never costs more than the one in-flight scenario.
        _atomic_write_json(LIVE_RESULTS_PATH, list(done.values()))

    print(f"\nWrote {len(done)}/{len(scenarios)} live scenario results to {LIVE_RESULTS_PATH}")
    if failed:
        print(f"{len(failed)} scenario(s) failed and will be retried automatically on the next run: {failed}")
    print("Manual or LLM-judge scoring against the answer key is the next step per blueprint Section 9.3 (this script does not auto-score free-text LLM-only/RAG-grounded output).")


def score_live(scenarios: list[dict], graph: CausalGraph) -> dict:
    """Scores a completed --live run per blueprint Section 9.3: applies the
    same Causal Consistency Checker post-hoc to the llm_only and rag_grounded
    free text (which had no checker in their generation loop), and reuses the
    verdict rootcause_full already produced live. Using one checker to score
    all three conditions is what makes the comparison apples-to-apples."""
    from rootcause.agent.extraction import extract_causal_chain

    if not LIVE_RESULTS_PATH.exists():
        raise SystemExit(f"No live results found at {LIVE_RESULTS_PATH}. Run `python eval/run_eval.py --live` first.")

    scenario_by_id = {s["id"]: s for s in scenarios}
    with open(LIVE_RESULTS_PATH, encoding="utf-8") as f:
        live_rows = {row["scenario_id"]: row for row in json.load(f)}

    node_catalog = graph.node_catalog()
    detail = []

    for scenario_id, row in live_rows.items():
        known_variables = scenario_by_id[scenario_id]["known_variables"]

        llm_chain = extract_causal_chain(row["llm_only"], node_catalog)
        llm_verdict = check_chain([(l.cause, l.effect) for l in llm_chain.chain], graph, known_variables)

        rag_chain = extract_causal_chain(row["rag_grounded"]["mechanism"], node_catalog)
        rag_verdict = check_chain([(l.cause, l.effect) for l in rag_chain.chain], graph, known_variables)

        detail.append({
            "scenario_id": scenario_id,
            "domain": row["domain"],
            "llm_only": llm_verdict.status,
            "rag_grounded": rag_verdict.status,
            "rootcause_full": row["rootcause_full"]["checker_status"],
        })

    summary = {}
    for condition in ("llm_only", "rag_grounded", "rootcause_full"):
        statuses = [d[condition] for d in detail]
        total = len(statuses)
        accepted = statuses.count("accepted")
        summary[condition] = {
            "total": total,
            "accepted": accepted,
            "downgraded": statuses.count("downgraded"),
            "rejected": statuses.count("rejected"),
            "causal_validity_rate": accepted / total if total else float("nan"),
        }

    _atomic_write_json(RESULTS_DIR / "live_scored.json", {"summary": summary, "detail": detail})
    return summary


def print_live_score_report(summary: dict) -> None:
    print("Causal validity rate by condition (same checker applied post-hoc to all three;")
    print("rootcause_full's verdict is the one it actually produced live, checker in the loop):\n")
    header = f"{'condition':<16} {'accepted':>9} {'downgraded':>11} {'rejected':>9} {'validity rate':>14}"
    print(header)
    print("-" * len(header))
    for condition, s in summary.items():
        print(f"{condition:<16} {s['accepted']:>9} {s['downgraded']:>11} {s['rejected']:>9} {s['causal_validity_rate']:>13.1%}")
    print(f"\nFull per-scenario detail written to {RESULTS_DIR / 'live_scored.json'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Run the full 3-condition live comparison (requires GEMINI_API_KEY, free tier).")
    parser.add_argument("--fresh", action="store_true", help="With --live, ignore any existing checkpoint and start over instead of resuming.")
    parser.add_argument("--score", action="store_true", help="Score a completed --live run's results with the checker (requires GEMINI_API_KEY for chain extraction).")
    args = parser.parse_args()

    scenarios = load_scenarios()
    graph = CausalGraph.from_file(CAUSAL_MAP_PATH)

    if args.live:
        run_live(scenarios, fresh=args.fresh)
        return

    if args.score:
        summary = score_live(scenarios, graph)
        print_live_score_report(summary)
        return

    summary = run_offline(scenarios, graph)
    print_offline_report(summary)


if __name__ == "__main__":
    main()
