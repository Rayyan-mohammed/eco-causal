import { AnimatePresence, motion } from "framer-motion";
import { Bug, Droplets, Send, Sparkles, Trees } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";

const EXAMPLES = [
  {
    icon: Sparkles,
    title: "Semi-arid monoculture wheat",
    text: "I farm monoculture wheat on a semi-arid plot with rainfall around 280mm and soil organic carbon of about 0.4 percent. Biodiversity is declining, what should I do?",
  },
  {
    icon: Droplets,
    title: "Salt buildup from irrigation",
    text: "I irrigate heavily in a very dry climate. Could that be affecting my yields through salt buildup?",
  },
  {
    icon: Bug,
    title: "Fewer bees near the orchard",
    text: "I spray my orchard regularly for pests. Could that be why I'm seeing fewer bees?",
  },
  {
    icon: Trees,
    title: "Overgrazed rangeland",
    text: "My rangeland has been heavily grazed. Is that compacting my soil, and is it hurting my pollinators too?",
  },
];

function EmptyState({ onPick }) {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 py-10 text-center">
      <span className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-forest-500 to-forest-700 text-white shadow-lg shadow-forest-600/20">
        <Sparkles size={20} />
      </span>
      <h3 className="font-display text-[17px] font-bold text-forest-950 dark:text-white">
        Describe your site, or try an example
      </h3>
      <p className="mt-1.5 max-w-sm text-[13px] text-black/45 dark:text-white/40">
        Every recommendation gets checked against the causal map before you see it.
      </p>

      <div className="mt-7 grid w-full max-w-lg grid-cols-1 gap-2.5 sm:grid-cols-2">
        {EXAMPLES.map((ex, i) => (
          <motion.button
            key={ex.title}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.06 * i, duration: 0.3 }}
            onClick={() => onPick(ex.text)}
            className="group flex items-start gap-2.5 rounded-xl border border-black/5 bg-white/70 p-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-forest-300 hover:shadow-md dark:border-white/10 dark:bg-white/[0.04] dark:hover:border-forest-600"
          >
            <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-forest-50 text-forest-600 transition group-hover:bg-forest-600 group-hover:text-white dark:bg-forest-900/50 dark:text-forest-300">
              <ex.icon size={14} />
            </span>
            <span className="text-[12.5px] font-medium leading-snug text-forest-900 dark:text-white/85">
              {ex.title}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

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
    <div className="flex h-[70vh] flex-col overflow-hidden rounded-2xl border border-black/5 bg-white/70 shadow-[0_2px_16px_rgba(20,63,41,0.05)] backdrop-blur-sm dark:border-white/10 dark:bg-white/[0.03]">
      {!geminiConfigured && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-[12.5px] text-amber-800 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200">
          GEMINI_API_KEY is not set on the server — chat requests will fail until it's configured.
        </div>
      )}

      <div ref={logRef} className="flex-1 space-y-4 overflow-y-auto p-5">
        {messages.length === 0 ? (
          <EmptyState onPick={(text) => onSend(text)} />
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <MessageBubble key={m.id} role={m.role} text={m.text} meta={m.meta} pending={m.pending} />
            ))}
          </AnimatePresence>
        )}
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
          className="flex items-center gap-1.5 rounded-xl bg-gradient-to-br from-forest-600 to-forest-800 px-4 py-2.5 text-[14px] font-semibold text-white shadow-sm transition hover:brightness-110 disabled:opacity-40 disabled:hover:brightness-100"
        >
          <Send size={15} />
          Send
        </button>
      </form>
    </div>
  );
}
