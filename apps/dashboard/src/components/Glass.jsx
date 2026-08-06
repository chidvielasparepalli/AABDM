export function GlassCard({ className = "", hover = false, children, ...rest }) {
  return (
    <div
      className={`glass grain ${hover ? "glass-hover" : ""} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export function GlassButton({ variant = "primary", className = "", children, ...rest }) {
  const cls = {
    primary: "glass-btn-primary",
    ghost: "glass-btn-ghost",
    danger: "glass-btn-danger",
  }[variant];
  return (
    <button className={`${cls} ${className}`} {...rest}>
      {children}
    </button>
  );
}

export function GlassInput({ label, hint, className = "", ...rest }) {
  return (
    <label className={`block ${className}`}>
      {label && <span className="mb-1.5 block text-xs font-medium text-ink-dim">{label}</span>}
      <input className="glass-input" {...rest} />
      {hint && <span className="mt-1 block text-xs text-ink-faint">{hint}</span>}
    </label>
  );
}

const BADGE_COLORS = {
  gray: "border-white/10 bg-white/[0.05] text-ink-dim",
  violet: "border-aurora-violet/30 bg-aurora-violet/10 text-aurora-violet",
  cyan: "border-aurora-cyan/30 bg-aurora-cyan/10 text-aurora-cyan",
  amber: "border-aurora-amber/30 bg-aurora-amber/10 text-aurora-amber",
  green: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  red: "border-red-400/30 bg-red-400/10 text-red-300",
};

export function GlassBadge({ color = "gray", dot = true, children }) {
  return (
    <span className={`glass-badge ${BADGE_COLORS[color]}`}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

export function EmptyState({ title, hint, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <div className="text-3xl opacity-40">✦</div>
      <p className="font-display text-lg font-medium text-ink">{title}</p>
      {hint && <p className="max-w-sm text-sm text-ink-faint">{hint}</p>}
      {action}
    </div>
  );
}
