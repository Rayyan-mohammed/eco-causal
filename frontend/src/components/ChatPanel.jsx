import { AnimatePresence } from "framer-motion";
import { Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";

const EXAMPLE =
  "I farm monoculture wheat on a semi-arid plot with rainfall around 280mm and soil organic carbon of about 0.4 percent. Biodiversity is declining, what should I do?";

export default function ChatPanel({ messages, onSend, sending, geminiConfigured }) {
  const [input, setInput] = useState("");
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages, sending]);

  const submit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    onSend(text);
    setInput("");
  };

  return (
    <div className="flex h-[70vh] flex-col overflow-hidden rounded-2xl border border-black/5 bg-white/70 shadow-sm backdrop-blur-sm dark:border-white/10 dark:bg-white/[0.03]">
      {!geminiConfigured && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-[12.5px] text-amber-800 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200">
          GEMINI_API_KEY is not set on the server — chat requests will fail until it's configured.
        </div>
      )}

      <div ref={logRef} className="flex-1 space-y-4 overflow-y-auto p-5">
        {messages.length === 0 && (
          <p className="pt-8 text-center text-[13.5px] italic text-black/35 dark:text-white/30">
            Describe your site — for example: &ldquo;{EXAMPLE}&rdquo;
          </p>
        )}
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <MessageBubble key={m.id} role={m.role} text={m.text} meta={m.meta} pending={m.pending} />
          ))}
        </AnimatePresence>
      </div>

      <form onSubmit={submit} className="flex gap-2 border-t border-black/5 p-3.5 dark:border-white/10">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Describe your site and what you're concerned about…"
          className="flex-1 rounded-xl border border-black/10 bg-black/[0.02] px-3.5 py-2.5 text-[14px] outline-none focus:border-forest-400 dark:border-white/10 dark:bg-black/20 dark:text-white/90"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="flex items-center gap-1.5 rounded-xl bg-forest-700 px-4 py-2.5 text-[14px] font-semibold text-white transition hover:bg-forest-800 disabled:opacity-40 disabled:hover:bg-forest-700"
        >
          <Send size={15} />
          Send
        </button>
      </form>
    </div>
  );
}
