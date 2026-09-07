import { useState, useEffect } from "react";
import { api } from "../api/client";

const s = {
  page: { padding: 24, background: "#09090b", minHeight: "100vh", color: "#e4e4e7" },
  card: { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: 20, marginBottom: 16 },
  h1: { fontSize: 22, fontWeight: 700, margin: "0 0 4px", color: "#fff" },
  sub: { color: "#71717a", fontSize: 13, margin: "0 0 24px" },
  h2: { fontSize: 15, fontWeight: 600, margin: "0 0 14px", color: "#a1a1aa" },
  input: { width: "100%", background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 12px", color: "#e4e4e7", fontSize: 13, boxSizing: "border-box" },
  select: { background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 12px", color: "#e4e4e7", fontSize: 13 },
  btn: { padding: "8px 16px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnSm: { padding: "5px 10px", borderRadius: 6, border: "none", fontSize: 12, fontWeight: 600, cursor: "pointer" },
  tag: (c) => ({ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 600, background: c === "ok" ? "rgba(34,197,94,.15)" : c === "error" ? "rgba(239,68,68,.15)" : "rgba(99,102,241,.15)", color: c === "ok" ? "#4ade80" : c === "error" ? "#f87171" : "#818cf8" }),
  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 },
};

export default function ActionLayer() {
  const [actions, setActions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [form, setForm] = useState({ name: "", type: "webhook", trigger: "alert", url: "", active: true });
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState("actions");

  const load = async () => {
    const [a, l] = await Promise.all([
      api.get("/actions").then(r => r.data).catch(() => []),
      api.get("/actions/logs").then(r => r.data).catch(() => []),
    ]);
    setActions(a);
    setLogs(l);
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!form.name) return;
    setLoading(true);
    await api.post("/actions", form).catch(() => {});
    setForm({ name: "", type: "webhook", trigger: "alert", url: "", active: true });
    await load();
    setLoading(false);
  };

  const run = async (id) => {
    await api.post(`/actions/${id}/run`, {}).catch(() => {});
    await load();
  };

  const del = async (id) => {
    await api.delete(`/actions/${id}`).catch(() => {});
    await load();
  };

  const typeColor = { webhook: "#6366f1", slack: "#4ade80", email: "#f59e0b" };

  return (
    <div style={s.page}>
      <h1 style={s.h1}>⚡ Action Layer</h1>
      <p style={s.sub}>Automate responses — fire webhooks, Slack alerts, and emails when KPIs breach thresholds</p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["actions", "logs", "guide"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...s.btnSm, background: tab === t ? "rgba(99,102,241,.2)" : "rgba(255,255,255,.05)", color: tab === t ? "#818cf8" : "#71717a", border: `1px solid ${tab === t ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)"}` }}>
            {t === "actions" ? "🎯 Actions" : t === "logs" ? "📋 Logs" : "📖 Guide"}
          </button>
        ))}
      </div>

      {tab === "actions" && (
        <>
          <div style={s.card}>
            <h2 style={s.h2}>Create Action</h2>
            <div style={s.grid}>
              <div>
                <div style={{ fontSize: 12, color: "#71717a", marginBottom: 4 }}>Name</div>
                <input style={s.input} placeholder="e.g. Notify Slack on Revenue Drop" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#71717a", marginBottom: 4 }}>Type</div>
                <select style={{ ...s.select, width: "100%" }} value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                  <option value="webhook">🔗 Webhook (POST to URL)</option>
                  <option value="slack">💬 Slack Notification</option>
                  <option value="email">📧 Email Alert</option>
                </select>
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#71717a", marginBottom: 4 }}>Trigger</div>
                <select style={{ ...s.select, width: "100%" }} value={form.trigger} onChange={e => setForm(f => ({ ...f, trigger: e.target.value }))}>
                  <option value="alert">On Alert Fire</option>
                  <option value="manual">Manual Only</option>
                </select>
              </div>
              <div>
                <div style={{ fontSize: 12, color: "#71717a", marginBottom: 4 }}>URL (webhook / Slack webhook)</div>
                <input style={s.input} placeholder="https://hooks.slack.com/..." value={form.url} onChange={e => setForm(f => ({ ...f, url: e.target.value }))} />
              </div>
            </div>
            <button style={{ ...s.btn, marginTop: 14 }} onClick={create} disabled={loading}>
              {loading ? "Creating…" : "+ Create Action"}
            </button>
          </div>

          {actions.length === 0 ? (
            <div style={{ ...s.card, textAlign: "center", color: "#52525b", padding: 40 }}>
              No actions yet. Create one above to automate responses to alerts.
            </div>
          ) : actions.map(a => (
            <div key={a.id} style={{ ...s.card, display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: "#fff", marginBottom: 4 }}>{a.name}</div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <span style={s.tag("info")}>{a.type}</span>
                  <span style={{ ...s.tag("info"), background: "rgba(251,191,36,.1)", color: "#fbbf24" }}>{a.trigger}</span>
                  {a.url && <span style={{ fontSize: 11, color: "#52525b", fontFamily: "monospace" }}>{a.url.slice(0, 40)}…</span>}
                </div>
              </div>
              <button style={{ ...s.btnSm, background: "rgba(34,197,94,.15)", color: "#4ade80" }} onClick={() => run(a.id)}>▶ Run</button>
              <button style={{ ...s.btnSm, background: "rgba(239,68,68,.1)", color: "#f87171" }} onClick={() => del(a.id)}>✕</button>
            </div>
          ))}
        </>
      )}

      {tab === "logs" && (
        <div style={s.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <h2 style={{ ...s.h2, margin: 0 }}>Execution Logs</h2>
            <button style={{ ...s.btnSm, background: "rgba(239,68,68,.1)", color: "#f87171" }} onClick={() => api.delete("/actions/logs").then(load)}>Clear</button>
          </div>
          {logs.length === 0 ? <div style={{ color: "#52525b", textAlign: "center", padding: 30 }}>No logs yet</div> : logs.map((l, i) => (
            <div key={i} style={{ borderBottom: "1px solid rgba(255,255,255,.05)", padding: "10px 0", display: "flex", gap: 12, alignItems: "flex-start" }}>
              <span style={s.tag(l.success ? "ok" : "error")}>{l.success ? "✓ ok" : "✗ fail"}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 13, color: "#e4e4e7" }}>{l.name}</div>
                <div style={{ fontSize: 11, color: "#52525b", marginTop: 2 }}>{l.ts}</div>
                {l.result && <div style={{ fontSize: 11, color: "#71717a", marginTop: 4, fontFamily: "monospace" }}>{JSON.stringify(l.result).slice(0, 120)}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "guide" && (
        <div style={s.card}>
          <h2 style={s.h2}>How to set up automated actions</h2>
          {[
            { icon: "1️⃣", title: "Create an Alert Rule", desc: "Go to Alerts → create a KPI threshold rule (e.g. revenue < 1000)" },
            { icon: "2️⃣", title: "Create an Action", desc: "Add a webhook, Slack, or email action with trigger = 'On Alert Fire'" },
            { icon: "3️⃣", title: "It fires automatically", desc: "When the alert triggers, COGNIDATA instantly POSTs to your URL or sends a Slack message" },
            { icon: "💬", title: "Slack Setup", desc: "Go to api.slack.com/apps → Create App → Incoming Webhooks → copy the URL" },
            { icon: "🔗", title: "Webhook Payload", desc: 'COGNIDATA sends: { source, action, metric, value, threshold, message, timestamp }' },
          ].map((item, i) => (
            <div key={i} style={{ display: "flex", gap: 14, marginBottom: 16 }}>
              <span style={{ fontSize: 20 }}>{item.icon}</span>
              <div>
                <div style={{ fontWeight: 600, color: "#e4e4e7", marginBottom: 2 }}>{item.title}</div>
                <div style={{ color: "#71717a", fontSize: 13 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
