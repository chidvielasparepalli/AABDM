import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useApi } from "../api";
import { GlassCard, GlassButton, GlassInput, GlassBadge, EmptyState } from "../components/Glass";
import { Loading } from "../components/Spinner";
import { date, usd } from "../lib/format";

const STATUS_COLOR = {
  Lead: "amber",
  Proposal: "violet",
  Closed: "cyan",
};

function NewClientModal({ api, onClose, onCreated }) {
  const [form, setForm] = useState({ name: "", company: "", email: "", phone: "", website: "", industry: "", budget: "", notes: "" });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    try {
      const body = { ...form };
      if (body.budget) body.budget = Number(body.budget);
      else delete body.budget;
      for (const k of Object.keys(body)) if (!body[k]) delete body[k];
      const created = await api.post("/clients", body);
      onCreated(created);
      onClose();
    } catch (ex) {
      setErr(ex.message);
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <form
        onSubmit={submit}
        className="glass grain relative w-full max-w-lg p-6"
      >
        <h2 className="font-display text-lg font-semibold text-white">New client</h2>
        <p className="mt-0.5 text-sm text-ink-faint">Ava will research them, then call.</p>

        <div className="mt-5 grid grid-cols-2 gap-4">
          <GlassInput label="Name" required autoFocus value={form.name} onChange={set("name")} />
          <GlassInput label="Company" value={form.company} onChange={set("company")} />
          <GlassInput label="Email" type="email" value={form.email} onChange={set("email")} />
          <GlassInput label="Phone" value={form.phone} onChange={set("phone")} />
          <GlassInput label="Website" placeholder="acme.com" value={form.website} onChange={set("website")} />
          <GlassInput label="Industry" value={form.industry} onChange={set("industry")} />
          <GlassInput label="Budget (USD/mo)" type="number" value={form.budget} onChange={set("budget")} />
        </div>
        <GlassInput label="Notes" className="mt-4" value={form.notes} onChange={set("notes")} />

        {err && <p className="mt-3 text-sm text-red-300">{err}</p>}

        <div className="mt-6 flex justify-end gap-3">
          <GlassButton type="button" variant="ghost" onClick={onClose}>Cancel</GlassButton>
          <GlassButton type="submit" disabled={saving || !form.name.trim()}>
            {saving ? "Creating…" : "Create client"}
          </GlassButton>
        </div>
      </form>
    </div>
  );
}

export default function Clients() {
  const api = useApi();
  const [clients, setClients] = useState(null);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api.get("/clients").then(setClients).catch(setError);
  }, []);

  const filtered = (clients ?? []).filter(
    (c) =>
      !query ||
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      (c.company ?? "").toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="animate-fade-up space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Prospecting</p>
          <h1 className="page-title">Clients</h1>
          <p className="mt-1 text-sm text-ink-dim">{clients?.length ?? "…"} in the pipeline</p>
        </div>
        <GlassButton onClick={() => setShowModal(true)}>+ Add client</GlassButton>
      </header>

      <div className="max-w-sm">
        <GlassInput placeholder="Search name or company…" value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>

      {error && <EmptyState title="Couldn't load clients" hint={error.message} />}
      {!clients && !error && <Loading />}

      {clients && !clients.length && !query && (
        <GlassCard>
          <EmptyState
            title="No clients yet"
            hint="Add your first lead and Ava will research, call, and qualify them."
            action={<GlassButton onClick={() => setShowModal(true)}>+ Add client</GlassButton>}
          />
        </GlassCard>
      )}

      {filtered.length > 0 && (
        <GlassCard className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-glass-line text-[11px] uppercase tracking-[0.12em] text-ink-faint">
                  <th className="px-5 py-3 font-medium">Client</th>
                  <th className="hidden px-5 py-3 font-medium md:table-cell">Industry</th>
                  <th className="hidden px-5 py-3 font-medium sm:table-cell">Status</th>
                  <th className="hidden px-5 py-3 text-right font-medium sm:table-cell">Budget</th>
                  <th className="px-5 py-3 text-right font-medium">Added</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr
                    key={c.id}
                    className="group border-b border-glass-line/60 transition-colors last:border-0 hover:bg-white/[0.03]"
                  >
                    <td className="px-5 py-3.5">
                      <Link to={`/clients/${c.id}`} className="block">
                        <span className="font-medium text-white group-hover:text-aurora-violet">
                          {c.name}
                        </span>
                        {c.company && (
                          <span className="block text-xs text-ink-faint">{c.company}</span>
                        )}
                      </Link>
                    </td>
                    <td className="hidden px-5 py-3.5 text-ink-dim md:table-cell">{c.industry ?? "—"}</td>
                    <td className="hidden px-5 py-3.5 sm:table-cell">
                      <GlassBadge color={STATUS_COLOR[c.status] ?? "gray"}>{c.status}</GlassBadge>
                    </td>
                    <td className="hidden px-5 py-3.5 text-right text-ink-dim sm:table-cell">
                      {usd(c.budget)}
                    </td>
                    <td className="px-5 py-3.5 text-right text-ink-faint">{date(c.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      {query && !filtered.length && (
        <GlassCard>
          <EmptyState title="No matches" hint={`Nothing for “${query}”`} />
        </GlassCard>
      )}

      {showModal && (
        <NewClientModal
          api={api}
          onClose={() => setShowModal(false)}
          onCreated={(c) => setClients((prev) => [c, ...(prev ?? [])])}
        />
      )}
    </div>
  );
}
