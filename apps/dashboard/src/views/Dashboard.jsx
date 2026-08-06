import { useEffect, useState } from "react";

import { useApi } from "../api";
import { GlassCard, EmptyState } from "../components/Glass";
import { StatCard } from "../components/StatCard";
import { CallsAreaChart, LeadBarChart } from "../components/Chart";
import { Loading } from "../components/Spinner";
import { usd } from "../lib/format";

export default function Dashboard() {
  const api = useApi();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .get("/analytics")
      .then(setData)
      .catch(setError);
  }, []);

  if (error)
    return (
      <EmptyState
        title="Couldn't load analytics"
        hint={error.message}
        action={
          <button className="glass-btn-ghost" onClick={() => location.reload()}>
            Retry
          </button>
        }
      />
    );
  if (!data) return <Loading label="Loading control room…" />;

  const { kpis, calls_series, lead_quality, revenue_series, ai_learning } = data;

  return (
    <div className="animate-fade-up space-y-6">
      <header>
        <p className="eyebrow">Command center</p>
        <h1 className="page-title">Pipeline health</h1>
        <p className="mt-1 text-sm text-ink-dim">
          Calls, conversions, and lead flow across {calls_series.length} days.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total calls" value={kpis.total_calls} accent="violet" />
        <StatCard label="Conversion rate" value={`${kpis.conversion_rate}%`} accent="cyan" />
        <StatCard label="Meetings booked" value={kpis.meetings_booked} sub={`${kpis.meetings_confirmed} confirmed`} accent="amber" />
        <StatCard label="Pipeline value" value={usd(kpis.revenue)} sub={`Avg budget ${usd(kpis.avg_budget)}`} accent="white" />
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <GlassCard className="p-5 lg:col-span-2">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 className="font-display text-base font-semibold text-white">Call activity</h2>
            <span className="text-xs text-ink-faint">Last 14 days</span>
          </div>
          <CallsAreaChart data={calls_series} />
        </GlassCard>

        <GlassCard className="p-5">
          <h2 className="mb-4 font-display text-base font-semibold text-white">Lead quality</h2>
          {lead_quality.length ? (
            <LeadBarChart data={lead_quality} />
          ) : (
            <p className="py-16 text-center text-sm text-ink-faint">No clients yet</p>
          )}
        </GlassCard>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        <GlassCard className="p-5">
          <h2 className="mb-3 font-display text-base font-semibold text-white">Revenue estimate</h2>
          <p className="font-display text-3xl font-semibold text-white">{usd(kpis.revenue)}</p>
          <p className="mt-1 text-xs text-ink-faint">Proposal + Closed client budgets</p>
          <div className="mt-4 h-px bg-glass-line" />
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-ink-dim">14-day pipeline</dt>
              <dd className="text-white">{usd(revenue_series.reduce((a, r) => a + r.revenue, 0))}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-dim">Strategies updated</dt>
              <dd className="text-white">{ai_learning[0].value}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-dim">Objections learned</dt>
              <dd className="text-white">{ai_learning[1].value}</dd>
            </div>
          </dl>
        </GlassCard>

        <GlassCard className="p-5 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-base font-semibold text-white">Notes</h2>
            <span className="text-xs text-ink-faint">Ava · AI BDM</span>
          </div>
          <ul className="space-y-3 text-sm text-ink-dim">
            <li className="rounded-xl border border-glass-line bg-white/[0.03] p-3">
              <span className="text-white">Start a call</span> from any client to let Ava run a
              discovery conversation — she books meetings and drafts follow-ups automatically.
            </li>
            <li className="rounded-xl border border-glass-line bg-white/[0.03] p-3">
              <span className="text-white">Run research</span> on a client with a website to get
              SEO scores, tech stack, and opportunity analysis.
            </li>
            <li className="rounded-xl border border-glass-line bg-white/[0.03] p-3">
              Revenue tracking and AI learning stats are live once calls close and follow-ups send.
            </li>
          </ul>
        </GlassCard>
      </section>
    </div>
  );
}
