import dataclasses
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rootcause.agent.pipeline import RootcausePipeline
from rootcause.agent.state import ConversationState
from rootcause.config import GEMINI_API_KEY

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="ROOTCAUSE API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline: RootcausePipeline | None = None
_sessions: dict[str, ConversationState] = {}


def get_pipeline() -> RootcausePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RootcausePipeline()
    return _pipeline


def get_session(session_id: str) -> ConversationState:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Unknown session_id. Call /api/session first.")
    return _sessions[session_id]


def _serialize_result(result: dict) -> dict:
    """Turns the pipeline's raw result (which may hold dataclass objects) into
    a plain JSON-safe dict for the HTTP boundary."""
    out = dict(result)
    if "edge_results" in out and out["edge_results"] is not None:
        out["edge_results"] = [dataclasses.asdict(r) for r in out["edge_results"]]
    return out


class ChatRequest(BaseModel):
    session_id: str
    message: str


class VariablesRequest(BaseModel):
    session_id: str
    variables: dict


@app.post("/api/session")
def create_session() -> dict:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = ConversationState()
    return {"session_id": session_id, "gemini_configured": bool(GEMINI_API_KEY)}


@app.get("/api/status")
def status() -> dict:
    return {"gemini_configured": bool(GEMINI_API_KEY)}


@app.get("/api/variables/{session_id}")
def get_variables(session_id: str) -> dict:
    state = get_session(session_id)
    return {"known_variables": state.known_variables}


@app.post("/api/variables")
def set_variables(req: VariablesRequest) -> dict:
    state = get_session(req.session_id)
    state.update_variables(req.variables)
    return {"known_variables": state.known_variables}


@app.post("/api/reset")
def reset(req: ChatRequest) -> dict:
    _sessions[req.session_id] = ConversationState()
    return {"ok": True}


@app.post("/api/chat")
def chat(req: ChatRequest) -> dict:
    state = get_session(req.session_id)
    pipeline = get_pipeline()
    result = pipeline.handle_turn(state, req.message)
    return {"known_variables": state.known_variables, **_serialize_result(result)}


# Serve the built React app (frontend/dist, produced by `npm run build`).
# Mounted/declared last so neither shadows the /api/* routes above.
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")


@app.get("/{full_path:path}")
def spa(full_path: str) -> FileResponse:
    return FileResponse(str(FRONTEND_DIST / "index.html"))
