import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, Clock, TrendingUp } from "lucide-react";
import { useState } from "react";
import ReasoningGraph from "./ReasoningGraph";
import StatusBadge from "./StatusBadge";

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-1">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-forest-500/70"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ repeat: Infinity, duration: 1.1, delay: i * 0.15 }}
        />
      ))}
    </div>
  );
}

const HORIZON_LABEL = { short: "Short-term", medium: "Medium-term", long: "Long-term" };

function SourcesDisclosure({ citations, stepEvidence }) {
  const [open, setOpen] = useState(false);
  const steps = stepEvidence ?? [];
  const retrieved = citations ?? [];
  if (!steps.length && !retrieved.length) return null;
  return (
    <div>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1 text-[12px] font-semibold text-forest-700 dark:text-forest-300"
      >
        <ChevronDown size={13} className={`transition-transform ${open ? "rotate-180" : ""}`} />
        Evidence &amp; sources ({steps.length + retrieved.length})
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="mt-2 space-y-3 overflow-hidden text-[11.5px] leading-relaxed text-black/50 dark:text-white/45"
          >
            {steps.length > 0 && (
              <div>
                <div className="mb-1 font-semibold text-black/60 dark:text-white/60">
                  Evidence for each step of the checked chain
                </div>
                <ol className="space-y-2 pl-4">
                  {steps.map((st, i) => (
                    <li key={i} className="list-decimal">
                      <span className="font-medium text-black/70 dark:text-white/70">
                        {st.cause} {st.direction} {st.effect}
                      </span>
                      {st.mechanism && <span> — {st.mechanism}</span>}
                      {st.citation && <div className="mt-0.5 italic">{st.citation}</div>}
                    </li>
                  ))}
                </ol>
              </div>
            )}
            {retrieved.length > 0 && (
              <div>
                <div className="mb-1 font-semibold text-black/60 dark:text-white/60">
                  Retrieved context used for drafting
                </div>
                <ul className="space-y-1.5 pl-4">
                  {retrieved.map((c, i) => (
                    <li key={i} className="list-disc">
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function MessageBubble({ role, text, meta, pending }) {
  const isUser = role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`max-w-[92%] sm:max-w-[85%] ${isUser ? "items-end" : "items-start"} flex flex-col gap-1`}>
        <span className="px-1 text-[10.5px] font-semibold uppercase tracking-wide text-black/35 dark:text-white/35">
          {isUser ? "You" : "ROOTCAUSE"}
        </span>
        <div
          className={
            isUser
              ? "rounded-2xl rounded-tr-sm bg-gradient-to-br from-forest-600 to-forest-800 px-4 py-3 text-[14px] leading-relaxed text-white shadow-md shadow-forest-700/15"
              : "rounded-2xl rounded-tl-sm border border-forest-900/5 bg-gradient-to-br from-forest-50 to-white px-4 py-3.5 text-[14px] leading-relaxed text-forest-950 shadow-[0_2px_14px_rgba(20,63,41,0.06)] dark:border-white/5 dark:from-white/[0.07] dark:to-white/[0.03] dark:text-white/90"
          }
        >
          {pending ? <TypingIndicator /> : <div className="whitespace-pre-wrap">{text}</div>}

          {meta?.checker_status && (
            <div className="mt-3.5 flex flex-col gap-3">
              {meta.impacted_metrics?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {meta.impacted_metrics.map((m) => (
                    <span
                      key={m}
                      className="rounded-full border border-black/10 bg-white px-2.5 py-1 text-[11px] font-medium text-forest-800 dark:border-white/10 dark:bg-black/20 dark:text-forest-200"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              )}

              {(meta.horizon || meta.time_horizon) && (
                <div className="flex items-center gap-1.5 text-[12px] text-black/50 dark:text-white/45">
                  <Clock size={13} />
                  <span className="font-medium text-black/70 dark:text-white/70">
                    {[HORIZON_LABEL[meta.horizon], meta.time_horizon].filter(Boolean).join(" · ")}
                  </span>
                </div>
              )}

              {meta.expected_effect && (
                <div className="flex items-start gap-1.5 rounded-lg bg-black/[0.03] px-2.5 py-2 text-[12px] leading-relaxed dark:bg-white/[0.05]">
                  <TrendingUp size={13} className="mt-0.5 shrink-0 text-forest-600 dark:text-forest-300" />
                  <span className={meta.expected_effect.startsWith("Not quantified") ? "italic text-black/45 dark:text-white/40" : "text-black/70 dark:text-white/70"}>
                    <span className="font-semibold">Expected effect: </span>
                    {meta.expected_effect}
                  </span>
                </div>
              )}

              <StatusBadge status={meta.checker_status} confidence={meta.confidence} />

              {meta.edge_results?.length > 0 && (
                <div>
                  <div className="mb-1.5 text-[11px] font-medium text-black/40 dark:text-white/40">
                    Reasoning chain checked against the causal map
                  </div>
                  <ReasoningGraph edgeResults={meta.edge_results} />
                  <div className="mt-1.5 flex gap-3 text-[10.5px] text-black/40 dark:text-white/40">
                    <span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#2f9e5c]" /> supported</span>
                    <span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#c98a1f]" /> unverified/unmet</span>
                    <span className="flex items-center gap-1"><i className="h-2 w-2 rounded-full bg-[#d1453b]" /> not documented</span>
                  </div>
                </div>
              )}

              <SourcesDisclosure citations={meta.citations} stepEvidence={meta.step_evidence} />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
