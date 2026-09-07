import { useState } from "react";
import { api } from "../api/client";

const s = {
  page: { padding: 24, background: "#09090b", minHeight: "100vh", color: "#e4e4e7" },
  card: { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: 20, marginBottom: 16 },
  h1: { fontSize: 22, fontWeight: 700, margin: "0 0 4px", color: "#fff" },
  sub: { color: "#71717a", fontSize: 13, margin: "0 0 24px" },
  h2: { fontSize: 15, fontWeight: 600, margin: "0 0 14px", color: "#a1a1aa" },
  input: { width: "100%", background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "10px 14px", color: "#e4e4e7", fontSize: 14, boxSizing: "border-box" },
  btn: { padding: "10px 20px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 14, fontWeight: 600, cursor: "pointer" },
  btnSm: { padding: "6px 12px", borderRadius: 6, border: "none", fontSize: 12, fontWeight: 600, cursor: "pointer" },
  tag: (c) => ({ padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700, background: c === "high" ? "rgba(239,68,68,.15)" : c === "medium" ? "rgba(251,191,36,.15)" : "rgba(34,197,94,.15)", color: c === "high" ? "#f87171" : c === "medium" ? "#fbbf24" : "#4ade80" }),
  conf: (v) => ({ display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700, background: v >= 80 ? "rgba(34,197,94,.15)" : v >= 60 ? "rgba(251,191,36,.15)" : "rgba(239,68,68,.15)", color: v >= 80 ? "#4ade80" : v >= 60 ? "#fbbf24" : "#f87171" }),
};

export default function DeepAnalyst() {
  const [tab, setTab] = useState("reason");
  const [question, setQuestion] = useState("");
  const [goal, setGoal] = useState("");
  const [constraints, setConstraints] = useState("");
  const [focus, setFocus] = useState("general");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true); setError(""); setResult(null);
    try {
      let r;
      if (tab === "reason") r = await api.post("/analyst/reason", { question, depth: 3, auto_suggest: true });
      else if (tab === "insights") r = await api.post("/analyst/auto-insights", { focus, max_insights: 5 });
      else if (tab === "decide") r = await api.post("/analyst/decide", { goal, constraints });
      else r = await api.post("/analyst/narrate");
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Failed — make sure a dataset is loaded and API key is set");
    }
    setLoading(false);
  };

  const tabs = [
    { id: "reason", label: "🧠 Deep Reason", desc: "Multi-step reasoning chain with confidence scores" },
    { id: "insights", label: "💡 Auto Insights", desc: "AI scans your data and surfaces key findings autonomously" },
    { id: "decide", label: "🎯 Decision Engine", desc: "Give a goal, get ranked action recommendations" },
    { id: "narrate", label: "📝 Narrate", desc: "Generate a full executive narrative from your data" },
  ];

  return (
    <div style={s.page}>
      <h1 style={s.h1}>🧠 Deep AI Analyst</h1>
      <p style={s.sub}>Option A — Most powerful AI analyst. Multi-turn reasoning, autonomous insights, decision recommendations.</p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setResult(null); }} style={{ ...s.btnSm, background: tab === t.id ? "rgba(99,102,241,.2)" : "rgba(255,255,255,.05)", color: tab === t.id ? "#818cf8" : "#71717a", border: `1px solid ${tab === t.id ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)"}` }}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={s.card}>
        <div style={{ fontSize: 12, color: "#52525b", marginBottom: 14 }}>{tabs.find(t => t.id === tab)?.desc}</div>

        {tab === "reason" && (
          <input style={{ ...s.input, marginBottom: 12 }} placeholder="Ask anything about your data… e.g. 'What is driving the revenue decline in Q3?'" value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => e.key === "Enter" && run()} />
        )}
        {tab === "insights" && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 12, color: "#71717a", marginBottom: 6 }}>Focus area</div>
            <select style={{ background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 12px", color: "#e4e4e7", fontSize: 13 }} value={focus} onChange={e => setFocus(e.target.value)}>
              <option value="general">General insights</option>
              <option value="anomaly">Anomalies & outliers</option>
              <option value="trend">Trends & growth</option>
              <option value="comparison">Group comparisons</option>
              <option value="decision">Actionable decisions</option>
            </select>
          </div>
        )}
        {tab === "decide" && (
          <>
            <input style={{ ...s.input, marginBottom: 10 }} placeholder="Business goal — e.g. 'Increase monthly revenue by 20%'" value={goal} onChange={e => setGoal(e.target.value)} />
            <input style={{ ...s.input, marginBottom: 12 }} placeholder="Constraints (optional) — e.g. 'Budget under $50k, no new hires'" value={constraints} onChange={e => setConstraints(e.target.value)} />
          </>
        )}
        {tab === "narrate" && (
          <div style={{ color: "#71717a", fontSize: 13, marginBottom: 12 }}>Generates a full executive narrative from your loaded dataset. No input needed.</div>
        )}

        <button style={s.btn} onClick={run} disabled={loading}>
          {loading ? "Analyzing…" : tab === "reason" ? "🧠 Reason" : tab === "insights" ? "💡 Generate Insights" : tab === "decide" ? "🎯 Get Recommendations" : "📝 Generate Narrative"}
        </button>
        {error && <div style={{ color: "#f87171", fontSize: 13, marginTop: 10 }}>{error}</div>}
      </div>

      {result && (
        <>
          {/* Deep Reason result */}
          {result.reasoning_chain && (
            <>
              <div style={s.card}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                  <h2 style={{ ...s.h2, margin: 0 }}>Answer</h2>
                  <span style={s.conf(result.confidence)}>Confidence: {result.confidence}%</span>
                </div>
                <div style={{ color: "#e4e4e7", lineHeight: 1.7, fontSize: 14 }}>{result.answer}</div>
                {result.caveats?.length > 0 && (
                  <div style={{ marginTop: 12, padding: 12, background: "rgba(251,191,36,.05)", borderRadius: 8, border: "1px solid rgba(251,191,36,.15)" }}>
                    <div style={{ fontSize: 12, color: "#fbbf24", marginBottom: 6 }}>⚠ Caveats</div>
                    {result.caveats.map((c, i) => <div key={i} style={{ fontSize: 13, color: "#a1a1aa" }}>• {c}</div>)}
                  </div>
                )}
              </div>
              <div style={s.card}>
                <h2 style={s.h2}>Reasoning Chain ({result.steps} steps)</h2>
                {result.reasoning_chain.map((step, i) => (
                  <div key={i} style={{ marginBottom: 14, paddingLeft: 14, borderLeft: "2px solid rgba(99,102,241,.3)" }}>
                    <div style={{ fontSize: 12, color: "#6366f1", marginBottom: 4 }}>Step {i + 1}: {step.question}</div>
                    <div style={{ fontSize: 13, color: "#a1a1aa", lineHeight: 1.6 }}>{step.answer}</div>
                  </div>
                ))}
              </div>
              {result.suggested_questions?.length > 0 && (
                <div style={s.card}>
                  <h2 style={s.h2}>Suggested Follow-up Questions</h2>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {result.suggested_questions.map((q, i) => (
                      <button key={i} onClick={() => { setQuestion(q); setResult(null); }} style={{ textAlign: "left", background: "rgba(99,102,241,.08)", border: "1px solid rgba(99,102,241,.2)", borderRadius: 8, padding: "10px 14px", color: "#818cf8", fontSize: 13, cursor: "pointer" }}>
                        → {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Auto Insights result */}
          {result.insights && (
            <div>
              {result.insights.map((ins, i) => (
                <div key={i} style={s.card}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                    <div style={{ fontWeight: 700, fontSize: 15, color: "#fff" }}>{ins.title}</div>
                    <div style={{ display: "flex", gap: 6 }}>
                      <span style={s.tag(ins.importance)}>{ins.importance}</span>
                      <span style={s.conf(ins.confidence)}>{ins.confidence}%</span>
                    </div>
                  </div>
                  <div style={{ color: "#a1a1aa", fontSize: 13, lineHeight: 1.6, marginBottom: 10 }}>{ins.insight}</div>
                  <div style={{ padding: "8px 12px", background: "rgba(34,197,94,.05)", borderRadius: 8, border: "1px solid rgba(34,197,94,.15)", fontSize: 13, color: "#4ade80" }}>
                    ✓ Action: {ins.action}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Decision Engine result */}
          {result.recommendations && (
            <>
              <div style={s.card}>
                <h2 style={s.h2}>Goal: {result.goal}</h2>
                {result.recommendations.map((rec, i) => (
                  <div key={i} style={{ marginBottom: 14, padding: 14, background: "rgba(255,255,255,.02)", borderRadius: 8, border: "1px solid rgba(255,255,255,.06)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                      <span style={{ fontWeight: 700, color: "#fff" }}>#{rec.rank} {rec.action}</span>
                      <div style={{ display: "flex", gap: 6 }}>
                        <span style={s.tag(rec.effort === "high" ? "high" : rec.effort === "medium" ? "medium" : "low")}>effort: {rec.effort}</span>
                        <span style={s.conf(rec.confidence)}>{rec.confidence}%</span>
                      </div>
                    </div>
                    <div style={{ fontSize: 13, color: "#a1a1aa", marginBottom: 6 }}>{rec.rationale}</div>
                    <div style={{ fontSize: 12, color: "#4ade80" }}>Expected: {rec.expected_impact}</div>
                  </div>
                ))}
              </div>
              {result.kpis_to_track?.length > 0 && (
                <div style={s.card}>
                  <h2 style={s.h2}>KPIs to Track</h2>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {result.kpis_to_track.map((k, i) => <span key={i} style={{ background: "rgba(99,102,241,.1)", color: "#818cf8", padding: "4px 10px", borderRadius: 6, fontSize: 12 }}>{k}</span>)}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Narrative result */}
          {result.narrative && (
            <div style={s.card}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
                <h2 style={{ ...s.h2, margin: 0 }}>Executive Narrative</h2>
                <span style={{ fontSize: 12, color: "#52525b" }}>{result.word_count} words</span>
              </div>
              <div style={{ color: "#a1a1aa", fontSize: 14, lineHeight: 1.8, whiteSpace: "pre-wrap" }}>{result.narrative}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
