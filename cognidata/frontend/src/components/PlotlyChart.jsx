import { useState } from "react";
import Plot from "react-plotly.js";
import { api } from "../api/client";

export default function PlotlyChart({ figure, style, showExplain = true }) {
  const [explanation, setExplanation] = useState(null);
  const [explaining, setExplaining]   = useState(false);

  if (!figure) return null;

  const explain = async () => {
    setExplaining(true);
    try {
      const apiKey = localStorage.getItem("openai_key") || localStorage.getItem("aiml_key") || "";
      const chartTitle = figure.layout?.title?.text || figure.layout?.title || "this chart";
      const chartType  = figure.data?.[0]?.type || "chart";
      const { data } = await api.post("/ai/chat", {
        query: `In 2 sentences, explain what "${chartTitle}" (${chartType}) shows, flag anything unusual, and suggest one next question.`
      }, apiKey ? { headers: { "X-API-Key": apiKey } } : {});
      setExplanation(data?.data || data?.answer || "No explanation available.");
    } catch(e) {
      const msg = e.response?.data?.detail || e.message || "";
      if (msg.toLowerCase().includes("api key") || e.response?.status === 401) {
        setExplanation("API key required — add your OpenAI key in Settings.");
      } else {
        setExplanation("Could not generate explanation. Try again.");
      }
    }
    setExplaining(false);
  };

  return (
    <div style={{ position: "relative" }}>
      <Plot
        data={figure.data}
        layout={{
          ...figure.layout,
          paper_bgcolor: "transparent",
          plot_bgcolor:  "transparent",
          font: { color: "#a1a1aa", family: "Inter,sans-serif" },
          margin: { l: 40, r: 20, t: 40, b: 40 },
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", ...style }}
        useResizeHandler
      />
      {showExplain && (
        <div style={{ position: "absolute", top: 6, right: 6, zIndex: 10 }}>
          <button
            onClick={explain}
            disabled={explaining}
            title="Explain this chart with AI"
            style={{
              padding: "3px 8px", borderRadius: 6, border: "1px solid rgba(99,102,241,.3)",
              background: "rgba(9,9,11,.8)", color: "#818cf8", fontSize: 10, cursor: "pointer",
              backdropFilter: "blur(4px)", display: "flex", alignItems: "center", gap: 4,
              opacity: explaining ? 0.6 : 1,
            }}>
            {explaining ? "…" : "✦ Explain"}
          </button>
        </div>
      )}
      {explanation && (
        <div style={{
          margin: "4px 0 0", padding: "10px 14px",
          background: "rgba(99,102,241,.06)", border: "1px solid rgba(99,102,241,.2)",
          borderRadius: "0 0 10px 10px", fontSize: 12, color: "#a1a1aa", lineHeight: 1.6,
        }}>
          <span style={{ color: "#818cf8", fontWeight: 600, marginRight: 6 }}>✦ AI:</span>
          {explanation}
          <button onClick={() => setExplanation(null)}
            style={{ marginLeft: 8, background: "transparent", border: "none", color: "#52525b", cursor: "pointer", fontSize: 11 }}>
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
