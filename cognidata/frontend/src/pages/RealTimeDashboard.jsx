import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "../api/client";
import PlotlyChart from "../components/PlotlyChart";
import useAuth from "../store/auth";

const S = {
  page:    { padding: 24, background: "#09090b", minHeight: "100vh", color: "#e4e4e7" },
  card:    { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: 16, marginBottom: 14 },
  h1:      { fontSize: 22, fontWeight: 700, margin: "0 0 2px", color: "#fff" },
  sub:     { color: "#71717a", fontSize: 13, margin: "0 0 20px" },
  label:   { fontSize: 11, color: "#71717a", display: "block", marginBottom: 4 },
  select:  { background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "7px 12px", color: "#e4e4e7", fontSize: 13, outline: "none" },
  btn:     { padding: "8px 16px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  btnSm:   { padding: "5px 10px", borderRadius: 6, border: "none", fontSize: 12, fontWeight: 600, cursor: "pointer" },
  kpi:     { flex: "1 1 130px", background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 10, padding: "12px 16px" },
  dot:     (on) => ({ width: 8, height: 8, borderRadius: "50%", background: on ? "#4ade80" : "#52525b", display: "inline-block", marginRight: 6, boxShadow: on ? "0 0 6px #4ade80" : "none" }),
};

const PALETTE = ["#6366f1","#10b981","#f59e0b","#ef4444","#0ea5e9","#a855f7","#ec4899","#14b8a6"];
const MAX_POINTS = 200;

// ── Sparkline (mini canvas chart) ────────────────────────────────────────────
function Sparkline({ data, color = "#6366f1", height = 40 }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !data.length) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    const min = Math.min(...data), max = Math.max(...data);
    const range = max - min || 1;
    const pts = data.map((v, i) => [i / (data.length - 1) * W, H - ((v - min) / range) * (H - 4) - 2]);
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    pts.slice(1).forEach(([x, y]) => ctx.lineTo(x, y));
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    // Fill
    ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
    ctx.fillStyle = color + "22";
    ctx.fill();
  }, [data, color]);
  return <canvas ref={ref} width={120} height={height} style={{ display: "block" }} />;
}

// ── KPI Card ─────────────────────────────────────────────────────────────────
function KpiCard({ label, value, unit, history, color, delta }) {
  const fmt = (v) => {
    if (v === null || v === undefined) return "—";
    if (typeof v === "number") return v > 1000 ? v.toLocaleString(undefined, { maximumFractionDigits: 1 }) : v.toFixed(2);
    return String(v);
  };
  return (
    <div style={S.kpi}>
      <div style={{ fontSize: 11, color: "#52525b", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color, marginBottom: 2 }}>
        {fmt(value)}<span style={{ fontSize: 11, color: "#52525b", marginLeft: 4 }}>{unit}</span>
      </div>
      {delta !== null && delta !== undefined && (
        <div style={{ fontSize: 11, color: delta >= 0 ? "#4ade80" : "#f87171", marginBottom: 4 }}>
          {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(2)}
        </div>
      )}
      {history?.length > 1 && <Sparkline data={history} color={color} />}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function RealTimeDashboard() {
  const { token } = useAuth();
  const [streams, setStreams]       = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [connected, setConnected]   = useState(false);
  const [paused, setPaused]         = useState(false);
  const [chartType, setChartType]   = useState("Line");
  const [windowSize, setWindowSize] = useState(100);
  const [numCols, setNumCols]       = useState([]);
  const [xCol, setXCol]             = useState("_ts");
  const [yCols, setYCols]           = useState([]);

  // Per-column rolling data: { colName: [values] }
  const seriesRef  = useRef({});
  const tsRef      = useRef([]);
  const totalRef   = useRef(0);
  const epsRef     = useRef({ count: 0, ts: Date.now() });
  const sseRef     = useRef(null);

  const [renderTick, setRenderTick] = useState(0);
  const renderRef  = useRef(null);

  // Load streams list
  useEffect(() => {
    api.get("/ingest/streams").then(r => {
      setStreams(r.data || []);
      if (r.data?.length) setSelectedId(r.data[0].stream_id);
    }).catch(() => {});
  }, []);

  // Load snapshot when stream selected
  const loadSnapshot = useCallback(async (sid) => {
    if (!sid) return;
    try {
      const { data } = await api.get(`/stream/live/${sid}/snapshot?n=${windowSize}&token=${encodeURIComponent(token || "")}`);
      const cols = data.numeric_cols || [];
      setNumCols(cols);
      setYCols(cols.slice(0, 3));
      seriesRef.current = {};
      tsRef.current = [];
      cols.forEach(c => { seriesRef.current[c] = []; });
      data.rows.forEach(row => {
        tsRef.current.push(row._ts || "");
        cols.forEach(c => {
          const v = parseFloat(row[c]);
          if (!isNaN(v)) seriesRef.current[c] = [...(seriesRef.current[c] || []), v];
        });
      });
      totalRef.current = data.total;
      setRenderTick(t => t + 1);
    } catch {}
  }, [windowSize]);

  useEffect(() => { if (selectedId) loadSnapshot(selectedId); }, [selectedId]);

  // SSE connection
  const connect = useCallback(() => {
    if (!selectedId || !token) return;
    if (sseRef.current) { sseRef.current.close(); }

    const url = `http://localhost:8000/api/stream/live/${selectedId}?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    sseRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => { setConnected(false); };

    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "row" && !paused) {
          const row = msg.data;
          tsRef.current = [...tsRef.current, row._ts || ""].slice(-MAX_POINTS);
          numCols.forEach(c => {
            const v = parseFloat(row[c]);
            if (!isNaN(v)) {
              seriesRef.current[c] = [...(seriesRef.current[c] || []), v].slice(-MAX_POINTS);
            }
          });
          totalRef.current = msg.total;
          // EPS calc
          epsRef.current.count++;
          setRenderTick(t => t + 1);
        }
      } catch {}
    };
  }, [selectedId, token, paused, numCols]);

  const disconnect = useCallback(() => {
    if (sseRef.current) { sseRef.current.close(); sseRef.current = null; }
    setConnected(false);
  }, []);

  useEffect(() => () => disconnect(), []);

  // Throttled render loop — update charts at 2fps max
  useEffect(() => {
    renderRef.current = setInterval(() => setRenderTick(t => t + 1), 500);
    return () => clearInterval(renderRef.current);
  }, []);

  // EPS calculation
  const eps = (() => {
    const now = Date.now();
    const dt = (now - epsRef.current.ts) / 1000 || 1;
    const rate = epsRef.current.count / dt;
    epsRef.current = { count: 0, ts: now };
    return rate.toFixed(1);
  });

  // Build Plotly figure for a column
  const buildFig = (col, idx) => {
    const vals = seriesRef.current[col] || [];
    const xs = tsRef.current.slice(-vals.length);
    const color = PALETTE[idx % PALETTE.length];
    if (!vals.length) return null;

    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    const std = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length) || 1;
    const anomalies = vals.map((v, i) => Math.abs((v - mean) / std) > 2.5 ? i : -1).filter(i => i >= 0);

    const traces = [];
    if (chartType === "Line" || chartType === "Area") {
      traces.push({
        type: "scatter", mode: "lines",
        x: xs, y: vals,
        line: { color, width: 2 },
        fill: chartType === "Area" ? "tozeroy" : "none",
        fillcolor: color + "22",
        name: col,
      });
    } else if (chartType === "Bar") {
      traces.push({ type: "bar", x: xs, y: vals, marker: { color }, name: col });
    } else if (chartType === "Scatter") {
      traces.push({ type: "scatter", mode: "markers", x: xs, y: vals, marker: { color, size: 4 }, name: col });
    }

    // Anomaly markers
    if (anomalies.length) {
      traces.push({
        type: "scatter", mode: "markers",
        x: anomalies.map(i => xs[i]),
        y: anomalies.map(i => vals[i]),
        marker: { color: "#ef4444", size: 8, symbol: "x" },
        name: "Anomaly", showlegend: false,
      });
    }

    // Moving average
    const ma = vals.map((_, i) => {
      const w = vals.slice(Math.max(0, i - 9), i + 1);
      return w.reduce((a, b) => a + b, 0) / w.length;
    });
    traces.push({
      type: "scatter", mode: "lines",
      x: xs, y: ma,
      line: { color: "#ffffff44", width: 1, dash: "dot" },
      name: "MA(10)", showlegend: false,
    });

    return {
      data: traces,
      layout: {
        title: { text: col, font: { size: 12, color: "#a1a1aa" } },
        height: 220,
        template: "plotly_dark",
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        margin: { l: 40, r: 10, t: 30, b: 30 },
        xaxis: { showticklabels: xs.length < 50, tickfont: { size: 9 } },
        yaxis: { tickfont: { size: 9 } },
        showlegend: false,
      },
    };
  };

  // KPI values
  const kpis = yCols.map((col, idx) => {
    const vals = seriesRef.current[col] || [];
    const last = vals[vals.length - 1] ?? null;
    const prev = vals[vals.length - 2] ?? null;
    const delta = last !== null && prev !== null ? last - prev : null;
    return { col, last, delta, history: vals.slice(-30), color: PALETTE[idx % PALETTE.length] };
  });

  const selectedStream = streams.find(s => s.stream_id === selectedId);

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <h1 style={S.h1}>📊 Real-Time Dashboard</h1>
          <p style={S.sub}>Live streaming data visualization — charts update as events arrive via SSE.</p>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span style={S.dot(connected)} />
          <span style={{ fontSize: 12, color: connected ? "#4ade80" : "#52525b", marginRight: 8 }}>
            {connected ? "Live" : "Disconnected"}
          </span>
          <button onClick={() => setPaused(p => !p)} style={{ ...S.btnSm, background: paused ? "rgba(251,191,36,.15)" : "rgba(255,255,255,.06)", color: paused ? "#fbbf24" : "#a1a1aa", border: "1px solid rgba(255,255,255,.1)" }}>
            {paused ? "▶ Resume" : "⏸ Pause"}
          </button>
        </div>
      </div>

      {/* Controls */}
      <div style={{ ...S.card, display: "flex", gap: 16, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div>
          <label style={S.label}>Stream</label>
          <select style={S.select} value={selectedId} onChange={e => { setSelectedId(e.target.value); disconnect(); }}>
            <option value="">— select stream —</option>
            {streams.map(s => <option key={s.stream_id} value={s.stream_id}>{s.name} ({s.row_count} rows)</option>)}
          </select>
        </div>
        <div>
          <label style={S.label}>Chart Type</label>
          <select style={S.select} value={chartType} onChange={e => setChartType(e.target.value)}>
            {["Line", "Area", "Bar", "Scatter"].map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label style={S.label}>Window: {windowSize} pts</label>
          <input type="range" min={20} max={500} value={windowSize} onChange={e => setWindowSize(Number(e.target.value))}
            style={{ accentColor: "#6366f1", width: 100, display: "block", marginTop: 6 }} />
        </div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label style={S.label}>Y Columns (select up to 4)</label>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {numCols.map((c, i) => (
              <button key={c} onClick={() => setYCols(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c].slice(0, 4))}
                style={{ ...S.btnSm, background: yCols.includes(c) ? `${PALETTE[i % PALETTE.length]}33` : "rgba(255,255,255,.05)", color: yCols.includes(c) ? PALETTE[i % PALETTE.length] : "#71717a", border: `1px solid ${yCols.includes(c) ? PALETTE[i % PALETTE.length] + "66" : "rgba(255,255,255,.08)"}` }}>
                {c}
              </button>
            ))}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={connected ? disconnect : connect} disabled={!selectedId}
            style={{ ...S.btn, background: connected ? "rgba(239,68,68,.15)" : "linear-gradient(135deg,#6366f1,#8b5cf6)", color: connected ? "#f87171" : "#fff", border: connected ? "1px solid rgba(239,68,68,.3)" : "none" }}>
            {connected ? "⏹ Disconnect" : "▶ Connect"}
          </button>
          <button onClick={() => loadSnapshot(selectedId)} disabled={!selectedId}
            style={{ ...S.btnSm, background: "rgba(255,255,255,.06)", color: "#a1a1aa", border: "1px solid rgba(255,255,255,.1)" }}>
            ↺ Reload
          </button>
        </div>
      </div>

      {/* No stream selected */}
      {!selectedId && (
        <div style={{ ...S.card, textAlign: "center", color: "#52525b", padding: 60 }}>
          No streams yet. Go to <strong style={{ color: "#818cf8" }}>Live Ingest</strong> to create a stream and push data.
        </div>
      )}

      {selectedId && (
        <>
          {/* KPI row */}
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 14 }}>
            <div style={S.kpi}>
              <div style={{ fontSize: 11, color: "#52525b", marginBottom: 4 }}>Total Events</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#6366f1" }}>{totalRef.current.toLocaleString()}</div>
            </div>
            <div style={S.kpi}>
              <div style={{ fontSize: 11, color: "#52525b", marginBottom: 4 }}>Stream</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "#e4e4e7" }}>{selectedStream?.name || "—"}</div>
            </div>
            <div style={S.kpi}>
              <div style={{ fontSize: 11, color: "#52525b", marginBottom: 4 }}>Fields</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: "#10b981" }}>{numCols.length}</div>
            </div>
            {kpis.map(({ col, last, delta, history, color }) => (
              <KpiCard key={col} label={col} value={last} delta={delta} history={history} color={color} />
            ))}
          </div>

          {/* Charts grid */}
          {yCols.length === 0 && (
            <div style={{ ...S.card, textAlign: "center", color: "#52525b", padding: 40 }}>
              No numeric columns detected. Push some numeric data to the stream first.
            </div>
          )}
          <div style={{ display: "grid", gridTemplateColumns: yCols.length === 1 ? "1fr" : "1fr 1fr", gap: 14 }}>
            {yCols.map((col, idx) => {
              const fig = buildFig(col, idx);
              return (
                <div key={col} style={S.card}>
                  {fig ? <PlotlyChart figure={fig} /> : (
                    <div style={{ height: 220, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b", fontSize: 13 }}>
                      Waiting for data on <strong style={{ color: "#818cf8", marginLeft: 4 }}>{col}</strong>…
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Event log */}
          <div style={S.card}>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#52525b", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
              Recent Events
            </div>
            <div style={{ overflowX: "auto" }}>
              {(seriesRef.current[yCols[0]] || []).length === 0 ? (
                <div style={{ color: "#52525b", fontSize: 13, padding: "10px 0" }}>
                  No data yet. {connected ? "Waiting for events…" : "Connect to start receiving data."}
                </div>
              ) : (
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "5px 10px", color: "#52525b", borderBottom: "1px solid rgba(255,255,255,.06)" }}>#</th>
                      <th style={{ textAlign: "left", padding: "5px 10px", color: "#52525b", borderBottom: "1px solid rgba(255,255,255,.06)" }}>Timestamp</th>
                      {yCols.map(c => <th key={c} style={{ textAlign: "right", padding: "5px 10px", color: "#52525b", borderBottom: "1px solid rgba(255,255,255,.06)" }}>{c}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {tsRef.current.slice(-10).reverse().map((ts, i) => {
                      const idx = tsRef.current.length - 1 - i;
                      return (
                        <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,.03)" }}>
                          <td style={{ padding: "4px 10px", color: "#3f3f46" }}>{totalRef.current - i}</td>
                          <td style={{ padding: "4px 10px", color: "#52525b", fontFamily: "monospace", fontSize: 11 }}>{String(ts).slice(11, 23)}</td>
                          {yCols.map((c, ci) => (
                            <td key={c} style={{ padding: "4px 10px", textAlign: "right", color: PALETTE[ci % PALETTE.length], fontFamily: "monospace" }}>
                              {(seriesRef.current[c] || [])[idx]?.toFixed(2) ?? "—"}
                            </td>
                          ))}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          {/* How to push data */}
          {!connected && (
            <div style={{ ...S.card, background: "rgba(99,102,241,.04)", border: "1px solid rgba(99,102,241,.15)" }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#818cf8", marginBottom: 8 }}>💡 How to push live data</div>
              <pre style={{ fontSize: 11, color: "#71717a", margin: 0, fontFamily: "monospace", whiteSpace: "pre-wrap" }}>{`import requests, time, random

STREAM_ID = "${selectedId}"
API_KEY   = "${selectedStream?.api_key || "YOUR_API_KEY"}"

while True:
    requests.post(
        f"http://localhost:8000/api/ingest/{selectedId}",
        json={"value": random.uniform(10, 100), "metric": random.randint(1, 50)},
        headers={"X-Stream-Key": API_KEY}
    )
    time.sleep(0.5)`}</pre>
            </div>
          )}
        </>
      )}
    </div>
  );
}
