import { useState, useEffect } from "react";
import { api } from "../api/client";

const s = {
  page: { padding: 24, background: "#09090b", minHeight: "100vh", color: "#e4e4e7" },
  card: { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: 20, marginBottom: 16 },
  h1: { fontSize: 22, fontWeight: 700, margin: "0 0 4px", color: "#fff" },
  sub: { color: "#71717a", fontSize: 13, margin: "0 0 24px" },
  h2: { fontSize: 15, fontWeight: 600, margin: "0 0 14px", color: "#a1a1aa" },
  code: { background: "#09090b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 8, padding: 14, fontFamily: "monospace", fontSize: 12, color: "#a1a1aa", whiteSpace: "pre-wrap", overflowX: "auto" },
  btn: { padding: "8px 16px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnSm: { padding: "5px 10px", borderRadius: 6, border: "none", fontSize: 12, fontWeight: 600, cursor: "pointer" },
  method: (m) => ({ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700, background: m === "GET" ? "rgba(34,197,94,.15)" : m === "POST" ? "rgba(99,102,241,.15)" : m === "DELETE" ? "rgba(239,68,68,.15)" : "rgba(251,191,36,.15)", color: m === "GET" ? "#4ade80" : m === "POST" ? "#818cf8" : m === "DELETE" ? "#f87171" : "#fbbf24" }),
};

export default function DeveloperHub() {
  const [ref, setRef] = useState(null);
  const [qs, setQs] = useState(null);
  const [tab, setTab] = useState("quickstart");
  const [lang, setLang] = useState("python");

  useEffect(() => {
    api.get("/sdk/reference").then(r => setRef(r.data)).catch(() => {});
    api.get("/sdk/quickstart").then(r => setQs(r.data)).catch(() => {});
  }, []);

  const copy = (text) => { navigator.clipboard.writeText(text); };

  return (
    <div style={s.page}>
      <h1 style={s.h1}>💻 Developer Hub</h1>
      <p style={s.sub}>Option D — Full API reference, SDK examples, webhook guide, and rate limits</p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {["quickstart", "reference", "sdk", "webhooks", "ratelimits"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{ ...s.btnSm, background: tab === t ? "rgba(99,102,241,.2)" : "rgba(255,255,255,.05)", color: tab === t ? "#818cf8" : "#71717a", border: `1px solid ${tab === t ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)"}` }}>
            {t === "quickstart" ? "🚀 Quickstart" : t === "reference" ? "📖 API Reference" : t === "sdk" ? "🛠 SDK" : t === "webhooks" ? "🔗 Webhooks" : "⚡ Rate Limits"}
          </button>
        ))}
      </div>

      {tab === "quickstart" && qs && (
        <div>
          {qs.steps?.map((step, i) => (
            <div key={i} style={s.card}>
              <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: "rgba(99,102,241,.2)", color: "#818cf8", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13, flexShrink: 0 }}>{step.step}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: "#fff", marginBottom: 6 }}>{step.title}</div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: step.body ? 8 : 0 }}>
                    <span style={s.method(step.method)}>{step.method}</span>
                    <code style={{ fontSize: 12, color: "#818cf8", fontFamily: "monospace" }}>{step.path}</code>
                  </div>
                  {step.body && <div style={s.code}>{JSON.stringify(step.body, null, 2)}</div>}
                  {step.note && <div style={{ fontSize: 12, color: "#52525b", marginTop: 6 }}>ℹ {step.note}</div>}
                  {step.returns && <div style={{ fontSize: 12, color: "#4ade80", marginTop: 6 }}>Returns: {step.returns}</div>}
                  {step.then && <div style={{ fontSize: 12, color: "#fbbf24", marginTop: 6 }}>Then: {step.then}</div>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "reference" && ref && (
        <div>
          {Object.entries(ref.endpoints || {}).map(([group, endpoints]) => (
            <div key={group} style={s.card}>
              <h2 style={s.h2}>{group.charAt(0).toUpperCase() + group.slice(1)}</h2>
              {endpoints.map((ep, i) => (
                <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,.04)" }}>
                  <span style={s.method(ep.method)}>{ep.method}</span>
                  <code style={{ fontSize: 12, color: "#818cf8", fontFamily: "monospace", flex: 1 }}>/api{ep.path}</code>
                  {ep.note && <span style={{ fontSize: 11, color: "#52525b" }}>{ep.note}</span>}
                  {ep.params && <span style={{ fontSize: 11, color: "#52525b" }}>?{ep.params}</span>}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {tab === "sdk" && ref && (
        <div>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            {["python", "javascript", "curl"].map(l => (
              <button key={l} onClick={() => setLang(l)} style={{ ...s.btnSm, background: lang === l ? "rgba(99,102,241,.2)" : "rgba(255,255,255,.05)", color: lang === l ? "#818cf8" : "#71717a", border: `1px solid ${lang === l ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)"}` }}>
                {l}
              </button>
            ))}
          </div>
          <div style={s.card}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
              <h2 style={{ ...s.h2, margin: 0 }}>
                {lang === "python" ? "Python SDK" : lang === "javascript" ? "JavaScript SDK" : "curl Examples"}
              </h2>
              <button style={{ ...s.btnSm, background: "rgba(255,255,255,.05)", color: "#71717a" }} onClick={() => copy(lang === "python" ? ref.python_sdk : lang === "javascript" ? ref.javascript_sdk : Object.values(ref.curl_examples || {}).join("\n\n"))}>
                Copy
              </button>
            </div>
            {lang === "python" && <div style={s.code}>{ref.python_sdk}</div>}
            {lang === "javascript" && <div style={s.code}>{ref.javascript_sdk}</div>}
            {lang === "curl" && Object.entries(ref.curl_examples || {}).map(([k, v]) => (
              <div key={k} style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 12, color: "#71717a", marginBottom: 6 }}>{k}</div>
                <div style={s.code}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "webhooks" && (
        <div style={s.card}>
          <h2 style={s.h2}>Webhook Integration Guide</h2>
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontWeight: 600, color: "#fff", marginBottom: 8 }}>Setup in 3 steps</div>
            {["Create an alert rule (Alerts page)", "Create a webhook action (Action Layer page) with your URL", "When the alert fires, COGNIDATA POSTs the payload to your URL automatically"].map((step, i) => (
              <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8 }}>
                <span style={{ color: "#6366f1", fontWeight: 700 }}>{i + 1}.</span>
                <span style={{ color: "#a1a1aa", fontSize: 13 }}>{step}</span>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 13, color: "#71717a", marginBottom: 8 }}>Payload sent to your URL:</div>
          <div style={s.code}>{JSON.stringify({ source: "cognidata", action: "My Webhook", timestamp: "2026-04-02T10:00:00Z", metric: "revenue", value: 850, threshold: 1000, condition: "lt", message: "Revenue dropped below threshold", level: "critical" }, null, 2)}</div>
          <div style={{ marginTop: 16, fontSize: 13, color: "#71717a", marginBottom: 8 }}>Custom payload template (use placeholders):</div>
          <div style={s.code}>{`{"text": "Alert: {metric} is {value} (threshold: {threshold})", "channel": "#alerts"}`}</div>
        </div>
      )}

      {tab === "ratelimits" && ref && (
        <div style={s.card}>
          <h2 style={s.h2}>Rate Limits</h2>
          {Object.entries(ref.rate_limits || {}).map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid rgba(255,255,255,.05)" }}>
              <span style={{ color: "#a1a1aa", fontSize: 13 }}>{k.replace(/_/g, " ")}</span>
              <span style={{ color: "#818cf8", fontFamily: "monospace", fontSize: 13 }}>{v}</span>
            </div>
          ))}
          <div style={{ marginTop: 16, padding: 14, background: "rgba(251,191,36,.05)", borderRadius: 8, border: "1px solid rgba(251,191,36,.15)" }}>
            <div style={{ fontSize: 12, color: "#fbbf24", marginBottom: 4 }}>Auth</div>
            <div style={{ fontSize: 13, color: "#a1a1aa" }}>All endpoints require <code style={{ color: "#818cf8" }}>Authorization: Bearer TOKEN</code> header. Get a token via <code style={{ color: "#818cf8" }}>POST /api/auth/login</code>. Alternatively use an API key from your Profile page.</div>
          </div>
        </div>
      )}
    </div>
  );
}
