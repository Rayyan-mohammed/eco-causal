import json
import sys
from pathlib import Path

import streamlit as st

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

for role, text, meta in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)
        if meta:
            st.caption(f"{BADGES.get(meta['checker_status'], '')} Checker: {meta['checker_status']} · confidence: {meta['confidence']}")
            if meta["citations"]:
                with st.expander("Sources"):
                    for c in meta["citations"]:
                        st.markdown(f"- {c}")

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
                "checker_status": result["checker_status"],
                "confidence": result["confidence"],
                "citations": result["citations"],
            }
            st.caption(f"{BADGES[meta['checker_status']]} Checker: {meta['checker_status']} · confidence: {meta['confidence']}")
            if meta["citations"]:
                with st.expander("Sources"):
                    for c in meta["citations"]:
                        st.markdown(f"- {c}")

    st.session_state.history.append(("assistant", result["text"], meta))
