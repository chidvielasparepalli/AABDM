import { useEffect, useState } from "react";

import { useApi } from "../api";
import { GlassCard, GlassBadge, EmptyState } from "../components/Glass";
import { StatCard } from "../components/StatCard";
import { Loading } from "../components/Spinner";
import { dateTime } from "../lib/format";

export default function Learning() {
  const api = useApi();
  const [stats, setStats] = useState(null);
  const [entries, setEntries] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get("/learning/stats").then(setStats).catch(setError);
    api.get("/learning").then(setEntries).catch(() => setEntries([]));
  }, []);

  if (error)
    return <EmptyState title="Couldn't load learning" hint={error.message} />;
  if (!stats) return <Loading label="Loading learning loop…" />;

  return (
    <div className="animate-fade-up space-y-6">
      <header>
        <p className="eyebrow">Self-learning</p>
        <h1 className="page-title">What Ava learned</h1>
        <p className="mt-1 text-sm text-ink-dim">
          Each call is reviewed — objections, strategies, and lessons accumulate here.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Calls reviewed" value={stats.total_reviews} accent="violet" />
        <StatCard label="Avg success score" value={stats.avg_score} accent="cyan" />
        <StatCard label="Objection types" value={stats.top_objections.length} accent="amber" />
        <StatCard label="Strategies" value={stats.strategies.length} accent="white" />
      </section>

      {stats.total_reviews === 0 ? (
        <GlassCard>
          <EmptyState
            title="No calls reviewed yet"
            hint="Every completed call gets a review — objection, strategy, and a lesson for the next one."
          />
        </GlassCard>
      ) : (
        <>
          <section className="grid gap-6 lg:grid-cols-2">
            {["top_objections", "strategies"].map((key) => (
              <GlassCard key={key} className="p-5">
                <h2 className="mb-4 font-display text-base font-semibold capitalize text-white">
                  {key.replace("_", " ")}
                </h2>
                {stats[key].length ? (
                  <ul className="space-y-2.5">
                    {stats[key].map((item) => (
                      <li key={item.objection ?? item.strategy} className="flex items-center justify-between">
                        <span className="text-sm text-ink-dim">{item.objection ?? item.strategy}</span>
                        <GlassBadge color="violet" dot={false}>{item.count}</GlassBadge>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-ink-faint">None yet</p>
                )}
              </GlassCard>
            ))}
          </section>

          <GlassCard className="overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-glass-line text-[11px] uppercase tracking-[0.12em] text-ink-faint">
                    <th className="px-5 py-3 font-medium">Outcome</th>
                    <th className="hidden px-5 py-3 font-medium md:table-cell">Score</th>
                    <th className="hidden px-5 py-3 font-medium sm:table-cell">Objection</th>
                    <th className="px-5 py-3 font-medium">Lesson</th>
                    <th className="px-5 py-3 text-right font-medium">Reviewed</th>
                  </tr>
                </thead>
                <tbody>
                  {(entries ?? []).map((e) => (
                    <tr key={e.id} className="border-b border-glass-line/60 transition-colors last:border-0 hover:bg-white/[0.03]">
                      <td className="px-5 py-3.5">
                        <GlassBadge color={e.outcome?.includes("Meeting") ? "cyan" : "gray"} dot={false}>
                          {e.outcome ?? "—"}
                        </GlassBadge>
                      </td>
                      <td className="hidden px-5 py-3.5 font-mono text-ink md:table-cell">
                        {e.success_score != null ? `${e.success_score}/100` : "—"}
                      </td>
                      <td className="hidden px-5 py-3.5 text-ink-dim sm:table-cell">{e.objection ?? "—"}</td>
                      <td className="px-5 py-3.5 text-ink-dim">{e.lesson}</td>
                      <td className="px-5 py-3.5 text-right text-ink-faint">{dateTime(e.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
