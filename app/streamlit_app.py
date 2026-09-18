import json
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

# On Streamlit Community Cloud, keys are set via the app's Secrets UI
# (st.secrets) rather than a .env file. Bridge them into the environment
# before any rootcause module is imported, since config.py reads os.environ
# at import time. Locally, with no secrets.toml configured, this is a no-op.
try:
    for _key, _value in st.secrets.items():
        os.environ.setdefault(_key, str(_value))
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rootcause.agent.pipeline import RootcausePipeline
from rootcause.agent.state import ConversationState
from rootcause.config import GEMINI_API_KEY

st.set_page_config(page_title="ROOTCAUSE", page_icon="🌱", layout="centered")

BADGES = {"accepted": "✅", "downgraded": "⚠️", "rejected": "❌"}


@st.cache_resource
def get_pipeline() -> RootcausePipeline:
    return RootcausePipeline()


if "state" not in st.session_state:
    st.session_state.state = ConversationState()
if "history" not in st.session_state:
    st.session_state.history = []

st.title("🌱 ROOTCAUSE")
st.caption(
    "A biodiversity advisory agent that checks its own multi-variable reasoning against a "
    "source-backed causal map before it lets a recommendation reach you."
)

if not GEMINI_API_KEY:
    st.warning("GEMINI_API_KEY is not set. Add it to a .env file (see .env.example) before chatting.")

with st.sidebar:
    st.header("Known site variables")
    if st.session_state.state.known_variables:
        st.json(st.session_state.state.known_variables)
    else:
        st.caption("None yet — these fill in as the conversation progresses.")

    st.divider()
    st.header("Structured JSON input")
    st.caption("Optional: submit site variables directly as JSON instead of free text (geo-coordinates supported).")
    json_text = st.text_area(
        "JSON",
        placeholder=(
            '{"soil_organic_carbon": 0.4, "rainfall_level": 250, '
            '"land_use": "monoculture wheat", "latitude": 17.4, "longitude": 78.5}'
        ),
        height=140,
    )
    if st.button("Apply JSON") and json_text.strip():
        try:
            data = json.loads(json_text)
            st.session_state.state.update_variables(data)
            st.success("Variables applied.")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")

    st.divider()
    if st.button("Reset conversation"):
        st.session_state.state = ConversationState()
        st.session_state.history = []
        st.rerun()

EDGE_COLORS = {"missing": "#dc2626", "unmet": "#f59e0b", "ok": "#16a34a"}


def _edge_color(edge_result) -> str:
    if not edge_result.exists:
        return EDGE_COLORS["missing"]
    if edge_result.condition_satisfied is False:
        return EDGE_COLORS["unmet"]
    if edge_result.condition_satisfied is None and edge_result.edge and edge_result.edge.get("condition"):
        return EDGE_COLORS["unmet"]
    return EDGE_COLORS["ok"]


def render_chain_diagram(edge_results: list) -> None:
    """Draws the exact reasoning chain the checker just evaluated, colored by
    verdict — the point is that a reviewer can see the differentiator (the
    causal map actually being checked) in one glance, not just read about it."""
    if not edge_results:
        return
    graph = nx.DiGraph()
    edge_colors = []
    for r in edge_results:
        graph.add_edge(r.source, r.target)
        edge_colors.append(_edge_color(r))
    labels = {n: n.replace("_", " ") for n in graph.nodes}

    fig, ax = plt.subplots(figsize=(6, 3))
    pos = nx.spring_layout(graph, seed=7, k=1.3)
    nx.draw_networkx_nodes(graph, pos, node_color="#e0e7ff", node_size=1800, ax=ax)
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=7, ax=ax)
    nx.draw_networkx_edges(
        graph, pos, edge_color=edge_colors, width=2.2, arrowsize=16,
        arrowstyle="-|>", connectionstyle="arc3,rad=0.08", ax=ax,
    )
    ax.axis("off")
    ax.margins(0.2)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True, use_container_width=False)
    plt.close(fig)
    st.caption("🟢 supported · 🟠 condition not verified/met · 🔴 not documented (or reversed)")


def render_meta(meta: dict) -> None:
    if meta.get("impacted_metrics"):
        st.markdown("**Impacted metrics:** " + ", ".join(meta["impacted_metrics"]))
    if meta.get("time_horizon"):
        st.markdown(f"**Time horizon:** {meta['time_horizon']}")
    st.caption(f"{BADGES.get(meta['checker_status'], '')} Checker: {meta['checker_status']} · confidence: {meta['confidence']}")
    if meta.get("edge_results"):
        render_chain_diagram(meta["edge_results"])
    if meta["citations"]:
        with st.expander("Sources"):
            for c in meta["citations"]:
                st.markdown(f"- {c}")


for role, text, meta in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)
        if meta:
            render_meta(meta)

user_text = st.chat_input("Describe your site and what you're concerned about...")
if user_text:
    st.session_state.history.append(("user", user_text, None))
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Reasoning..."):
            pipeline = get_pipeline()
            result = pipeline.handle_turn(st.session_state.state, user_text)
        st.markdown(result["text"])

        meta = None
        if result["type"] == "recommendation":
            meta = {
                "impacted_metrics": result["impacted_metrics"],
                "time_horizon": result["time_horizon"],
                "checker_status": result["checker_status"],
                "confidence": result["confidence"],
                "citations": result["citations"],
                "edge_results": result["edge_results"],
            }
            render_meta(meta)

    st.session_state.history.append(("assistant", result["text"], meta))
