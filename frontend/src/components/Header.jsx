import { Code2, Moon, Sprout, Sun } from "lucide-react";

export default function Header({ dark, onToggleDark }) {
  return (
    <header className="sticky top-0 z-20 border-b border-black/5 bg-white/80 backdrop-blur-md dark:border-white/10 dark:bg-forest-950/80">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3.5">
        <div className="flex items-center gap-3">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-forest-500 to-forest-800 text-white shadow-md shadow-forest-600/25">
            <Sprout size={18} strokeWidth={2.5} />
          </span>
          <div>
            <div className="font-display text-[15px] font-bold leading-tight text-forest-900 dark:text-forest-100">
              ROOTCAUSE
            </div>
            <div className="text-[11px] text-black/45 dark:text-white/40">
              Causal Consistency for Biodiversity Advisory
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <a
            href="https://github.com/Rayyan-mohammed/eco-causal"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-[13px] font-medium text-black/60 transition hover:bg-black/5 hover:text-black dark:text-white/60 dark:hover:bg-white/10 dark:hover:text-white"
          >
            <Code2 size={15} />
            Source
          </a>
          <button
            onClick={onToggleDark}
            aria-label="Toggle color theme"
            className="grid h-9 w-9 place-items-center rounded-lg text-black/60 transition hover:bg-black/5 hover:text-black dark:text-white/60 dark:hover:bg-white/10 dark:hover:text-white"
          >
            {dark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </header>
  );
}
