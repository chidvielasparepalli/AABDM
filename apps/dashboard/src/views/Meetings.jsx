import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useApi } from "../api";
import { GlassCard, GlassButton, GlassBadge, EmptyState } from "../components/Glass";
import { Loading } from "../components/Spinner";
import { dateTime } from "../lib/format";

const STATUS_COLOR = {
  booked: "amber",
  confirmed: "cyan",
  done: "gray",
  cancelled: "red",
};

export default function Meetings() {
  const api = useApi();
  const [meetings, setMeetings] = useState(null);
  const [upcomingOnly, setUpcomingOnly] = useState(false);
  const [error, setError] = useState(null);

  const load = () =>
    api
      .get(`/meetings?upcoming_only=${upcomingOnly}`)
      .then(setMeetings)
      .catch((ex) => setError(ex.message || "Failed to load meetings."));

  useEffect(() => {
    load();
  }, [upcomingOnly]);

  async function setStatus(m, status) {
    try {
      await api.post(`/meetings/${m.id}/status`, { status });
      load();
    } catch (ex) {
      setError(ex.message);
    }
  }

  return (
    <div className="animate-fade-up space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Calendar</p>
          <h1 className="page-title">Meetings</h1>
          <p className="mt-1 text-sm text-ink-dim">Booked automatically when a call closes positively.</p>
        </div>
        <div className="flex gap-1 rounded-xl border border-glass-line bg-black/20 p-1">
          {[false, true].map((u) => (
            <button
              key={u}
              onClick={() => setUpcomingOnly(u)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
                upcomingOnly === u ? "bg-white/[0.10] text-white" : "text-ink-dim hover:text-ink"
              }`}
            >
              {u ? "Upcoming" : "All"}
            </button>
          ))}
        </div>
      </header>

      {error && <p className="text-sm text-red-300">{error}</p>}
      {!meetings && !error && <Loading />}

      {meetings && !meetings.length && (
        <GlassCard>
          <EmptyState
            title={upcomingOnly ? "No upcoming meetings" : "No meetings yet"}
            hint="Run a call that ends positively and Ava books the next slot automatically."
          />
        </GlassCard>
      )}

      <div className="space-y-3">
        {meetings?.map((m) => (
          <GlassCard key={m.id} className="flex flex-wrap items-center justify-between gap-4 p-4" hover>
            <div>
              <p className="font-display font-medium text-white">{m.title}</p>
              <p className="mt-0.5 text-sm text-ink-dim">{dateTime(m.scheduled_at)}</p>
            </div>
            <div className="flex items-center gap-3">
              <Link to={`/clients/${m.client_id}`} className="text-xs text-ink-faint hover:text-aurora-violet">
                Client #{m.client_id} →
              </Link>
              <GlassBadge color={STATUS_COLOR[m.status] ?? "gray"}>{m.status}</GlassBadge>
              {m.status !== "cancelled" && m.status !== "done" && (
                <div className="flex gap-2">
                  {m.status === "booked" && (
                    <GlassButton variant="ghost" onClick={() => setStatus(m, "confirmed")}>
                      Confirm
                    </GlassButton>
                  )}
                  <GlassButton variant="danger" onClick={() => setStatus(m, "cancelled")}>
                    Cancel
                  </GlassButton>
                </div>
              )}
            </div>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}
