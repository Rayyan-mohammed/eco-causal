# ROOTCAUSE

A biodiversity advisory chatbot that checks its own multi-variable reasoning against a small, source-backed causal map before it lets a recommendation reach the user.

Built for the Darukaa.Earth AI Biodiversity Intelligence Chatbot Challenge. See `ROOTCAUSE_Blueprint.docx` for the full research writeup this implementation follows.

## The idea

Standard retrieval-augmented generation checks whether a *fact* exists in a source. Nothing in a standard RAG pipeline checks whether a *claimed relationship between two or more facts* is itself supported by that source. A language model can retrieve two true facts — "soil carbon increases microbial diversity" and "microbial diversity supports pollinators" — and still chain them into an invalid recommendation, for example by ignoring that an intervention only works above a rainfall threshold.

ROOTCAUSE closes that specific gap with a **Causal Consistency Checker**: a validation step, sitting between the recommendation draft and the final answer, that extracts the claimed cause → effect chain and checks each step against an expert-curated causal graph — does the edge exist, does the direction match, is any attached condition satisfied by the user's stated site details. Failing claims are downgraded or rejected rather than shown with false confidence.

This is a validation layer over claims a language model generates, not a causal-discovery method — a narrower, more defensible claim than "AI discovers causality," and the one this project actually delivers on.

## Architecture

```
Input handler → Clarification node → Retrieval (RAG) → Correlation tool
    → Recommendation generator → Causal Consistency Checker → Output formatter
                                        ↕
                                  Memory store (multi-turn)
```

A standard RAG agent stops at the recommendation generator. ROOTCAUSE inserts the checker immediately after it: no recommendation reaches the user without first passing, or being explicitly marked as failing, a check against the sourced causal map.

The pipeline runs as an explicit, deterministic stage sequence (`rootcause/agent/pipeline.py`) rather than an open-ended tool-calling loop — the tool set (retrieve, correlate) is fixed and known ahead of time, so a deterministic pipeline is more auditable and reliable than giving the model free rein to decide when to call what, which matters for a system whose entire value proposition is *validated* correctness.

## Project layout

```
data/
  causal_map.json       expert-curated directed graph: ~32 nodes, ~45 edges, each with a citation,
                         effect direction, and (where checkable) a structured numeric condition
  reference_ranges.json literature-derived bands (soil carbon, rainfall, pH, salinity) for the correlation tool
  knowledge/*.md         source excerpts per domain, chunked and indexed for retrieval
  sources.md             primary-source portals (SoilGrids, FAOSTAT, GBIF, IPBES, IPCC, Global Forest Watch)
                          to pull exact citations from before the submission deadline

rootcause/
  causal/graph.py         loads the causal map, answers exists / direction / condition questions
  knowledge/vectorstore.py Chroma-backed retrieval over data/knowledge/*.md
  agent/
    state.py               multi-turn conversation memory
    clarification.py       detects missing required variables, asks a targeted follow-up
    tools.py                retrieval + correlation tools
    extraction.py           structured extraction: free text → variables, and draft → causal chain
    recommendation.py       drafts the recommendation from retrieved context + correlations
    checker.py              the Causal Consistency Checker itself
    pipeline.py             wires the stages together, with one regeneration retry on rejection
  output/formatter.py       assembles the final response: recommendation, confidence, checker status, citations
  llm.py                    thin Gemini API wrapper (chat + structured parse), free tier by default
  config.py                 paths, model id, required-variable list

app/streamlit_app.py        chat UI: free text or structured JSON input, geo-coordinates supported,
                             shows the checker's verdict and cited sources per turn

eval/
  test_scenarios.json       30 hand-built scenarios across all 5 domains, each with a pre-labeled
                             answer key of valid vs. invalid multi-variable claims
  run_eval.py                --offline (default): replays the answer key through the checker directly,
                             no API key needed, reports checker precision/recall
                             --live: runs the real LLM-only / RAG-grounded / ROOTCAUSE-full comparison
                             from blueprint Section 9 (requires GEMINI_API_KEY, free tier)

tests/                      pytest suite for the graph, checker, clarification, and correlation logic
```

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # then fill in GEMINI_API_KEY
```

Get a free `GEMINI_API_KEY` at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — just a Google account, no card, no billing setup. The default model (`gemini-2.5-flash`, set in `.env.example`) runs entirely on Google's free tier.

## Running it

```bash
# offline eval — no API key needed, verifies the checker against the answer key
python eval/run_eval.py

# unit tests
pytest tests/

# the chat app (needs GEMINI_API_KEY in .env)
streamlit run app/streamlit_app.py

# the full live 3-condition evaluation (needs GEMINI_API_KEY, free tier)
python eval/run_eval.py --live
```

## Current status against the blueprint's evaluation metrics

Running `python eval/run_eval.py` right now (no API key required) against the 30-scenario, 64-claim answer key:

| Metric | Result |
|---|---|
| Causal validity rate (accepted-expected claims correctly accepted) | 100% |
| Checker precision (of claims flagged invalid, how many truly are) | 100% |
| Checker recall (of truly invalid claims, how many were caught) | 100% |

This validates the checker's logic against the causal map itself — it does not yet measure whether a live LLM's freely generated recommendations get caught, which is what `--live` mode is for once an API key is available.

## Honest scope

The causal map is expert-curated from cited literature, not statistically discovered from raw data. Every peer-reviewed and institutional-report citation has been checked against a live web search and carries a verified DOI, publisher URL, or ISBN — see `data/sources.md` § "Citation verification pass" for exactly which citations are DOI-verified papers, which point to an official assessment-report landing page, and the two that link to a general FAO portal rather than a single precisely-dated document (flagged inline in those citations themselves, not hidden).

Coverage is necessarily incomplete at ~32 nodes / ~45 edges, and only 4 edges currently carry a *structured*, numerically-checkable condition (rainfall thresholds for cover cropping and agroforestry, a soil pH threshold for earthworms); several other documented conditions (overgrazing severity, fertilizer application rate, drainage quality) exist as citations in the map but aren't yet wired to a numeric check, so claims through those edges are honestly downgraded rather than either falsely accepted or rejected. Extending `condition_check` coverage on those edges is the natural next increment.

## References

- Zecevic, Willig, Dhami & Kersting (2023). *Causal Parrots: Large Language Models May Talk Causality But Are Not Causal.* arXiv:2308.13067.
- Wu et al. (2025). *Why LLMs Fail at Causal Discovery and How Interventional Agents Escape.* arXiv:2605.27567.
- Agri-SAGE (2026). arXiv:2607.00454.
- AgriGPT (2025). arXiv:2508.08632.
- AgriRegion (2025). arXiv:2512.10114.
- FAO Global Soil Partnership; IPCC Assessment Reports; IPBES Assessment Reports — see `data/sources.md` and inline citations in `data/causal_map.json` / `data/knowledge/*.md`.
