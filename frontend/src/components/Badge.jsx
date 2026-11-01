export default function Badge({ value }) {
  const color = {
    HIGH: "bg-red-100 text-red-700",
    MEDIUM: "bg-amber-100 text-amber-700",
    LOW: "bg-emerald-100 text-emerald-700",
    OPEN: "bg-blue-100 text-blue-700",
    INVESTIGATING: "bg-violet-100 text-violet-700",
    IN_PROGRESS: "bg-violet-100 text-violet-700",
    RESOLVED: "bg-emerald-100 text-emerald-700",
    CLOSED: "bg-slate-100 text-slate-600",
    SHORTAGE: "bg-red-100 text-red-700",
    MATCHED: "bg-emerald-100 text-emerald-700",
    SURPLUS: "bg-sky-100 text-sky-700",
    healthy: "bg-emerald-100 text-emerald-700",
    connected: "bg-emerald-100 text-emerald-700",
    error: "bg-red-100 text-red-700",
  }[value] || "bg-slate-100 text-slate-600";

  return (
    <span className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${color}`}>
      {value || "—"}
    </span>
  );
}
