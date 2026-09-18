import { useEffect, useRef, useState } from "react";
import { Toaster } from "react-hot-toast";
import toast from "react-hot-toast";
import { api } from "./api";
import ChatPanel from "./components/ChatPanel";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Sidebar from "./components/Sidebar";

let idCounter = 0;
const nextId = () => `m${++idCounter}`;

export default function App() {
  const [dark, setDark] = useState(() => localStorage.getItem("rc_theme") === "dark");
  const [sessionId, setSessionId] = useState(null);
  const [geminiConfigured, setGeminiConfigured] = useState(true);
  const [messages, setMessages] = useState([]);
  const [knownVariables, setKnownVariables] = useState({});
  const [sending, setSending] = useState(false);
  // Mirrors sessionId for use inside async handlers without a stale closure —
  // state updates from a just-completed recovery aren't visible to the same tick.
  const sessionIdRef = useRef(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("rc_theme", dark ? "dark" : "light");
  }, [dark]);

  const adoptSession = (id) => {
    sessionIdRef.current = id;
    setSessionId(id);
    sessionStorage.setItem("rc_session", id);
  };

  useEffect(() => {
    (async () => {
      try {
        const stored = sessionStorage.getItem("rc_session");
        if (stored) {
          sessionIdRef.current = stored;
          setSessionId(stored);
        } else {
          const data = await api.createSession();
          adoptSession(data.session_id);
        }
        const status = await api.status();
        setGeminiConfigured(status.gemini_configured);
      } catch (e) {
        toast.error("Could not reach the ROOTCAUSE server.");
      }
    })();
  }, []);

  // Free-tier hosts spin the server down after inactivity; when it wakes back
  // up, its in-memory session store is empty even though this tab's
  // sessionStorage still has the old id. Rather than surface that as a raw
  // "unknown session" error, get a fresh session and retry once transparently.
  const withSessionRecovery = async (call) => {
    try {
      return await call(sessionIdRef.current);
    } catch (e) {
      if (e.status === 404) {
        const data = await api.createSession();
        adoptSession(data.session_id);
        toast("Reconnected — the server restarted, so site variables were reset.", { icon: "🔄" });
        return await call(sessionIdRef.current);
      }
      throw e;
    }
  };

  const sendMessage = async (text) => {
    if (!sessionIdRef.current) return;
    setMessages((m) => [...m, { id: nextId(), role: "user", text }]);
    const pendingId = nextId();
    setMessages((m) => [...m, { id: pendingId, role: "assistant", text: "", pending: true }]);
    setSending(true);
    try {
      const result = await withSessionRecovery((sid) => api.chat(sid, text));
      setKnownVariables(result.known_variables || {});
      setMessages((m) =>
        m.map((msg) => (msg.id === pendingId ? { id: pendingId, role: "assistant", text: result.text, meta: result } : msg))
      );
    } catch (e) {
      setMessages((m) =>
        m.map((msg) =>
          msg.id === pendingId
            ? { id: pendingId, role: "assistant", text: "Something went wrong reaching the server. Please try again." }
            : msg
        )
      );
      toast.error(e.message || "Request failed");
    } finally {
      setSending(false);
    }
  };

  const applyJson = async (variables) => {
    if (!sessionIdRef.current) return;
    const data = await withSessionRecovery((sid) => api.setVariables(sid, variables));
    setKnownVariables(data.known_variables || {});
  };

  const reset = async () => {
    if (!sessionIdRef.current) return;
    await withSessionRecovery((sid) => api.reset(sid));
    setMessages([]);
    setKnownVariables({});
  };

  return (
    <div className="min-h-screen bg-[#f8faf7] text-[#16221c] dark:bg-[#0b120d] dark:text-[#eef1ea]">
      <Toaster position="top-center" toastOptions={{ style: { fontSize: 13 } }} />
      <Header dark={dark} onToggleDark={() => setDark((d) => !d)} />
      <Hero />
      <main className="mx-auto grid max-w-5xl grid-cols-1 gap-5 px-5 py-8 lg:grid-cols-[1fr_300px]">
        <ChatPanel messages={messages} onSend={sendMessage} sending={sending} geminiConfigured={geminiConfigured} />
        <Sidebar knownVariables={knownVariables} onApplyJson={applyJson} onReset={reset} />
      </main>
    </div>
  );
}
