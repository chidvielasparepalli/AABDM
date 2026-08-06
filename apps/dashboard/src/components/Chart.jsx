import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// validated dark-mode categorical palette (see dataviz skill) — #5A50C4
// carries a contrast WARN; relief = the axis labels already on the chart
const C = {
  violet: "#7668E8",
  cyan: "#2E9C88",
  amber: "#B5853B",
  deep: "#5A50C4",
};
const GRID = "rgba(255,255,255,0.06)";
const AXIS = "#5A6478";

function GlassTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass rounded-xl px-3 py-2 text-xs">
      <p className="mb-1 font-display font-medium text-white">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="flex items-center gap-2 text-ink-dim">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="capitalize">{p.name}</span>
          <span className="ml-auto pl-3 font-medium text-white">{p.value}</span>
        </p>
      ))}
    </div>
  );
}

const axisProps = {
  stroke: AXIS,
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

// calls over 14 days — two series, thin area marks
export function CallsAreaChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="callsFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.violet} stopOpacity={0.35} />
            <stop offset="100%" stopColor={C.violet} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="posFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.cyan} stopOpacity={0.3} />
            <stop offset="100%" stopColor={C.cyan} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} strokeDasharray="3 6" vertical={false} />
        <XAxis dataKey="date" {...axisProps} />
        <YAxis {...axisProps} allowDecimals={false} />
        <Tooltip content={<GlassTooltip />} cursor={{ stroke: GRID, strokeWidth: 1 }} />
        <Area
          type="monotone"
          dataKey="calls"
          name="Calls"
          stroke={C.violet}
          strokeWidth={2}
          fill="url(#callsFill)"
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
        <Area
          type="monotone"
          dataKey="positive"
          name="Positive"
          stroke={C.cyan}
          strokeWidth={2}
          fill="url(#posFill)"
          dot={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

const LEAD_COLORS = [C.violet, C.cyan, C.amber, C.deep];

// lead quality — categorical bars, fixed hue order
export function LeadBarChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <CartesianGrid stroke={GRID} strokeDasharray="3 6" vertical={false} />
        <XAxis dataKey="status" {...axisProps} />
        <YAxis {...axisProps} allowDecimals={false} />
        <Tooltip content={<GlassTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="count" name="Clients" radius={[4, 4, 0, 0]} barSize={28}>
          {data.map((_, i) => (
            <Cell key={i} fill={LEAD_COLORS[i % LEAD_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
