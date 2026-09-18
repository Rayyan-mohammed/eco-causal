import { motion } from "framer-motion";
import { ArrowRight, ScanSearch, ShieldCheck, Sparkles } from "lucide-react";

const STEPS = [
  { icon: ScanSearch, label: "Retrieve", desc: "Search the sourced knowledge base" },
  { icon: Sparkles, label: "Draft", desc: "Generate a multi-variable recommendation" },
  { icon: ShieldCheck, label: "Verify", desc: "Check the claim against the causal map" },
];

export default function Hero() {
  return (
    <section className="border-b border-black/5 bg-gradient-to-b from-forest-50 to-white dark:border-white/10 dark:from-forest-950 dark:to-[#0b120d]">
      <div className="mx-auto max-w-3xl px-5 py-12 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="font-display text-[26px] font-bold leading-tight text-forest-900 sm:text-[30px] dark:text-forest-50"
        >
          A biodiversity advisor that checks its own reasoning
          <br className="hidden sm:block" /> before it answers you.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08 }}
          className="mx-auto mt-4 max-w-xl text-[15px] leading-relaxed text-black/55 dark:text-white/55"
        >
          Standard RAG chatbots verify that a fact exists in a source. ROOTCAUSE goes
          further: every multi-variable recommendation is extracted into a causal chain
          and checked, edge by edge, against a source-cited map.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.16 }}
          className="mt-9 flex items-center justify-center gap-1.5 sm:gap-3"
        >
          {STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-1.5 sm:gap-3">
              <div className="flex flex-col items-center gap-1.5 rounded-2xl bg-white/70 px-3 py-2.5 shadow-sm ring-1 ring-black/5 sm:px-4 sm:py-3 dark:bg-white/5 dark:ring-white/10">
                <step.icon size={18} className="text-forest-600 dark:text-forest-300" strokeWidth={2.25} />
                <div className="text-[11.5px] font-semibold text-forest-900 dark:text-forest-100">{step.label}</div>
              </div>
              {i < STEPS.length - 1 && <ArrowRight size={14} className="text-black/25 dark:text-white/25" />}
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
