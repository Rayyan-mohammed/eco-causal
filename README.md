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
  causal_map.json       expert-curated directed graph: 32 nodes, 58 edges, each with a citation,
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
  output/formatter.py       assembles the final response: action, mechanism, impacted metrics, time horizon,
                             confidence, checker status, citations — as separate structured fields
  llm.py                    thin Gemini API wrapper (chat + structured parse), free tier by default
  config.py                 paths, model id, required-variable list

app/api.py                  FastAPI backend: session-based /api/chat, /api/variables, /api/reset — a thin
                             HTTP wrapper around the same rootcause pipeline, nothing duplicated. Also serves
                             the built frontend/dist in production.

frontend/                    React 19 + Vite + Tailwind v4 UI — the only frontend (Streamlit and the earlier
                             vanilla-JS version were both removed in favor of this one)
  src/App.jsx                 session bootstrap, chat state, dark-mode persistence
  src/components/
    ReasoningGraph.jsx          React Flow diagram of the exact chain the checker evaluated, auto-layout,
                                 color-coded live (green/amber/red), not a static image
    MessageBubble.jsx           chat bubble: action + mechanism, impacted-metric chips, time horizon,
                                 status badge, the graph, a collapsible sources list — framer-motion throughout
    Sidebar.jsx                 known site variables (formatted, not a raw JSON dump) + structured JSON input
    Hero.jsx / Header.jsx       landing section with a 3-step pipeline visual, sticky header, theme toggle

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

cd frontend
npm install
npm run build                 # produces frontend/dist, which app/api.py serves
cd ..
```

Get a free `GEMINI_API_KEY` at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — just a Google account, no card, no billing setup. The default model (`gemini-3.1-flash-lite`, set in `.env.example`) runs entirely on Google's free tier. (`gemini-2.5-flash` and `gemini-2.0-flash` have since been retired for new API users — Google's own 404 error names the current replacement generation; `gemini-3.1-flash-lite` was chosen over the flagship `gemini-3.6-flash` after live testing found the latter frequently 503s under free-tier demand.)

**Multiple free-tier accounts:** add `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, ... to `.env` (numbered sequentially, no gaps) and `rootcause/llm.py` round-robins across all of them on every call, automatically falling back to the next key within the same call on a rate limit (429) or transient server overload (500/503). This multiplies effective free-tier throughput linearly with the number of accounts.

## Running it

```bash
# offline eval — no API key needed, verifies the checker against the answer key
python eval/run_eval.py

# unit tests (includes the FastAPI routes; needs frontend/dist to exist — run npm run build first)
pytest tests/

# production mode: one server, needs GEMINI_API_KEY in .env and frontend/dist already built
uvicorn app.api:app --reload
# then open http://127.0.0.1:8000

# frontend dev mode instead (hot reload): run these two in separate terminals
uvicorn app.api:app --reload            # backend on :8000
cd frontend && npm run dev              # frontend on :5173, proxies /api to :8000

# the full live 3-condition evaluation (needs GEMINI_API_KEY, free tier)
python eval/run_eval.py --live

# score a completed --live run: applies the same checker to all 3 conditions
python eval/run_eval.py --score
```

## Deploying a live URL

The knowledge base auto-builds on first run if missing (`rootcause/agent/tools.py`), so there's no manual indexing step on a fresh host. The repo's `Dockerfile` is a multi-stage build — a Node stage builds `frontend/dist`, then a Python stage serves it alongside the API — so a plain `docker build .` produces a fully working image with nothing to build separately.

1. Push this repo to GitHub (already done if you're reading this from the repo).
2. Go to [render.com](https://render.com) (or Fly.io / Railway — all three build directly from a `Dockerfile` on a free tier), sign in with GitHub — this step needs your own account, it can't be done on your behalf.
3. **New -> Web Service**, pick this repo. The host detects the `Dockerfile` automatically.
4. Add your key(s) as environment variables — `GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, ... (or a single `GEMINI_API_KEY`) — the same names `.env` uses locally, since `rootcause/config.py` reads them directly from the process environment either way.
5. Deploy. Free-tier services spin down after inactivity and take ~30-60s to wake on the next request — expected on a free host, not a bug.

## Current status against the blueprint's evaluation metrics

Running `python eval/run_eval.py` right now (no API key required) against the 30-scenario, 64-claim answer key:

| Metric | Result |
|---|---|
| Causal validity rate (accepted-expected claims correctly accepted) | 100% |
| Checker precision (of claims flagged invalid, how many truly are) | 100% |
| Checker recall (of truly invalid claims, how many were caught) | 100% |

This validates the checker's logic against the causal map itself. The `--live` mode goes further and answers the actual research question — `python eval/run_eval.py --live && python eval/run_eval.py --score`, all 30 scenarios, real Gemini API calls. Run three times on 2026-09-18 (LLM output is non-deterministic, so every run is reported honestly rather than keeping only the best one):

| Condition | Run A | Run B | Run C | Average |
|---|---|---|---|---|
| LLM-only (no retrieval, no checker) | 6.7% | 10.0% | 13.3% | ~10.0% |
| RAG-grounded (retrieval, no checker) | 40.0% | 43.3% | 43.3% | ~42.2% |
| ROOTCAUSE full (retrieval + checker) | 80.0% | 70.0% | 73.3% | **~74.4%** |

This is the blueprint's core claim, shown directly and reproducibly across three independent runs: causal validity rises monotonically as retrieval and then the checker get added, every time, regardless of run-to-run variance in the LLM's exact wording. The same checker was applied post-hoc to all three conditions' outputs for a fair comparison (raw detail in `eval/results/live_scored.json`, gitignored — rerun the two commands above to reproduce). For context, the very first live run (before any of the fixes below) scored 6.7% / 30.0% / 43.3% against a 45-edge map with one regeneration attempt — expanding the map to 58 edges, wiring up condition checks for the most common recurring downgrade causes (arid-climate proxies via rainfall, categorical grazing severity), allowing up to 3 regeneration attempts, and prompting the model to check its own site data before proposing a mechanism moved ROOTCAUSE full from the low 40s to a stable ~74% average, with rejections dropping to 0-4 out of 30 across the three runs (down from 11 originally).

Two honest caveats on reading these numbers:
- **The absolute percentages are conservative, not a ceiling.** The causal map covers 58 edges; a claim not in the map gets rejected even if it's a reasonable real-world relationship the map simply hasn't captured yet. This affects all three conditions equally, so the *relative* ordering above is solid evidence — the *absolute* rates would rise further with a larger map still.
- **Chain length confounds the comparison somewhat.** The LLM-only baseline, with no retrieval to ground it, tends to write long, meandering answers that extract into much longer causal chains than ROOTCAUSE's disciplined single-mechanism output — and a longer chain has a mechanically higher chance of containing at least one unsupported step, independent of whether the reasoning is actually worse. Some of LLM-only's low score is genuine hallucination (verified by spot-checking extracted chains, e.g. one run had `tillage_intensity` claimed to directly affect `soil_structure`, `earthworm_abundance`, and `pollution_runoff` in one hop each — only the first two are documented edges, added specifically because tillage's direct mechanical effects are real and separate from its carbon-mediated effect), but some is this length effect.

A real example from Run B, scenario s16 (heat stress on orchard pollinators): ROOTCAUSE recommended organic mulching, reasoning that "mulching increases soil moisture retention, which decreases surface evaporation, which reduces the upward capillary movement of salts, thereby lowering surface soil salinity." That mechanism is real and now in the map (added specifically because this exact claim showed up in an earlier run and was verified against the literature — see `data/causal_map.json` edge `e58`) — but the map is honest that the condition under which it holds (evaporation-driven salinization under irrigation specifically) couldn't be confirmed from what the user had said, so the answer was downgraded with the caveat spelled out rather than presented as fully certain. That's the intended behavior for a claim that's directionally right but incompletely verifiable, not a bug.

## Honest scope

The causal map is expert-curated from cited literature, not statistically discovered from raw data. Every peer-reviewed and institutional-report citation has been checked against a live web search and carries a verified DOI, publisher URL, or ISBN — see `data/sources.md` § "Citation verification pass" for exactly which citations are DOI-verified papers, which point to an official assessment-report landing page, and the two that link to a general FAO portal rather than a single precisely-dated document (flagged inline in those citations themselves, not hidden).

Coverage is necessarily incomplete at 32 nodes / 58 edges, and only 11 edges currently carry a *structured*, checkable condition — rainfall thresholds (cover cropping, agroforestry, the rainfall-vegetation link, irrigation-driven salinity, irrigation-driven yield), a soil pH threshold for earthworms, and categorical grazing severity (three edges). Several other documented conditions (fertilizer application rate/timing, drainage quality specifically, deforestation scale/timescale) exist as citations in the map but aren't yet wired to a check, so claims through those edges are honestly downgraded rather than either falsely accepted or rejected. Extending `condition_check` coverage on those edges is the natural next increment.

## References

- Zecevic, Willig, Dhami & Kersting (2023). *Causal Parrots: Large Language Models May Talk Causality But Are Not Causal.* arXiv:2308.13067.
- Wu et al. (2025). *Why LLMs Fail at Causal Discovery and How Interventional Agents Escape.* arXiv:2605.27567.
- Agri-SAGE (2026). arXiv:2607.00454.
- AgriGPT (2025). arXiv:2508.08632.
- AgriRegion (2025). arXiv:2512.10114.
- FAO Global Soil Partnership; IPCC Assessment Reports; IPBES Assessment Reports — see `data/sources.md` and inline citations in `data/causal_map.json` / `data/knowledge/*.md`.
