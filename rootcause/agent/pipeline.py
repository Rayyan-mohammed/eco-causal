from rootcause.agent.checker import check_chain
from rootcause.agent.clarification import build_clarification_question, missing_required_variables
from rootcause.agent.extraction import extract_causal_chain, extract_input_variables
from rootcause.agent.recommendation import draft_recommendation
from rootcause.agent.state import ConversationState
from rootcause.agent.tools import correlate, retrieve
from rootcause.causal.graph import CausalGraph
from rootcause.config import CAUSAL_MAP_PATH
from rootcause.output.formatter import format_response

MAX_REGENERATIONS = 1


class RootcausePipeline:
    """Runs the fixed stage sequence from the blueprint: input handling,
    clarification, retrieval, correlation, recommendation drafting, the
    Causal Consistency Checker, and output formatting. Multi-turn memory
    lives in the ConversationState passed in by the caller (e.g. the
    Streamlit app), so the same pipeline instance can serve many conversations."""

    def __init__(self):
        self.graph = CausalGraph.from_file(CAUSAL_MAP_PATH)

    def handle_turn(self, state: ConversationState, user_text: str) -> dict:
        state.add_user_message(user_text)

        extracted = extract_input_variables(user_text)
        state.update_variables(extracted.model_dump(exclude={"concern"}))

        missing = missing_required_variables(state.known_variables)
        if missing:
            question = build_clarification_question(missing)
            state.add_assistant_message(question)
            return {"type": "clarification", "text": question, "missing": missing}

        retrieved = retrieve(extracted.concern or user_text, n_results=4)
        correlations = correlate(state.known_variables)
        history = state.messages[:-1]

        draft, verdict = self._draft_and_check(user_text, retrieved, correlations, state.known_variables, history)

        result = format_response(draft, verdict, retrieved)
        state.add_assistant_message(result["text"])
        return {"type": "recommendation", **result}

    def _draft_and_check(self, user_text, retrieved, correlations, known_variables, history):
        draft = draft_recommendation(user_text, retrieved, correlations, known_variables, history)
        chain = extract_causal_chain(draft, self.graph.node_catalog())
        verdict = check_chain([(link.cause, link.effect) for link in chain.chain], self.graph, known_variables)

        attempts = 0
        while verdict.status == "rejected" and attempts < MAX_REGENERATIONS:
            draft = draft_recommendation(
                user_text, retrieved, correlations, known_variables, history, revision_note=verdict.explanation
            )
            chain = extract_causal_chain(draft, self.graph.node_catalog())
            verdict = check_chain([(link.cause, link.effect) for link in chain.chain], self.graph, known_variables)
            attempts += 1

        return draft, verdict
