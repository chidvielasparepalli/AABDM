import { GlassCard } from "./Glass";

export function StatCard({ label, value, sub, accent = "violet" }) {
  const ring = {
    violet: "text-aurora-violet",
    cyan: "text-aurora-cyan",
    amber: "text-aurora-amber",
    white: "text-white",
  }[accent];

  return (
    <GlassCard className="p-5" hover>
      <div className="flex items-start justify-between">
        <p className="eyebrow">{label}</p>
        <span className={`h-1.5 w-1.5 rounded-full bg-current ${ring} opacity-70`} />
      </div>
      <p className="mt-3 font-display text-3xl font-semibold tracking-tight text-white">{value}</p>
      {sub && <p className="mt-1 text-xs text-ink-faint">{sub}</p>}
    </GlassCard>
  );
}
