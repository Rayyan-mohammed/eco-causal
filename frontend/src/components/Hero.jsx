import { motion } from "framer-motion";
import { ArrowRight, ScanSearch, ShieldCheck, Sparkles } from "lucide-react";

const STEPS = [
  { icon: ScanSearch, label: "Retrieve", desc: "Search the sourced knowledge base" },
  { icon: Sparkles, label: "Draft", desc: "Generate a multi-variable recommendation" },
  { icon: ShieldCheck, label: "Verify", desc: "Check the claim against the causal map" },
];

export default function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-black/5 dark:border-white/10">
      <div className="mesh-bg absolute inset-0" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-white dark:to-[#0b120d]" />

      <div className="relative mx-auto max-w-3xl px-5 pb-16 pt-14 text-center sm:pt-20">
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
          className="font-display text-[32px] font-extrabold leading-[1.15] tracking-tight text-forest-950 sm:text-[42px] dark:text-white"
        >
          A biodiversity advisor that{" "}
          <span className="bg-gradient-to-r from-forest-600 via-forest-500 to-sky-400 bg-clip-text text-transparent">
            checks its own reasoning
          </span>{" "}
          before it answers you.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.12 }}
          className="mx-auto mt-4 max-w-xl text-[15.5px] leading-relaxed text-black/55 dark:text-white/55"
        >
          Standard RAG chatbots verify that a fact exists in a source. ROOTCAUSE goes
          further: every multi-variable recommendation is extracted into a causal chain
          and checked, edge by edge, against a source-cited map.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-10 flex items-center justify-center gap-1.5 sm:gap-3"
        >
          {STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-1.5 sm:gap-3">
              <div className="glass group flex flex-col items-center gap-2 rounded-2xl border border-black/5 px-4 py-3.5 shadow-[0_2px_10px_rgba(20,63,41,0.06)] transition hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(20,63,41,0.14)] sm:px-5 sm:py-4 dark:border-white/10">
                <span className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-forest-500 to-forest-700 text-white shadow-sm">
                  <step.icon size={16} strokeWidth={2.25} />
                </span>
                <div className="text-[12px] font-bold text-forest-900 dark:text-forest-50">{step.label}</div>
              </div>
              {i < STEPS.length - 1 && <ArrowRight size={14} className="text-black/25 dark:text-white/25" />}
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
