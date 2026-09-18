import { motion } from "framer-motion";
import { Check, Copy, ListTree, RotateCcw, Sparkle } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";

const PLACEHOLDER = `{
  "soil_organic_carbon": 0.4,
  "rainfall_level": 250,
  "land_use": "monoculture wheat",
  "latitude": 17.4,
  "longitude": 78.5
}`;

function VariableRow({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-black/5 py-2 text-[12.5px] last:border-0 dark:border-white/10">
      <span className="text-black/45 dark:text-white/40">{label.replaceAll("_", " ")}</span>
      <span className="font-medium text-forest-900 dark:text-forest-100">{String(value)}</span>
    </div>
  );
}

function Card({ children, className = "" }) {
  return (
    <div
      className={`rounded-2xl border border-black/5 bg-white/80 p-4 shadow-[0_2px_14px_rgba(20,63,41,0.05)] backdrop-blur-sm dark:border-white/10 dark:bg-white/[0.04] ${className}`}
    >
      {children}
    </div>
  );
}

function IconBadge({ Icon }) {
  return (
    <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-forest-500 to-forest-700 text-white shadow-sm shadow-forest-600/20">
      <Icon size={13} />
    </span>
  );
}

function CopyButton({ getText, label = "Copy" }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(getText());
      setCopied(true);
      toast.success("Copied to clipboard");
      setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Couldn't copy — try selecting the text manually");
    }
  };

  return (
    <button
      onClick={copy}
      className="ml-auto flex items-center gap-1 rounded-md px-1.5 py-1 text-[11px] font-medium text-black/40 transition hover:bg-black/5 hover:text-forest-700 dark:text-white/35 dark:hover:bg-white/10 dark:hover:text-forest-300"
      title={label}
    >
      {copied ? <Check size={12} className="text-forest-600 dark:text-forest-300" /> : <Copy size={12} />}
      {copied ? "Copied" : label}
    </button>
  );
}

export default function Sidebar({ knownVariables, onApplyJson, onReset }) {
  const [jsonText, setJsonText] = useState("");
  const entries = Object.entries(knownVariables || {});

  const applyJson = () => {
    if (!jsonText.trim()) return;
    try {
      const parsed = JSON.parse(jsonText);
      onApplyJson(parsed);
      toast.success("Variables applied");
      setJsonText("");
    } catch (e) {
      toast.error(`Invalid JSON: ${e.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <div className="mb-3 flex items-center gap-2.5">
          <IconBadge Icon={ListTree} />
          <h3 className="font-display text-[13px] font-bold text-forest-900 dark:text-forest-100">
            Known site variables
          </h3>
          {entries.length > 0 && (
            <CopyButton getText={() => JSON.stringify(knownVariables, null, 2)} />
          )}
        </div>
        {entries.length === 0 ? (
          <p className="text-[12px] leading-relaxed text-black/40 dark:text-white/35">
            None yet — these fill in as the conversation progresses.
          </p>
        ) : (
          <motion.div layout>
            {entries.map(([k, v]) => (
              <VariableRow key={k} label={k} value={v} />
            ))}
          </motion.div>
        )}
      </Card>

      <Card>
        <div className="mb-2 flex items-center gap-2.5">
          <IconBadge Icon={Sparkle} />
          <h3 className="font-display text-[13px] font-bold text-forest-900 dark:text-forest-100">
            Structured JSON input
          </h3>
          <CopyButton getText={() => jsonText.trim() || PLACEHOLDER} label="Copy example" />
        </div>
        <p className="mb-2.5 text-[11.5px] leading-relaxed text-black/45 dark:text-white/35">
          Submit site variables directly instead of free text. Geo-coordinates are
          inferred into a climate zone.
        </p>
        <textarea
          value={jsonText}
          onChange={(e) => setJsonText(e.target.value)}
          rows={6}
          placeholder={PLACEHOLDER}
          className="w-full resize-y rounded-lg border border-black/10 bg-black/[0.02] p-2.5 font-mono text-[11px] text-forest-950 outline-none focus:border-forest-400 dark:border-white/10 dark:bg-black/20 dark:text-white/85"
        />
        <div className="mt-2.5 flex gap-2">
          <button
            onClick={() => setJsonText(PLACEHOLDER)}
            className="rounded-lg border border-black/10 px-3 py-2 text-[12px] font-medium text-black/55 transition hover:bg-black/5 dark:border-white/10 dark:text-white/55 dark:hover:bg-white/10"
          >
            Use example
          </button>
          <button
            onClick={applyJson}
            className="flex-1 rounded-lg bg-gradient-to-br from-forest-600 to-forest-800 py-2 text-[13px] font-semibold text-white shadow-sm transition hover:brightness-110 active:scale-[0.99]"
          >
            Apply JSON
          </button>
        </div>
      </Card>

      <button
        onClick={onReset}
        className="flex items-center justify-center gap-1.5 rounded-2xl border border-black/10 bg-white/70 py-2.5 text-[13px] font-medium text-black/55 shadow-sm transition hover:bg-white dark:border-white/10 dark:bg-white/[0.04] dark:text-white/55 dark:hover:bg-white/[0.08]"
      >
        <RotateCcw size={14} />
        Reset conversation
      </button>
    </div>
  );
}
