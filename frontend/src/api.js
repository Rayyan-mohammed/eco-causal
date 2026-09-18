const BASE = import.meta.env.VITE_API_BASE || "";

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    const err = new Error(detail.detail || `${path} failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

async function get(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const err = new Error(`${path} failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const api = {
  createSession: () => post("/api/session"),
  status: () => get("/api/status"),
  chat: (sessionId, message) => post("/api/chat", { session_id: sessionId, message }),
  setVariables: (sessionId, variables) => post("/api/variables", { session_id: sessionId, variables }),
  getVariables: (sessionId) => get(`/api/variables/${sessionId}`),
  reset: (sessionId) => post("/api/reset", { session_id: sessionId, message: "" }),
};
