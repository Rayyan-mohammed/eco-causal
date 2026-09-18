const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const knownVarsEl = document.getElementById("known-vars");
const jsonInput = document.getElementById("json-input");
const jsonStatus = document.getElementById("json-status");
const statusBanner = document.getElementById("status-banner");
const tpl = document.getElementById("tpl-message");

let sessionId = null;

async function api(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function init() {
  try {
    const stored = sessionStorage.getItem("rootcause_session");
    if (stored) {
      sessionId = stored;
    } else {
      const data = await api("/api/session");
      sessionId = data.session_id;
      sessionStorage.setItem("rootcause_session", sessionId);
      if (!data.gemini_configured) showBanner();
    }
    const status = await fetch("/api/status").then((r) => r.json());
    if (!status.gemini_configured) showBanner();
  } catch (e) {
    console.error(e);
  }
}

function showBanner() {
  statusBanner.textContent = "GEMINI_API_KEY is not set on the server — chat requests will fail until it's configured.";
  statusBanner.classList.remove("hidden");
}

function renderKnownVariables(vars) {
  if (!vars || Object.keys(vars).length === 0) {
    knownVarsEl.textContent = "None yet — these fill in as the conversation progresses.";
    return;
  }
  knownVarsEl.textContent = JSON.stringify(vars, null, 2);
}

const BADGE_ICON = { accepted: "✓", downgraded: "!", rejected: "✕" };

function edgeColor(r) {
  if (!r.exists) return "#c0392b";
  if (r.condition_satisfied === false) return "#b7791f";
  if (r.condition_satisfied === null && r.edge && r.edge.condition) return "#b7791f";
  return "#2f9e5c";
}

function renderGraph(container, edgeResults) {
  const nodeIds = new Set();
  const nodes = [];
  const edges = [];
  edgeResults.forEach((r, i) => {
    [r.source, r.target].forEach((id) => {
      if (!nodeIds.has(id)) {
        nodeIds.add(id);
        nodes.push({ id, label: id.replaceAll("_", " ") });
      }
    });
    edges.push({
      id: i,
      from: r.source,
      to: r.target,
      color: { color: edgeColor(r), highlight: edgeColor(r) },
      arrows: "to",
      width: 2.5,
      smooth: { type: "curvedCW", roundness: 0.15 },
    });
  });

  new vis.Network(
    container,
    { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) },
    {
      autoResize: true,
      physics: { stabilization: true, barnesHut: { springLength: 130 } },
      nodes: {
        shape: "box",
        margin: 8,
        font: { size: 12, face: "Inter" },
        color: { background: "#e5f4ea", border: "#2f9e5c" },
        borderWidth: 1.5,
      },
      edges: { font: { size: 0 } },
      interaction: { dragView: true, zoomView: true, selectable: false },
    }
  );
}

function appendMessage(role, text, meta) {
  const node = tpl.content.cloneNode(true);
  const msg = node.querySelector(".msg");
  msg.classList.add(role);
  node.querySelector(".msg-role").textContent = role === "user" ? "You" : "ROOTCAUSE";
  node.querySelector(".msg-text").textContent = text;

  if (meta && meta.checker_status) {
    const metaEl = node.querySelector(".msg-meta");
    metaEl.classList.remove("hidden");

    if (meta.impacted_metrics && meta.impacted_metrics.length) {
      const chipsEl = node.querySelector(".impacted-metrics");
      meta.impacted_metrics.forEach((m) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = m;
        chipsEl.appendChild(chip);
      });
    }
    if (meta.time_horizon) {
      node.querySelector(".time-horizon").innerHTML = `<b>Time horizon:</b> ${meta.time_horizon}`;
    }
    const badge = node.querySelector(".badge");
    badge.textContent = `${BADGE_ICON[meta.checker_status] || ""} ${meta.checker_status}`;
    badge.classList.add(meta.checker_status);
    node.querySelector(".confidence").textContent = `confidence: ${meta.confidence}`;

    if (meta.edge_results && meta.edge_results.length) {
      const graphWrap = node.querySelector(".graph-wrap");
      graphWrap.classList.remove("hidden");
      // defer graph rendering until the element is attached to the DOM
      requestAnimationFrame(() => {
        const canvas = msg.querySelector(".graph-canvas");
        renderGraph(canvas, meta.edge_results);
      });
    }
    if (meta.citations && meta.citations.length) {
      const sourcesEl = node.querySelector(".sources");
      sourcesEl.classList.remove("hidden");
      const ul = sourcesEl.querySelector("ul");
      meta.citations.forEach((c) => {
        const li = document.createElement("li");
        li.textContent = c;
        ul.appendChild(li);
      });
    }
  }

  chatLog.appendChild(node);
  chatLog.scrollTop = chatLog.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text || !sessionId) return;

  appendMessage("user", text, null);
  chatInput.value = "";
  sendBtn.disabled = true;
  appendMessage("assistant", "Reasoning…", null);
  const placeholder = chatLog.lastElementChild;

  try {
    const result = await api("/api/chat", { session_id: sessionId, message: text });
    placeholder.remove();
    appendMessage("assistant", result.text, result);
    renderKnownVariables(result.known_variables);
  } catch (err) {
    placeholder.querySelector(".msg-text").textContent = "Something went wrong reaching the server. Please try again.";
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    chatInput.focus();
  }
});

document.getElementById("apply-json-btn").addEventListener("click", async () => {
  jsonStatus.textContent = "";
  jsonStatus.className = "json-status";
  let variables;
  try {
    variables = JSON.parse(jsonInput.value);
  } catch (e) {
    jsonStatus.textContent = `Invalid JSON: ${e.message}`;
    jsonStatus.classList.add("err");
    return;
  }
  try {
    const data = await api("/api/variables", { session_id: sessionId, variables });
    renderKnownVariables(data.known_variables);
    jsonStatus.textContent = "Variables applied.";
    jsonStatus.classList.add("ok");
  } catch (e) {
    jsonStatus.textContent = "Failed to apply variables.";
    jsonStatus.classList.add("err");
  }
});

document.getElementById("reset-btn").addEventListener("click", async () => {
  if (!sessionId) return;
  await api("/api/reset", { session_id: sessionId });
  chatLog.innerHTML = "";
  renderKnownVariables({});
});

init();
