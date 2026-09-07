import { useEffect, useState } from "react";
import { api } from "../api/client";

// ── Error boundary — prevents any child crash from blanking the page ──────────
import { Component } from "react";
class Safe extends Component {
  state = { err: null };
  static getDerivedStateFromError(e) { return { err: e }; }
  render() {
    if (this.state.err) return (
      <div style={{ padding: 12, color: "#f87171", fontSize: 12, background: "rgba(239,68,68,.05)", borderRadius: 8 }}>
        ⚠ {this.state.err.message}
      </div>
    );
    return this.props.children;
  }
}

// ── Inline chart using Canvas API — zero external deps ────────────────────────
function MiniBar({ data, color = "#6366f1", height = 60 }) {
  if (!data?.length) return null;
  const max = Math.max(...data.map(d => d.value || 0), 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 2, height, padding: "4px 8px" }}>
      {data.slice(0, 20).map((d, i) => (
        <div key={i} title={`${d.label}: ${d.value}`} style={{
          flex: 1, background: color, borderRadius: "2px 2px 0 0",
          height: `${Math.max(4, (d.value / max) * 100)}%`,
          opacity: 0.8, minWidth: 4,
        }} />
      ))}
    </div>
  );
}

// ── Plotly chart — loaded dynamically, fails gracefully ───────────────────────
function Chart({ figure, height = 260 }) {
  const [Plot, setPlot] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    import("react-plotly.js").then(m => {
      if (!cancelled) setPlot(() => m.default);
    }).catch(e => {
      if (!cancelled) setErr(e.message);
    });
    return () => { cancelled = true; };
  }, []);

  if (!figure) return null;
  if (err) return <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b", fontSize: 12 }}>Chart unavailable</div>;
  if (!Plot) return <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "#52525b", fontSize: 12 }}>Loading…</div>;

  return (
    <Safe>
      <Plot
        data={figure.data || []}
        layout={{
          ...figure.layout,
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          font: { color: "#a1a1aa", family: "Inter,sans-serif", size: 11 },
          margin: { l: 40, r: 16, t: 30, b: 40 },
          height,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </Safe>
  );
}

const S = {
  page:      { padding: "20px 24px", background: "#09090b", minHeight: "100vh", color: "#e4e4e7", overflowY: "auto" },
  header:    { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 },
  title:     { fontSize: 20, fontWeight: 700, color: "#fff" },
  sub:       { fontSize: 12, color: "#71717a", marginTop: 2 },
  tabs:      { display: "flex", gap: 4, marginBottom: 20, borderBottom: "1px solid rgba(255,255,255,.06)" },
  tab:       (a) => ({ padding: "8px 16px", background: "transparent", border: "none", fontSize: 13, fontWeight: 500, cursor: "pointer", borderBottom: a ? "2px solid #6366f1" : "2px solid transparent", color: a ? "#818cf8" : "#71717a" }),
  card:      { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: 16, marginBottom: 14 },
  kpiGrid:   { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))", gap: 12, marginBottom: 20 },
  kpi:       { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, padding: "16px 18px" },
  kpiVal:    { fontSize: 26, fontWeight: 700, color: "#818cf8" },
  kpiLbl:    { fontSize: 11, color: "#71717a", marginTop: 4 },
  grid2:     { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 },
  chartCard: { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, overflow: "hidden" },
  chartTitle:{ fontSize: 12, fontWeight: 600, color: "#a1a1aa", padding: "10px 14px", borderBottom: "1px solid rgba(255,255,255,.05)" },
  input:     { background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 12px", color: "#e4e4e7", fontSize: 13, width: "100%", boxSizing: "border-box" },
  select:    { background: "#09090b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, padding: "8px 12px", color: "#e4e4e7", fontSize: 13 },
  btn:       { padding: "8px 16px", borderRadius: 8, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 13, fontWeight: 600, cursor: "pointer" },
  empty:     { textAlign: "center", padding: "60px 20px", color: "#52525b", fontSize: 14 },
  table:     { width: "100%", borderCollapse: "collapse", fontSize: 12 },
  th:        { padding: "8px 12px", textAlign: "left", color: "#71717a", borderBottom: "1px solid rgba(255,255,255,.06)", fontWeight: 600, fontSize: 11 },
  td:        { padding: "8px 12px", borderBottom: "1px solid rgba(255,255,255,.04)", color: "#e4e4e7" },
};

// ── Overview Tab ──────────────────────────────────────────────────────────────
function OverviewTab() {
  const [info, setInfo]     = useState(null);
  const [charts, setCharts] = useState([]);
  const [loading, setLoad]  = useState(false);
  const [palette, setPalette] = useState("Indigo");
  const PALETTES = ["Indigo", "Emerald", "Sunset", "Ocean"];

  const load = async (pal = palette) => {
    setLoad(true);
    try {
      const [infoRes, chartsRes] = await Promise.allSettled([
        api.get("/data/info"),
        api.get(`/viz/overview?max_charts=6&palette=${pal}`),
      ]);
      if (infoRes.status === "fulfilled") {
        const d = infoRes.value.data;
        if (d && typeof d.rows === "number") setInfo(d);
      }
      if (chartsRes.status === "fulfilled") setCharts(chartsRes.value.data?.charts || []);
    } catch {}
    setLoad(false);
  };

  useEffect(() => { load(); }, []);

  if (!info && !loading) return (
    <div style={S.empty}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>📤</div>
      <div style={{ fontWeight: 600, color: "#a1a1aa" }}>No dataset loaded</div>
      <div style={{ fontSize: 12, marginTop: 6 }}>Upload a CSV, Excel, or JSON file to see your dashboard</div>
    </div>
  );

  return (
    <div>
      {/* Palette */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "#71717a" }}>Palette:</span>
        {PALETTES.map(p => (
          <button key={p} onClick={() => { setPalette(p); load(p); }}
            style={{ padding: "4px 12px", borderRadius: 20, border: "1px solid", fontSize: 11, cursor: "pointer",
              background: palette === p ? "rgba(99,102,241,.2)" : "transparent",
              borderColor: palette === p ? "rgba(99,102,241,.5)" : "rgba(255,255,255,.1)",
              color: palette === p ? "#818cf8" : "#71717a" }}>
            {p}
          </button>
        ))}
        {loading && <span style={{ fontSize: 11, color: "#52525b" }}>Loading…</span>}
      </div>

      {/* KPI cards */}
      {info && (() => {
        const missingRaw = info.missing_values;
        const missing = typeof missingRaw === "number"
          ? missingRaw
          : (missingRaw && typeof missingRaw === "object")
            ? Object.values(missingRaw).reduce((a, b) => a + (Number(b) || 0), 0)
            : 0;
        return (
          <div style={S.kpiGrid}>
            {[
              ["Rows", info.rows?.toLocaleString(), "#6366f1"],
              ["Columns", info.columns, "#10b981"],
              ["Numeric", Array.isArray(info.numeric_columns) ? info.numeric_columns.length : (info.numeric_columns || 0), "#f59e0b"],
              ["Categorical", Array.isArray(info.categorical_columns) ? info.categorical_columns.length : (info.categorical_columns || 0), "#0ea5e9"],
              ["Missing", missing, missing > 0 ? "#ef4444" : "#22c55e"],
            ].map(([label, val, color]) => (
              <div key={label} style={S.kpi}>
                <div style={{ ...S.kpiVal, color }}>{typeof val === "object" ? "—" : (val ?? "—")}</div>
                <div style={S.kpiLbl}>{label}</div>
              </div>
            ))}
          </div>
        );
      })()}

      {/* Charts grid */}
      {charts.length > 0 && (
        <div style={S.grid2}>
          {charts.map((c, i) => (
            <div key={i} style={S.chartCard}>
              <div style={S.chartTitle}>{c.title}</div>
              <Safe>
                <Chart figure={c.plotly_json} height={260} />
              </Safe>
            </div>
          ))}
        </div>
      )}

      {!loading && charts.length === 0 && info && (
        <div style={{ ...S.card, textAlign: "center", color: "#52525b", padding: 30 }}>
          Charts are loading… if they don't appear, check your API key in Settings.
        </div>
      )}
    </div>
  );
}

// ── Data Explorer Tab ─────────────────────────────────────────────────────────
function ExplorerTab() {
  const [preview, setPreview] = useState(null);
  const [stats, setStats]     = useState(null);
  const [search, setSearch]   = useState("");
  const [page, setPage]       = useState(0);
  const PAGE_SIZE = 20;

  useEffect(() => {
    Promise.allSettled([
      api.get("/data/preview?n=500"),
      api.get("/data/stats"),
    ]).then(([p, s]) => {
      if (p.status === "fulfilled") setPreview(p.value.data);
      if (s.status === "fulfilled") setStats(s.value.data);
    });
  }, []);

  if (!preview) return <div style={S.empty}>No dataset loaded</div>;

  const rows = preview.data || [];
  const cols = preview.columns || [];
  const filtered = search
    ? rows.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(search.toLowerCase())))
    : rows;
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  return (
    <div>
      {/* Stats */}
      {stats && (
        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          {Object.entries(stats).slice(0, 6).map(([col, s]) => (
            <div key={col} style={{ ...S.kpi, flex: "1 1 130px" }}>
              <div style={{ fontSize: 11, color: "#71717a", marginBottom: 4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{col}</div>
              <div style={{ fontSize: 13, color: "#e4e4e7" }}>μ {typeof s.mean === "number" ? s.mean.toFixed(2) : "—"}</div>
              <div style={{ fontSize: 11, color: "#52525b" }}>σ {typeof s.std === "number" ? s.std.toFixed(2) : "—"}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginBottom: 12 }}>
        <input style={S.input} placeholder="Search rows…" value={search}
          onChange={e => { setSearch(e.target.value); setPage(0); }} />
      </div>

      <div style={{ ...S.card, padding: 0, overflowX: "auto" }}>
        <table style={S.table}>
          <thead>
            <tr>{cols.map(c => <th key={c} style={S.th}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {paged.map((row, i) => (
              <tr key={i}>
                {cols.map(c => <td key={c} style={S.td}>{String(row[c] ?? "").slice(0, 60)}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderTop: "1px solid rgba(255,255,255,.05)", fontSize: 12, color: "#71717a" }}>
          <span>{filtered.length} rows{search ? ` (filtered from ${rows.length})` : ""}</span>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
              style={{ ...S.btn, padding: "4px 10px", fontSize: 11, opacity: page === 0 ? 0.4 : 1 }}>← Prev</button>
            <span style={{ padding: "4px 8px" }}>{page + 1} / {totalPages || 1}</span>
            <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
              style={{ ...S.btn, padding: "4px 10px", fontSize: 11, opacity: page >= totalPages - 1 ? 0.4 : 1 }}>Next →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Charts Tab ────────────────────────────────────────────────────────────────
function ChartsTab() {
  const [info, setInfo]      = useState(null);
  const [xCol, setXCol]      = useState("");
  const [yCol, setYCol]      = useState("");
  const [chartType, setType] = useState("Bar");
  const [chart, setChart]    = useState(null);
  const [loading, setLoad]   = useState(false);
  const [error, setError]    = useState("");
  const TYPES = [
    // Classic
    "Bar", "Line", "Scatter", "Pie", "Histogram", "Box", "Heatmap", "Area",
    "Treemap", "Radar", "Waterfall", "Stacked Bar", "Stacked Area",
    "Bubble", "Violin", "Funnel", "Sunburst",
    "Marimekko", "Table with Charts", "3D Area",
    // 2026 Trending
    "Sankey", "Beeswarm", "Bullet", "Small Multiples",
    "Rose", "Time Series", "Infographic",
  ];

  useEffect(() => {
    api.get("/data/info").then(r => {
      setInfo(r.data);
      const cols = r.data?.columns_info?.map(c => c.name) || [];
      if (cols[0]) setXCol(cols[0]);
      if (cols[1]) setYCol(cols[1]);
    }).catch(() => {});
  }, []);

  const build = async () => {
    if (!xCol) return;
    setLoad(true); setError("");
    try {
      // Map display names to backend chart type strings
      const typeMap = {
        "Stacked Bar": "stacked_bar",
        "Stacked Area": "stacked_area",
        "Table with Charts": "table_sparkline",
        "3D Area": "3d_area",
        "Marimekko": "marimekko",
        // 2026 trending
        "Sankey": "sankey",
        "Beeswarm": "beeswarm",
        "Bullet": "bullet",
        "Small Multiples": "small multiples",
        "Rose": "rose",
        "Time Series": "timeseries",
        "Network Graph": "network",
        "Gantt": "gantt",
        // Advanced / AI-Era
        "Parallel Coordinates": "parallel coordinates",
        "Chord": "chord",
        "Hexbin": "hexbin",
        "Ridgeline": "ridgeline",
        "Streamgraph": "streamgraph",
        "Dendrogram": "dendrogram",
        "Voronoi": "voronoi",
        "Uncertainty": "uncertainty",
        "PCA": "pca",
        "SHAP": "shap",
        "Choropleth": "choropleth",
        "Event Stream": "event stream",
        // Statistical
        "Q-Q Plot": "qq plot",
        "ECDF": "ecdf",
        "KDE": "kde",
        "Rug Plot": "rug plot",
        "Dot Plot": "dot plot",
        "Lollipop": "lollipop",
        "Slope Chart": "slope chart",
        "Dumbbell": "dumbbell",
        "Diverging Bar": "diverging bar",
        // Business & Financial
        "Candlestick": "candlestick",
        "Pair Plot": "pair plot",
        "Donut": "donut",
        "Waffle": "waffle",
        "Pyramid": "pyramid",
        "100% Stacked": "100% stacked",
        // Time-Series
        "ACF": "acf",
        "Contour": "contour",
        "Run Chart": "run chart",
        "Control Chart": "control chart",
        // Creative
        "Polar Line": "polar line",
        "Radial Bar": "radial bar",
        "Circle Packing": "circle packing",
        "Arc Diagram": "arc diagram",
        "Spiral": "spiral",
        "Funnel Area": "funnel area",
        // ML & AI
        "ROC Curve": "roc curve",
        "Precision Recall": "precision recall",
        "Confusion Matrix": "confusion matrix",
        "Learning Curve": "learning curve",
        "Monte Carlo": "monte carlo",
        "Drawdown": "drawdown",
        // Matrix & Correlation
        "Correlogram": "correlogram",
        "Cluster Heatmap": "cluster heatmap",
        "Radial Heatmap": "radial heatmap",
        "Faceted Heatmap": "faceted heatmap",
        // Hierarchical
        "Icicle": "icicle",
        "Surface": "surface",
        // Text & Bonus
        "Word Frequency": "word frequency",
        "Horizon": "horizon",
        "Animated Bubble": "animated bubble",
        // Statistical Advanced
        "PDF Plot": "pdf plot",
        "Kaplan-Meier": "kaplan meier",
        "Periodogram": "periodogram",
        "Adjacency Matrix": "adjacency matrix",
        "Pareto": "pareto frontier",
        "Manhattan": "manhattan plot",
        "Volcano": "volcano plot",
        // Finance & Ops
        "Dual Axis": "dual axis",
        "KPI Traffic Light": "kpi traffic light",
        "Efficient Frontier": "efficient frontier",
        "Gain Chart": "gain chart",
        // Spatial & Signal
        "Delaunay": "delaunay",
        "Convex Hull": "convex hull",
        "Cross Correlation": "cross correlation",
        "PACF": "pacf",
        "Log Heatmap": "log heatmap",
        // Composite
        "Variance Analysis": "variance analysis",
        "Composite": "composite",
        "3D Volume": "3d scatter volume",
        // Survival & Signal
        "Nelson-Aalen": "nelson aalen",
        "Hazard Function": "hazard function",
        "ACF Heatmap": "autocorrelation heatmap",
        "Scalogram": "scalogram",
        "Coherence": "coherence",
        // Network & Security
        "Community Graph": "community graph",
        "Attack Graph": "attack graph",
        "Animated Network": "animated network",
        "Linked Brushing": "linked brushing",
        // Business Intelligence
        "Sensitivity Analysis": "sensitivity analysis",
        "Strategy Map": "strategy map",
        "Balanced Scorecard": "balanced scorecard",
        // Spatial & UX
        "Alpha Shape": "alpha shape",
        "Faceted Grid": "faceted grid",
        "User Journey": "user journey",
        // Hybrid & Narrative
        "Sankey Heatmap": "sankey heatmap",
        "Narrative": "narrative",
        "Storyboard": "storyboard",
      };
      const effectiveType = typeMap[chartType] || chartType;
      const effectiveY = yCol || xCol;
      const { data } = await api.post("/viz/custom", {
        chart_type: effectiveType,
        x_col: xCol,
        y_col: effectiveY,
      });
      setChart(data?.plotly_json || data);
    } catch(e) {
      const detail = e.response?.data?.detail || e.message || "Chart build failed";
      setError(detail);
    }
    setLoad(false);
  };

  const cols = info?.columns_info?.map(c => c.name) || [];
  if (!info) return <div style={S.empty}>No dataset loaded</div>;

  return (
    <div>
      <div style={{ ...S.card, display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
        <div style={{ flex: "1 1 120px" }}>
          <div style={{ fontSize: 11, color: "#71717a", marginBottom: 4 }}>Chart Type</div>
          <select style={S.select} value={chartType} onChange={e => setType(e.target.value)}>
            <optgroup label="── Classic ──">
              {["Bar","Line","Scatter","Pie","Histogram","Box","Heatmap","Area","Treemap","Radar","Waterfall","Stacked Bar","Stacked Area","Bubble","Violin","Funnel","Sunburst","Marimekko","Table with Charts","3D Area"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── 2026 Trending ──">
              {["Sankey","Beeswarm","Bullet","Small Multiples","Rose","Time Series","Infographic","Network Graph","Gantt"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Advanced / AI-Era ──">
              {["Parallel Coordinates","Chord","Hexbin","Ridgeline","Streamgraph","Dendrogram","Voronoi","Uncertainty","PCA","SHAP","Choropleth","Event Stream"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Statistical ──">
              {["Q-Q Plot","ECDF","KDE","Rug Plot","Dot Plot","Lollipop","Slope Chart","Dumbbell","Diverging Bar"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Business & Financial ──">
              {["Candlestick","Pair Plot","Donut","Waffle","Pyramid","100% Stacked"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Time-Series ──">
              {["ACF","Contour","Run Chart","Control Chart"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Creative ──">
              {["Polar Line","Radial Bar","Circle Packing","Arc Diagram","Spiral","Funnel Area"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── ML & AI ──">
              {["ROC Curve","Precision Recall","Confusion Matrix","Learning Curve","Monte Carlo","Drawdown"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Matrix & Correlation ──">
              {["Correlogram","Cluster Heatmap","Radial Heatmap","Faceted Heatmap"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Hierarchical ──">
              {["Icicle","Surface"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Text & Bonus ──">
              {["Word Frequency","Horizon","Animated Bubble"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Statistical Advanced ──">
              {["PDF Plot","Kaplan-Meier","Periodogram","Adjacency Matrix","Pareto","Manhattan","Volcano"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Finance & Ops ──">
              {["Dual Axis","KPI Traffic Light","Efficient Frontier","Gain Chart"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Spatial & Signal ──">
              {["Delaunay","Convex Hull","Cross Correlation","PACF","Log Heatmap"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Composite ──">
              {["Variance Analysis","Composite","3D Volume"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Survival & Signal ──">
              {["Nelson-Aalen","Hazard Function","ACF Heatmap","Scalogram","Coherence"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Network & Security ──">
              {["Community Graph","Attack Graph","Animated Network","Linked Brushing"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Business Intelligence ──">
              {["Sensitivity Analysis","Strategy Map","Balanced Scorecard","KPI Traffic Light"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Spatial & UX ──">
              {["Alpha Shape","Faceted Grid","User Journey"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
            <optgroup label="── Hybrid & Narrative ──">
              {["Sankey Heatmap","Narrative","Storyboard"].map(t => <option key={t}>{t}</option>)}
            </optgroup>
          </select>
        </div>
        <div style={{ flex: "1 1 140px" }}>
          <div style={{ fontSize: 11, color: "#71717a", marginBottom: 4 }}>X Column</div>
          <select style={S.select} value={xCol} onChange={e => setXCol(e.target.value)}>
            {cols.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div style={{ flex: "1 1 140px" }}>
          <div style={{ fontSize: 11, color: "#71717a", marginBottom: 4 }}>Y Column</div>
          <select style={S.select} value={yCol} onChange={e => setYCol(e.target.value)}>
            <option value="">— same as X —</option>
            {cols.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <button onClick={build} disabled={loading || !xCol} style={S.btn}>
          {loading ? "Building…" : "📊 Build Chart"}
        </button>
      </div>
      {error && <div style={{ color: "#f87171", fontSize: 13, marginBottom: 12, padding: "8px 12px", background: "rgba(239,68,68,.05)", borderRadius: 8 }}>{error}</div>}
      {chartType === "Pie" && (
        <div style={{ fontSize: 12, color: "#f59e0b", marginBottom: 12, padding: "6px 12px", background: "rgba(251,191,36,.05)", borderRadius: 8 }}>
          💡 Pie: X = category, Y = numeric value
        </div>
      )}
      {["Waterfall", "Funnel"].includes(chartType) && (
        <div style={{ fontSize: 12, color: "#0ea5e9", marginBottom: 12, padding: "6px 12px", background: "rgba(14,165,233,.05)", borderRadius: 8 }}>
          💡 {chartType}: X = labels, Y = numeric values
        </div>
      )}
      {["Radar", "Heatmap"].includes(chartType) && (
        <div style={{ fontSize: 12, color: "#10b981", marginBottom: 12, padding: "6px 12px", background: "rgba(16,185,129,.05)", borderRadius: 8 }}>
          💡 {chartType}: uses all numeric columns automatically
        </div>
      )}
      {chartType === "Marimekko" && (
        <div style={{ fontSize: 12, color: "#a855f7", marginBottom: 12, padding: "6px 12px", background: "rgba(168,85,247,.05)", borderRadius: 8 }}>
          💡 Marimekko: X = category, Y = numeric — bar width = share of total
        </div>
      )}
      {chartType === "Table with Charts" && (
        <div style={{ fontSize: 12, color: "#06b6d4", marginBottom: 12, padding: "6px 12px", background: "rgba(6,182,212,.05)", borderRadius: 8 }}>
          💡 Table with Charts: shows data table with sparklines — no column selection needed
        </div>
      )}
      {chartType === "3D Area" && (
        <div style={{ fontSize: 12, color: "#f97316", marginBottom: 12, padding: "6px 12px", background: "rgba(249,115,22,.05)", borderRadius: 8 }}>
          💡 3D Area: uses first 3 numeric columns as X, Y, Z axes automatically
        </div>
      )}
      {chartType === "Sankey" && (
        <div style={{ fontSize: 12, color: "#6366f1", marginBottom: 12, padding: "6px 12px", background: "rgba(99,102,241,.05)", borderRadius: 8 }}>
          🔀 Sankey/Alluvial: X = source category, Y = target category — shows flow between groups
        </div>
      )}
      {chartType === "Beeswarm" && (
        <div style={{ fontSize: 12, color: "#10b981", marginBottom: 12, padding: "6px 12px", background: "rgba(16,185,129,.05)", borderRadius: 8 }}>
          🐝 Beeswarm: X = category (optional), Y = numeric — shows every data point without overlap
        </div>
      )}
      {chartType === "Bullet" && (
        <div style={{ fontSize: 12, color: "#f59e0b", marginBottom: 12, padding: "6px 12px", background: "rgba(245,158,11,.05)", borderRadius: 8 }}>
          🎯 Bullet Chart: compact KPI view — actual vs target vs performance range for all numeric columns
        </div>
      )}
      {chartType === "Small Multiples" && (
        <div style={{ fontSize: 12, color: "#8b5cf6", marginBottom: 12, padding: "6px 12px", background: "rgba(139,92,246,.05)", borderRadius: 8 }}>
          🔲 Small Multiples: X = category (facet), Y = numeric — side-by-side comparison grid
        </div>
      )}
      {chartType === "Rose" && (
        <div style={{ fontSize: 12, color: "#ec4899", marginBottom: 12, padding: "6px 12px", background: "rgba(236,72,153,.05)", borderRadius: 8 }}>
          🌹 Rose/Polar Area: X = category — visually appealing alternative to pie charts
        </div>
      )}
      {chartType === "Time Series" && (
        <div style={{ fontSize: 12, color: "#0ea5e9", marginBottom: 12, padding: "6px 12px", background: "rgba(14,165,233,.05)", borderRadius: 8 }}>
          📈 Time Series: X = time/index column — multi-layered with range slider for large datasets
        </div>
      )}
      {chartType === "Infographic" && (
        <div style={{ fontSize: 12, color: "#a855f7", marginBottom: 12, padding: "6px 12px", background: "rgba(168,85,247,.05)", borderRadius: 8 }}>
          📰 Infographic: storytelling summary — KPI cards with delta indicators for all numeric columns
        </div>
      )}
      {chartType === "Network Graph" && (
        <div style={{ fontSize: 12, color: "#6366f1", marginBottom: 12, padding: "6px 12px", background: "rgba(99,102,241,.05)", borderRadius: 8 }}>
          🕸 Network Graph: X = source node, Y = target node (category columns) — node size = connection count. Falls back to correlation network if no category columns.
        </div>
      )}
      {chartType === "Gantt" && (
        <div style={{ fontSize: 12, color: "#10b981", marginBottom: 12, padding: "6px 12px", background: "rgba(16,185,129,.05)", borderRadius: 8 }}>
          📅 Gantt: X = task/name column, Y = duration/numeric — auto-detects start/end columns if present (e.g. "start_date", "end_date")
        </div>
      )}
      {chartType === "Parallel Coordinates" && (
        <div style={{ fontSize: 12, color: "#6366f1", marginBottom: 12, padding: "6px 12px", background: "rgba(99,102,241,.05)", borderRadius: 8 }}>
          📐 Parallel Coordinates: uses all numeric columns — each line = one record, great for high-dimensional data
        </div>
      )}
      {chartType === "Chord" && (
        <div style={{ fontSize: 12, color: "#8b5cf6", marginBottom: 12, padding: "6px 12px", background: "rgba(139,92,246,.05)", borderRadius: 8 }}>
          🔵 Chord: X = source category, Y = target category — circular flow diagram showing dense interconnections
        </div>
      )}
      {chartType === "Hexbin" && (
        <div style={{ fontSize: 12, color: "#f59e0b", marginBottom: 12, padding: "6px 12px", background: "rgba(245,158,11,.05)", borderRadius: 8 }}>
          🔷 Hexbin: X + Y = two numeric columns — density heatmap, better than scatter for large datasets
        </div>
      )}
      {chartType === "Ridgeline" && (
        <div style={{ fontSize: 12, color: "#10b981", marginBottom: 12, padding: "6px 12px", background: "rgba(16,185,129,.05)", borderRadius: 8 }}>
          🏔 Ridgeline: X = category, Y = numeric — overlapping distributions per group (Joy Plot)
        </div>
      )}
      {chartType === "Streamgraph" && (
        <div style={{ fontSize: 12, color: "#0ea5e9", marginBottom: 12, padding: "6px 12px", background: "rgba(14,165,233,.05)", borderRadius: 8 }}>
          🌊 Streamgraph: X = time/index column — stacked area as % share over time, shows composition flow
        </div>
      )}
      {chartType === "Dendrogram" && (
        <div style={{ fontSize: 12, color: "#ec4899", marginBottom: 12, padding: "6px 12px", background: "rgba(236,72,153,.05)", borderRadius: 8 }}>
          🌳 Dendrogram: uses all numeric columns — hierarchical clustering tree, no column selection needed
        </div>
      )}
      {chartType === "Voronoi" && (
        <div style={{ fontSize: 12, color: "#f97316", marginBottom: 12, padding: "6px 12px", background: "rgba(249,115,22,.05)", borderRadius: 8 }}>
          🔺 Voronoi: X + Y = two numeric columns — spatial partitioning diagram (requires scipy)
        </div>
      )}
      {chartType === "Uncertainty" && (
        <div style={{ fontSize: 12, color: "#6366f1", marginBottom: 12, padding: "6px 12px", background: "rgba(99,102,241,.05)", borderRadius: 8 }}>
          📊 Uncertainty/Confidence Bands: X = index/time, Y = numeric — shows rolling mean ± 2σ confidence interval
        </div>
      )}
      {chartType === "PCA" && (
        <div style={{ fontSize: 12, color: "#a855f7", marginBottom: 12, padding: "6px 12px", background: "rgba(168,85,247,.05)", borderRadius: 8 }}>
          🧬 PCA 2D Projection: uses all numeric columns — dimensionality reduction scatter plot (t-SNE approximation)
        </div>
      )}
      {chartType === "SHAP" && (
        <div style={{ fontSize: 12, color: "#ef4444", marginBottom: 12, padding: "6px 12px", background: "rgba(239,68,68,.05)", borderRadius: 8 }}>
          🤖 SHAP/Feature Importance: Y = target column — trains Random Forest and shows feature importances
        </div>
      )}
      {chartType === "Choropleth" && (
        <div style={{ fontSize: 12, color: "#10b981", marginBottom: 12, padding: "6px 12px", background: "rgba(16,185,129,.05)", borderRadius: 8 }}>
          🌍 Choropleth: X = country/region names, Y = numeric value — world map colored by value
        </div>
      )}
      {chartType === "Event Stream" && (
        <div style={{ fontSize: 12, color: "#f59e0b", marginBottom: 12, padding: "6px 12px", background: "rgba(245,158,11,.05)", borderRadius: 8 }}>
          ⚡ Event Stream: X = event type column — temporal event timeline, great for logs and IoT data
        </div>
      )}
      {chart && (
        <div style={S.chartCard}>
          <Safe><Chart figure={chart} height={420} /></Safe>
        </div>
      )}
    </div>
  );
}

// ── Data Doctor Tab ───────────────────────────────────────────────────────────
function DoctorTab() {
  const [report, setReport] = useState(null);
  const [loading, setLoad]  = useState(false);

  const run = async () => {
    setLoad(true);
    try { const { data } = await api.get("/data/doctor"); setReport(data); }
    catch {}
    setLoad(false);
  };

  useEffect(() => { run(); }, []);

  if (loading) return <div style={S.empty}>Running diagnostics…</div>;
  if (!report) return <div style={S.empty}><button onClick={run} style={S.btn}>🩺 Run Data Doctor</button></div>;

  const score = report?.health_score ?? report?.score ?? 0;
  const scoreColor = score >= 80 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";
  const issues = report?.issues || [];

  return (
    <div>
      <div style={{ ...S.card, display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ width: 80, height: 80, borderRadius: "50%", border: `4px solid ${scoreColor}`, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <span style={{ fontSize: 22, fontWeight: 700, color: scoreColor }}>{score}</span>
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#fff" }}>Data Health Score</div>
          <div style={{ fontSize: 13, color: "#71717a", marginTop: 4 }}>
            {score >= 80 ? "✅ Your data looks healthy" : score >= 50 ? "⚠️ Some issues detected" : "❌ Data needs attention"}
          </div>
        </div>
        <button onClick={run} style={{ ...S.btn, marginLeft: "auto", padding: "6px 14px", fontSize: 12 }}>Refresh</button>
      </div>

      {issues.length > 0 && (
        <div style={S.card}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#f87171", marginBottom: 10 }}>⚠ Issues Found</div>
          {issues.map((issue, i) => (
            <div key={i} style={{ padding: "6px 0", borderBottom: "1px solid rgba(255,255,255,.04)", fontSize: 13, color: "#a1a1aa" }}>
              • {typeof issue === "string" ? issue : JSON.stringify(issue)}
            </div>
          ))}
        </div>
      )}

      {report?.columns && (
        <div style={S.card}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#a1a1aa", marginBottom: 10 }}>Column Analysis</div>
          <div style={{ overflowX: "auto" }}>
            <table style={S.table}>
              <thead>
                <tr>{["Column", "Type", "Missing", "Unique", "Status"].map(h => <th key={h} style={S.th}>{h}</th>)}</tr>
              </thead>
              <tbody>
                {Object.entries(report.columns).map(([col, info]) => (
                  <tr key={col}>
                    <td style={S.td}>{col}</td>
                    <td style={S.td}><span style={{ padding: "2px 6px", borderRadius: 4, fontSize: 10, background: "rgba(99,102,241,.1)", color: "#818cf8" }}>{info.type || "—"}</span></td>
                    <td style={S.td}>{info.missing ?? 0}</td>
                    <td style={S.td}>{info.unique ?? "—"}</td>
                    <td style={S.td}>
                      <span style={{ padding: "2px 6px", borderRadius: 4, fontSize: 10, background: (info.missing || 0) > 0 ? "rgba(251,191,36,.1)" : "rgba(34,197,94,.1)", color: (info.missing || 0) > 0 ? "#fbbf24" : "#4ade80" }}>
                        {(info.missing || 0) > 0 ? "⚠ Has nulls" : "✓ Clean"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
const TABS = ["📊 Overview", "🔍 Data Explorer", "📈 Charts", "🩺 Data Doctor"];

export default function Dashboard() {
  const [tab, setTab]     = useState(0);
  const [dsInfo, setDsInfo] = useState(null);

  useEffect(() => {
    api.get("/data/info").then(r => {
      const d = r.data;
      // Guard: only set if it looks like dataset info, not raw data
      if (d && typeof d.rows === "number") setDsInfo(d);
    }).catch(() => {});
  }, []);

  return (
    <Safe>
      <div style={S.page}>
        <div style={S.header}>
          <div>
            <div style={S.title}>📊 Dashboard</div>
            <div style={S.sub}>
              {dsInfo
                ? `${dsInfo.rows?.toLocaleString()} rows · ${dsInfo.columns} columns`
                : "Upload a dataset to get started"}
            </div>
          </div>
          {dsInfo && (
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => api.post("/data/clean").catch(() => {})}
                style={{ ...S.btn, background: "rgba(16,185,129,.15)", color: "#34d399", border: "1px solid rgba(16,185,129,.3)" }}>
                🧹 Clean
              </button>
              <button onClick={() => api.get("/reports/export/csv").then(r => {
                const a = document.createElement("a");
                a.href = URL.createObjectURL(new Blob([r.data]));
                a.download = "export.csv"; a.click();
              }).catch(() => {})}
                style={{ ...S.btn, background: "rgba(99,102,241,.15)", color: "#818cf8", border: "1px solid rgba(99,102,241,.3)" }}>
                ⬇ Export
              </button>
            </div>
          )}
        </div>

        <div style={S.tabs}>
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setTab(i)} style={S.tab(tab === i)}>{t}</button>
          ))}
        </div>

        <Safe>
          {tab === 0 && <OverviewTab />}
          {tab === 1 && <ExplorerTab />}
          {tab === 2 && <ChartsTab />}
          {tab === 3 && <DoctorTab />}
        </Safe>
      </div>
    </Safe>
  );
}
