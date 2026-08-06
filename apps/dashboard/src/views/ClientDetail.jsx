import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useApi } from "../api";
import { GlassCard, GlassButton, GlassBadge, EmptyState } from "../components/Glass";
import { Loading, Spinner } from "../components/Spinner";
import { dateTime, dur, usd } from "../lib/format";

const STATUS_COLOR = { Lead: "amber", Proposal: "violet", Closed: "cyan" };

function Tab({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-all ${
        active ? "bg-white/[0.10] text-white" : "text-ink-dim hover:text-ink"
      }`}
    >
      {children}
    </button>
  );
}

// ---------- Research ----------

function ResearchTab({ client, api }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const r = await api.get(`/clients/${client.id}/research`);
      setReport(r);
    } catch (ex) {
      if (ex.status === 404) setReport(null);
      else setError(ex.message);
    }
  }, [client.id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (report?.status === "running") {
      const t = setInterval(async () => {
        const r = await api.get(`/clients/${client.id}/research`).catch(() => null);
        if (r && r.status !== "running") {
          setReport(r);
          clearInterval(t);
        }
      }, 2000);
      return () => clearInterval(t);
    }
  }, [report?.status]);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      await api.post(`/clients/${client.id}/research`);
      setReport((prev) => ({ ...prev, status: "running" }));
      load();
    } catch (ex) {
      setError(ex.message);
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="text-sm text-red-300">{error}</p>;

  if (!report) {
    return (
      <EmptyState
        title="No research yet"
        hint={client.website ? "Run a scan to analyze their site." : "This client has no website set — add one to research them."}
        action={
          client.website ? (
            <GlassButton onClick={start} disabled={busy}>
              {busy ? <Spinner className="h-4 w-4" /> : null} Run research
            </GlassButton>
          ) : null
        }
      />
    );
  }

  if (report.status === "running") {
    return (
      <div className="flex flex-col items-center gap-3 py-12">
        <Spinner className="h-6 w-6 text-aurora-violet" />
        <p className="text-sm text-ink-dim">Ava is scanning {report.url}…</p>
      </div>
    );
  }

  if (report.status === "error") {
    return (
      <EmptyState
        title="Research failed"
        hint={report.error}
        action={<GlassButton onClick={start} disabled={busy}>Retry</GlassButton>}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <GlassBadge color="violet">SEO {report.seo_score ?? "—"}/100</GlassBadge>
        <GlassBadge color="cyan">Speed {report.performance_score ?? "—"}/100</GlassBadge>
      </div>

      {report.tech_stack?.length > 0 && (
        <div>
          <p className="eyebrow mb-2">Tech stack</p>
          <div className="flex flex-wrap gap-2">
            {report.tech_stack.map((t) => (
              <span key={t} className="rounded-full border border-glass-line bg-white/[0.04] px-3 py-1 text-xs text-ink-dim">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {report.opportunities?.length > 0 && (
          <div className="rounded-xl border border-glass-line bg-white/[0.03] p-4">
            <p className="eyebrow mb-2">Opportunities</p>
            <ul className="list-disc space-y-1 pl-4 text-sm text-ink-dim">
              {report.opportunities.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
          </div>
        )}
        {report.missing_features?.length > 0 && (
          <div className="rounded-xl border border-glass-line bg-white/[0.03] p-4">
            <p className="eyebrow mb-2">Missing features</p>
            <ul className="list-disc space-y-1 pl-4 text-sm text-ink-dim">
              {report.missing_features.map((f) => (
                <li key={f}>{f}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------- BI ----------

function BiPanel({ bi }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative h-20 w-20">
          <svg viewBox="0 0 80 80" className="h-20 w-20 -rotate-90">
            <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="8" />
            <circle
              cx="40" cy="40" r="34" fill="none" stroke="#7668E8" strokeWidth="8" strokeLinecap="round"
              strokeDasharray={`${bi.opportunity_score * 2.13} 200`}
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center font-display text-xl font-semibold text-white">
            {bi.opportunity_score}
          </span>
        </div>
        <div>
          <p className="eyebrow">Opportunity score</p>
          <p className="mt-1 text-sm text-ink-dim">{bi.winning_strategy}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <GlassBadge color="violet">{bi.recommended_service ?? "Assessment"}</GlassBadge>
        <GlassBadge color="cyan">{usd(bi.budget_estimate.min)}–{usd(bi.budget_estimate.max)}/mo</GlassBadge>
      </div>

      {bi.swot && (
        <div className="grid gap-3 sm:grid-cols-2">
          {["strengths", "weaknesses", "opportunities", "threats"].map((k) => (
            <div key={k} className="rounded-xl border border-glass-line bg-white/[0.03] p-3">
              <p className="eyebrow mb-1.5">{k}</p>
              <ul className="list-disc space-y-0.5 pl-4 text-xs text-ink-dim">
                {bi.swot[k].map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------- Calls ----------

function CallsTab({ client, api }) {
  const [calls, setCalls] = useState(null);
  const [open, setOpen] = useState(null); // call_id of expanded transcript
  const [transcript, setTranscript] = useState({});
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(
    () => api.get(`/clients/${client.id}/calls`).then(setCalls).catch(setError),
    [client.id]
  );

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (open != null) {
      const t = setInterval(async () => {
        const c = await api.get(`/clients/${client.id}/calls/${open}`).catch(() => null);
        if (!c) return;
        setTranscript((prev) => ({ ...prev, [open]: c.transcript ?? [] }));
        if (c.status !== "running") {
          clearInterval(t);
          load();
        }
      }, 1500);
      return () => clearInterval(t);
    }
  }, [open]);

  async function start() {
    setStarting(true);
    setError(null);
    try {
      const c = await api.post(`/clients/${client.id}/calls`);
      setCalls((prev) => [c, ...(prev ?? [])]);
      setOpen(c.id);
    } catch (ex) {
      setError(ex.message);
    } finally {
      setStarting(false);
    }
  }

  if (!calls) return error ? <p className="text-sm text-red-300">{error}</p> : <Loading />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-ink-dim">{calls.length} call{calls.length === 1 ? "" : "s"} on record</p>
        <GlassButton onClick={start} disabled={starting || calls.some((c) => c.status === "running")}>
          {starting ? <Spinner className="h-4 w-4" /> : null} Start call
        </GlassButton>
      </div>

      {error && <p className="text-sm text-red-300">{error}</p>}

      {!calls.length && (
        <EmptyState
          title="No calls yet"
          hint="Start a call and Ava will run a discovery conversation with this client."
          action={<GlassButton onClick={start} disabled={starting}>Start call</GlassButton>}
        />
      )}

      {calls.map((c) => (
        <div key={c.id} className="overflow-hidden rounded-xl border border-glass-line bg-white/[0.03]">
          <button
            className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/[0.03]"
            onClick={() => setOpen(open === c.id ? null : c.id)}
          >
            <div>
              <p className="text-sm font-medium text-white">
                {dateTime(c.created_at)}
                {c.stage && <span className="ml-2 text-xs text-ink-faint">{c.stage}</span>}
              </p>
              {c.outcome && <p className="mt-0.5 text-xs text-ink-dim">{c.outcome}</p>}
            </div>
            <div className="flex items-center gap-2">
              {c.status === "running" && <Spinner className="h-3.5 w-3.5 text-aurora-violet" />}
              <GlassBadge color={c.status === "done" ? "cyan" : "amber"} dot={false}>
                {c.status}
              </GlassBadge>
              {c.duration_s != null && <span className="text-xs text-ink-faint">{dur(c.duration_s)}</span>}
            </div>
          </button>

          {open === c.id && (
            <div className="max-h-96 space-y-2 overflow-y-auto border-t border-glass-line px-4 py-3">
              {(transcript[c.id] ?? []).map((line, i) => (
                <div key={i} className={`flex ${line.role === "ai" ? "justify-start" : "justify-end"}`}>
                  <div
                    className={`max-w-[75%] rounded-xl px-3 py-2 text-sm ${
                      line.role === "ai"
                        ? "border border-aurora-violet/20 bg-aurora-violet/10 text-ink"
                        : "border border-glass-line bg-white/[0.05] text-ink-dim"
                    }`}
                  >
                    <span className="mb-0.5 block text-[10px] uppercase tracking-wider text-ink-faint">
                      {line.role === "ai" ? "Ava" : "Client"} · {line.stage}
                    </span>
                    {line.text}
                  </div>
                </div>
              ))}
              {!(transcript[c.id] ?? []).length && (
                <p className="py-4 text-center text-xs text-ink-faint">
                  {c.status === "running" ? "Call in progress…" : "No transcript"}
                </p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------- Memory ----------

function MemoryTab({ client, api }) {
  const [memories, setMemories] = useState(null);

  useEffect(() => {
    api.get(`/clients/${client.id}/memory`).then(setMemories).catch(() => setMemories([]));
  }, [client.id]);

  if (!memories) return <Loading />;

  if (!memories.length)
    return <EmptyState title="Nothing remembered yet" hint="Facts Ava learns from calls appear here." />;

  return (
    <ul className="space-y-2">
      {memories.map((m) => (
        <li key={m.id} className="rounded-xl border border-glass-line bg-white/[0.03] px-4 py-3">
          <div className="flex items-center justify-between">
            <GlassBadge color="violet" dot={false}>{m.key}</GlassBadge>
            <span className="text-xs text-ink-faint">{dateTime(m.created_at)}</span>
          </div>
          <p className="mt-2 text-sm text-ink">{m.value}</p>
        </li>
      ))}
    </ul>
  );
}

// ---------- Negotiation ----------

const NEG_FIELDS = ["pricing", "discounts", "freebies", "payment_terms", "escalation_rules"];

function NegotiationTab({ client, api }) {
  const [config, setConfig] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get(`/clients/${client.id}/negotiation`).then(setConfig);
  }, [client.id]);

  async function save() {
    setBusy(true);
    try {
      const next = await api.put(`/clients/${client.id}/negotiation`, config);
      setConfig(next);
    } finally {
      setBusy(false);
    }
  }

  if (!config) return <Loading />;

  return (
    <div className="space-y-4">
      {NEG_FIELDS.map((field) => (
        <div key={field} className="rounded-xl border border-glass-line bg-white/[0.03] p-4">
          <p className="eyebrow mb-2">{field.replace("_", " ")}</p>
          <textarea
            className="glass-input font-mono text-xs"
            rows={2}
            placeholder="JSON array — e.g. [{&quot;label&quot;:&quot;Basic&quot;,&quot;amount&quot;:1000}]"
            value={config[field] ? JSON.stringify(config[field]) : ""}
            onChange={(e) => {
              const raw = e.target.value.trim();
              let value = null;
              try {
                value = raw ? JSON.parse(raw) : null;
              } catch {
                value = null;
              }
              setConfig({ ...config, [field]: value });
            }}
          />
        </div>
      ))}
      <GlassButton onClick={save} disabled={busy}>{busy ? "Saving…" : "Save negotiation config"}</GlassButton>
    </div>
  );
}

// ---------- Follow-ups ----------

function FollowupsTab({ client, api }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    api.get(`/clients/${client.id}/follow-ups`).then(setItems).catch(() => setItems([]));
  }, [client.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function send(id) {
    setError(null);
    try {
      await api.post(`/clients/${client.id}/follow-ups/${id}/send`);
      load();
    } catch (ex) {
      setError(ex.message);
    }
  }

  if (!items) return <Loading />;

  if (!items.length)
    return <EmptyState title="No follow-ups" hint="After a call, Ava drafts thank-you emails and follow-ups here." />;

  return (
    <div className="space-y-3">
      {error && <p className="text-sm text-red-300">{error}</p>}
      {items.map((f) => (
        <div key={f.id} className="rounded-xl border border-glass-line bg-white/[0.03] p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GlassBadge color="violet" dot={false}>{f.kind}</GlassBadge>
              <GlassBadge color="gray" dot={false}>{f.channel}</GlassBadge>
            </div>
            <GlassBadge color={f.status === "sent" ? "green" : f.status === "failed" ? "red" : "amber"}>
              {f.status}
            </GlassBadge>
          </div>
          <p className="mt-2 whitespace-pre-wrap text-sm text-ink-dim">{f.content}</p>
          {f.status !== "sent" && (
            <div className="mt-3 flex justify-end">
              <GlassButton variant="ghost" onClick={() => send(f.id)} disabled={f.status === "pending" ? false : true}>
                Send
              </GlassButton>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------- Main ----------

export default function ClientDetail() {
  const { id } = useParams();
  const api = useApi();
  const [client, setClient] = useState(null);
  const [tab, setTab] = useState("overview");
  const [bi, setBi] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.get(`/clients/${id}`).then(setClient).catch(setError);
  }, [id]);

  useEffect(() => {
    if (tab === "overview" && !bi) {
      api.get(`/clients/${id}/bi`).then(setBi).catch(() => setBi(null));
    }
  }, [tab, bi]);

  if (error)
    return <EmptyState title="Client not found" hint={error.message} action={<Link to="/clients" className="glass-btn-ghost">Back to clients</Link>} />;
  if (!client) return <Loading />;

  const TABS = [
    ["overview", "Overview"],
    ["research", "Research"],
    ["calls", "Calls"],
    ["memory", "Memory"],
    ["negotiation", "Negotiation"],
    ["followups", "Follow-ups"],
  ];

  return (
    <div className="animate-fade-up space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link to="/clients" className="text-xs text-ink-faint hover:text-ink-dim">← Clients</Link>
          <h1 className="mt-1 flex items-center gap-3 page-title">
            {client.name}
            {client.company && <span className="text-lg font-normal text-ink-dim">· {client.company}</span>}
          </h1>
          <p className="mt-1 text-sm text-ink-dim">
            {client.industry ?? "Unknown industry"} · {usd(client.budget)}
          </p>
        </div>
        <GlassBadge color={STATUS_COLOR[client.status] ?? "gray"}>{client.status}</GlassBadge>
      </header>

      <div className="flex flex-wrap gap-1 rounded-xl border border-glass-line bg-black/20 p-1 backdrop-blur-xl">
        {TABS.map(([key, label]) => (
          <Tab key={key} active={tab === key} onClick={() => setTab(key)}>
            {label}
          </Tab>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid gap-6 lg:grid-cols-2">
          <GlassCard className="p-5">
            <h2 className="mb-4 font-display text-base font-semibold text-white">Contact</h2>
            <dl className="space-y-2.5 text-sm">
              {[["Email", client.email], ["Phone", client.phone], ["Website", client.website], ["Added", dateTime(client.created_at)]].map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <dt className="text-ink-dim">{k}</dt>
                  <dd className="text-right text-ink">{v ?? "—"}</dd>
                </div>
              ))}
            </dl>
            {client.notes && (
              <div className="mt-4 rounded-xl border border-glass-line bg-white/[0.03] p-3 text-sm text-ink-dim">
                {client.notes}
              </div>
            )}
          </GlassCard>

          {bi ? (
            <GlassCard className="p-5">
              <h2 className="mb-4 font-display text-base font-semibold text-white">Business intelligence</h2>
              <BiPanel bi={bi} />
            </GlassCard>
          ) : (
            <GlassCard className="p-5">
              <EmptyState title="No BI report" hint="Run research on their website to generate a SWOT, budget estimate, and opportunity score." />
            </GlassCard>
          )}
        </div>
      )}

      {tab === "research" && (
        <GlassCard className="p-5"><ResearchTab client={client} api={api} /></GlassCard>
      )}
      {tab === "calls" && <CallsTab client={client} api={api} />}
      {tab === "memory" && (
        <GlassCard className="p-5"><MemoryTab client={client} api={api} /></GlassCard>
      )}
      {tab === "negotiation" && (
        <GlassCard className="p-5"><NegotiationTab client={client} api={api} /></GlassCard>
      )}
      {tab === "followups" && <FollowupsTab client={client} api={api} />}
    </div>
  );
}
