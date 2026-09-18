import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";

const CONFIG = {
  accepted: {
    icon: CheckCircle2,
    label: "Accepted",
    className: "bg-forest-100 text-forest-700 dark:bg-forest-900/60 dark:text-forest-200",
  },
  downgraded: {
    icon: AlertTriangle,
    label: "Downgraded",
    className: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
  },
  rejected: {
    icon: XCircle,
    label: "Rejected",
    className: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200",
  },
};

export default function StatusBadge({ status, confidence }) {
  const cfg = CONFIG[status];
  if (!cfg) return null;
  const Icon = cfg.icon;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-semibold ${cfg.className}`}>
        <Icon size={13} strokeWidth={2.5} />
        {cfg.label}
      </span>
      <span className="text-black/40 dark:text-white/40">confidence: {confidence}</span>
    </div>
  );
}
