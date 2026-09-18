import { useEffect, useState } from "react";
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

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("rc_theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    (async () => {
      try {
        const stored = sessionStorage.getItem("rc_session");
        if (stored) {
          setSessionId(stored);
        } else {
          const data = await api.createSession();
          setSessionId(data.session_id);
          sessionStorage.setItem("rc_session", data.session_id);
        }
        const status = await api.status();
        setGeminiConfigured(status.gemini_configured);
      } catch (e) {
        toast.error("Could not reach the ROOTCAUSE server.");
      }
    })();
  }, []);

  const sendMessage = async (text) => {
    if (!sessionId) return;
    setMessages((m) => [...m, { id: nextId(), role: "user", text }]);
    const pendingId = nextId();
    setMessages((m) => [...m, { id: pendingId, role: "assistant", text: "", pending: true }]);
    setSending(true);
    try {
      const result = await api.chat(sessionId, text);
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
    if (!sessionId) return;
    const data = await api.setVariables(sessionId, variables);
    setKnownVariables(data.known_variables || {});
  };

  const reset = async () => {
    if (!sessionId) return;
    await api.reset(sessionId);
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
