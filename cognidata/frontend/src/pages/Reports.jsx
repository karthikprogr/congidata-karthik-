import { useEffect, useState, useMemo, Component } from "react";
import { api, dataApi } from "../api/client";
import PlotlyChart from "../components/PlotlyChart";
import Table from "../components/Table";

class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(e) { return { error: e }; }
  render() {
    if (this.state.error) return (
      <div style={{padding:40,color:"#f87171",background:"#09090b",minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column",gap:12}}>
        <div style={{fontSize:32}}>⚠️</div>
        <div style={{fontSize:16,fontWeight:600,color:"#f4f4f5"}}>Page Error</div>
        <div style={{fontSize:13,color:"#71717a",maxWidth:400,textAlign:"center"}}>{this.state.error.message}</div>
        <button onClick={()=>window.location.reload()} style={{padding:"8px 20px",borderRadius:8,border:"none",background:"#6366f1",color:"#fff",cursor:"pointer",fontSize:13}}>Reload</button>
      </div>
    );
    return this.props.children;
  }
}

const TABS = ["📋 Overview","🎨 Visual Report","📥 Export Center","🔬 Data Profiling","🕐 Scheduled Reports"];
const THEMES = ["plotly_dark","plotly","ggplot2","seaborn","simple_white"];
const PALETTES = [
  { name:"Indigo",  colors:["#6366f1","#8b5cf6","#a78bfa","#c4b5fd","#ddd6fe"] },
  { name:"Emerald", colors:["#10b981","#059669","#34d399","#6ee7b7","#a7f3d0"] },
  { name:"Sunset",  colors:["#f59e0b","#d97706","#fbbf24","#fcd34d","#fde68a"] },
  { name:"Ocean",   colors:["#0ea5e9","#0284c7","#38bdf8","#7dd3fc","#bae6fd"] },
];

export default function Reports() {
  const [tab, setTab]   = useState(0);
  const [info, setInfo] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoad] = useState(true);
  const [error, setErr] = useState(null);

  useEffect(() => {
    Promise.all([dataApi.info(), dataApi.preview(500)])
      .then(([i, p]) => { setInfo(i.data); setRows(p.data?.data || []); })
      .catch(e => setErr(e.response?.data?.detail || "Upload a dataset first."))
      .finally(() => setLoad(false));
  }, []);

  if (loading) return <Spinner />;
  if (error)   return <Empty msg={error} />;

  const numCols = info?.numeric_columns || [];
  const catCols = info?.categorical_columns || [];

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={{ display:"flex", alignItems:"center", gap:12 }}>
          <div style={S.icon}>📈</div>
          <div>
            <div style={S.title}>Reports</div>
            <div style={S.sub}>{info?.rows?.toLocaleString()} rows · {info?.columns} cols</div>
          </div>
        </div>
      </div>
      <div style={S.tabs}>
        {TABS.map((t, i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{ ...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b" }}>
            {t}
          </button>
        ))}
      </div>
      {tab === 0 && <OverviewTab info={info} rows={rows} numCols={numCols} catCols={catCols} />}
      {tab === 1 && <VisualReportTab info={info} rows={rows} numCols={numCols} catCols={catCols} />}
      {tab === 2 && <ExportCenterTab info={info} rows={rows} numCols={numCols} />}
      {tab === 3 && <DataProfilingTab />}
      {tab === 4 && <ScheduledReportsTab />}
    </div>
    </ErrorBoundary>
  );
}
function OverviewTab({ info, rows, numCols, catCols }) {
  const missing = Object.values(info?.missing_values || {}).reduce((a, b) => a + b, 0);
  const memMB = info?.memory_mb || 0;

  const dtypeCounts = useMemo(() => {
    const c = {};
    (info?.columns_info || []).forEach(col => { c[col.dtype] = (c[col.dtype] || 0) + 1; });
    return c;
  }, [info]);

  const missingCols = useMemo(() =>
    Object.entries(info?.missing_values || {}).filter(([, v]) => v > 0), [info]);

  const dtypeFig = Object.keys(dtypeCounts).length ? {
    data: [{ type:"pie", labels:Object.keys(dtypeCounts), values:Object.values(dtypeCounts), hole:0.4,
      marker:{ colors:["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#0ea5e9"] } }],
    layout: { title:{ text:"Column Types", font:{size:12} }, height:260, showlegend:true }
  } : null;

  const missingFig = missingCols.length ? {
    data: [{ type:"bar", x:missingCols.map(([k]) => k), y:missingCols.map(([, v]) => v),
      marker:{ color:"#f59e0b" } }],
    layout: { title:{ text:"Missing Values per Column", font:{size:12} }, height:240 }
  } : null;

  const numDesc = useMemo(() => {
    if (!rows.length || !numCols.length) return [];
    return numCols.slice(0, 15).map(col => {
      const vals = rows.map(r => Number(r[col])).filter(v => !isNaN(v));
      if (!vals.length) return null;
      const sorted = [...vals].sort((a, b) => a - b);
      const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
      const std = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length);
      return { Column:col, Count:vals.length, Mean:mean.toFixed(2), Std:std.toFixed(2),
        Min:sorted[0].toFixed(2), "25%":sorted[Math.floor(vals.length*0.25)].toFixed(2),
        "50%":sorted[Math.floor(vals.length*0.5)].toFixed(2),
        "75%":sorted[Math.floor(vals.length*0.75)].toFixed(2), Max:sorted[sorted.length-1].toFixed(2) };
    }).filter(Boolean);
  }, [rows, numCols]);

  const catDesc = useMemo(() => {
    if (!rows.length || !catCols.length) return [];
    return catCols.slice(0, 15).map(col => {
      const vals = rows.map(r => r[col]).filter(v => v != null);
      const counts = {};
      vals.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
      const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
      const nulls = (info?.missing_values?.[col] || 0);
      return { Column:col, Unique:sorted.length, "Top Value":sorted[0]?.[0] || "—",
        "Top Freq":sorted[0]?.[1] || 0, Missing:nulls };
    });
  }, [rows, catCols, info]);

  return (
    <div>
      <div style={{ display:"flex", gap:12, marginBottom:16, flexWrap:"wrap" }}>
        {[["Rows", info?.rows?.toLocaleString(), "#6366f1"],
          ["Columns", info?.columns, "#10b981"],
          ["Numeric", numCols.length, "#f59e0b"],
          ["Missing", missing, missing > 0 ? "#ef4444" : "#22c55e"],
          ["Memory", `${memMB} MB`, "#818cf8"]].map(([l, v, c]) => (
          <div key={l} style={S.kpi}>
            <div style={{ fontSize:22, fontWeight:700, color:c }}>{v}</div>
            <div style={{ fontSize:11, color:"#52525b", marginTop:3 }}>{l}</div>
          </div>
        ))}
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginBottom:14 }}>
        {dtypeFig && <Card title="Column Type Distribution"><PlotlyChart figure={dtypeFig} /></Card>}
        {missingFig ? <Card title="Missing Values"><PlotlyChart figure={missingFig} /></Card>
          : <Card title="Missing Values"><p style={{ color:"#22c55e", fontSize:13, padding:"20px 0" }}>✅ No missing values</p></Card>}
      </div>
      {numDesc.length > 0 && (
        <Card title="Numeric Summary" style={{ marginBottom:14 }}>
          <div style={{ overflowX:"auto" }}><Table data={numDesc} /></div>
        </Card>
      )}
      {catDesc.length > 0 && (
        <Card title="Categorical Summary">
          <div style={{ overflowX:"auto" }}><Table data={catDesc} /></div>
        </Card>
      )}
    </div>
  );
}
function VisualReportTab({ info, rows, numCols, catCols }) {
  const [title, setTitle]   = useState("COGNIDATA Report");
  const [theme, setTheme]   = useState(THEMES[0]);
  const [palette, setPalette] = useState(0);

  const pal = PALETTES[palette].colors;
  const dark = { template:theme, paper_bgcolor:"transparent", plot_bgcolor:"transparent",
    font:{ color:"#a1a1aa" }, height:280, margin:{ l:30, r:10, t:40, b:30 } };

  const histFig = useMemo(() => {
    const col = numCols[0]; if (!col) return null;
    const vals = rows.map(r => Number(r[col])).filter(v => !isNaN(v));
    return { data:[{ type:"histogram", x:vals, marker:{ color:pal[0], opacity:0.85 }, nbinsx:30 }],
      layout:{ ...dark, title:{ text:`Distribution: ${col}`, font:{size:12} } } };
  }, [numCols, rows, pal, theme]);

  const scatterFig = useMemo(() => {
    if (numCols.length < 2) return null;
    const [xc, yc] = numCols;
    const xs = rows.map(r => Number(r[xc])).filter(v => !isNaN(v));
    const ys = rows.map(r => Number(r[yc])).filter(v => !isNaN(v));
    const n = Math.min(xs.length, ys.length);
    const mx = xs.slice(0,n).reduce((a,b)=>a+b,0)/n, my = ys.slice(0,n).reduce((a,b)=>a+b,0)/n;
    const slope = xs.slice(0,n).reduce((a,v,i)=>a+(v-mx)*(ys[i]-my),0)/xs.slice(0,n).reduce((a,v)=>a+(v-mx)**2,0)||0;
    const trendY = xs.slice(0,n).map(v => my + slope*(v-mx));
    return { data:[
      { type:"scatter", mode:"markers", x:xs.slice(0,n), y:ys.slice(0,n), marker:{ color:pal[0], size:5, opacity:0.6 }, name:"Data" },
      { type:"scatter", mode:"lines", x:xs.slice(0,n), y:trendY, line:{ color:pal[1], width:2 }, name:"OLS Trend" },
    ], layout:{ ...dark, title:{ text:`${xc} vs ${yc}`, font:{size:12} } } };
  }, [numCols, rows, pal, theme]);

  const barFig = useMemo(() => {
    const col = catCols[0]; const num = numCols[0]; if (!col || !num) return null;
    const groups = {};
    rows.forEach(r => { const g = r[col]; const v = Number(r[num]); if (g != null && !isNaN(v)) { if (!groups[g]) groups[g] = []; groups[g].push(v); } });
    const top = Object.entries(groups).map(([k, vs]) => [k, vs.reduce((a,b)=>a+b,0)/vs.length]).sort((a,b)=>b[1]-a[1]).slice(0,10);
    return { data:[{ type:"bar", x:top.map(([k])=>k), y:top.map(([,v])=>v.toFixed(2)), marker:{ color:pal[0] } }],
      layout:{ ...dark, title:{ text:`Avg ${num} by ${col}`, font:{size:12} } } };
  }, [catCols, numCols, rows, pal, theme]);

  const heatFig = useMemo(() => {
    const cols = numCols.slice(0, 8); if (cols.length < 2) return null;
    const n = rows.length;
    const matrix = cols.map(c1 => cols.map(c2 => {
      const a = rows.map(r=>Number(r[c1])||0), b = rows.map(r=>Number(r[c2])||0);
      const ma = a.reduce((s,v)=>s+v,0)/n, mb = b.reduce((s,v)=>s+v,0)/n;
      const cov = a.reduce((s,v,i)=>s+(v-ma)*(b[i]-mb),0)/n;
      const sa = Math.sqrt(a.reduce((s,v)=>s+(v-ma)**2,0)/n)||1;
      const sb = Math.sqrt(b.reduce((s,v)=>s+(v-mb)**2,0)/n)||1;
      return cov/(sa*sb);
    }));
    return { data:[{ type:"heatmap", z:matrix, x:cols, y:cols, colorscale:"RdBu", zmid:0 }],
      layout:{ ...dark, title:{ text:"Correlation Heatmap", font:{size:12} } } };
  }, [numCols, rows, theme]);

  const trendFig = useMemo(() => {
    const col = numCols[0]; if (!col) return null;
    const vals = rows.map(r => Number(r[col])).filter(v => !isNaN(v));
    return { data:[{ type:"scatter", mode:"lines", x:vals.map((_,i)=>i), y:vals,
      fill:"tozeroy", line:{ color:pal[0], width:2 }, fillcolor:`${pal[0]}22` }],
      layout:{ ...dark, title:{ text:`Trend: ${col}`, font:{size:12} } } };
  }, [numCols, rows, pal, theme]);

  return (
    <div>
      <div style={{ display:"flex", gap:12, marginBottom:16, flexWrap:"wrap", alignItems:"flex-end" }}>
        <div style={{ flex:2, minWidth:200 }}>
          <label style={S.label}>Report Title</label>
          <input value={title} onChange={e=>setTitle(e.target.value)} style={{ ...S.input, width:"100%", boxSizing:"border-box" }} />
        </div>
        <div>
          <label style={S.label}>Theme</label>
          <select value={theme} onChange={e=>setTheme(e.target.value)} style={S.select}>
            {THEMES.map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label style={S.label}>Color Palette</label>
          <div style={{ display:"flex", gap:6, marginTop:4 }}>
            {PALETTES.map((p, i) => (
              <button key={p.name} onClick={() => setPalette(i)} title={p.name}
                style={{ width:20, height:20, borderRadius:"50%", border:"none", cursor:"pointer",
                  background:p.colors[0], boxShadow:palette===i?`0 0 0 2px #09090b,0 0 0 3px ${p.colors[0]}`:"none",
                  transform:palette===i?"scale(1.3)":"scale(1)" }} />
            ))}
          </div>
        </div>
      </div>

      <div style={{ padding:"12px 16px", borderRadius:10, background:"rgba(99,102,241,.08)", border:"1px solid rgba(99,102,241,.2)", marginBottom:16 }}>
        <div style={{ fontSize:14, fontWeight:700, color:"#f4f4f5" }}>{title}</div>
        <div style={{ fontSize:11, color:"#52525b", marginTop:2 }}>Generated: {new Date().toLocaleString()}</div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(460px,1fr))", gap:14 }}>
        {histFig    && <Card title="Distribution Histogram"><PlotlyChart figure={histFig} /></Card>}
        {scatterFig && <Card title="Correlation Scatter + OLS"><PlotlyChart figure={scatterFig} /></Card>}
        {barFig     && <Card title="Category Breakdown"><PlotlyChart figure={barFig} /></Card>}
        {heatFig    && <Card title="Correlation Heatmap"><PlotlyChart figure={heatFig} /></Card>}
        {trendFig   && <Card title="Trend Area Chart"><PlotlyChart figure={trendFig} /></Card>}
      </div>
    </div>
  );
}
function ExportCenterTab({ info, rows, numCols }) {
  const [chartType, setChartType] = useState("Histogram");
  const [chartCol, setChartCol]   = useState(numCols[0] || "");
  const [chartFig, setChartFig]   = useState(null);
  const [pdfTitle, setPdfTitle]   = useState("COGNIDATA Report");
  const [pdfSummary, setPdfSummary] = useState("");
  const [pdfInsights, setPdfInsights] = useState(false);
  const [pdfLoading, setPdfLoad]  = useState(false);
  const [pdfMsg, setPdfMsg]       = useState(null);

  const buildChart = () => {
    const col = chartCol;
    const vals = rows.map(r => Number(r[col])).filter(v => !isNaN(v));
    const dark = { template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent",
      font:{ color:"#a1a1aa" }, height:300, margin:{ l:30, r:10, t:40, b:30 } };
    let fig = null;
    if (chartType === "Histogram") fig = { data:[{ type:"histogram", x:vals, marker:{ color:"#6366f1", opacity:0.85 }, nbinsx:30 }], layout:{ ...dark, title:{ text:`Histogram: ${col}`, font:{size:12} } } };
    else if (chartType === "Box")  fig = { data:[{ type:"box", y:vals, marker:{ color:"#8b5cf6" }, name:col }], layout:{ ...dark, title:{ text:`Box Plot: ${col}`, font:{size:12} } } };
    else if (chartType === "Line") fig = { data:[{ type:"scatter", mode:"lines", x:vals.map((_,i)=>i), y:vals, line:{ color:"#6366f1", width:2 } }], layout:{ ...dark, title:{ text:`Line: ${col}`, font:{size:12} } } };
    else if (chartType === "Bar") {
      const top = vals.slice(0, 30);
      fig = { data:[{ type:"bar", x:top.map((_,i)=>i), y:top, marker:{ color:"#10b981" } }], layout:{ ...dark, title:{ text:`Bar: ${col}`, font:{size:12} } } };
    }
    setChartFig(fig);
  };

  const downloadCSV = async () => {
    const r = await api.get("/reports/export/csv", { responseType:"blob" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(r.data); a.download = "data.csv"; a.click();
  };

  const downloadExcel = async () => {
    const r = await api.get("/reports/export/excel", { responseType:"blob" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(r.data); a.download = "data.xlsx"; a.click();
  };

  const downloadJSON = async () => {
    const { data } = await api.get("/reports/export/json");
    const b = new Blob([JSON.stringify(data, null, 2)], { type:"application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "data.json"; a.click();
  };

  const downloadStatCSV = () => {
    if (!rows.length || !numCols.length) return;
    const header = ["Column","Count","Mean","Std","Min","Max"].join(",");
    const dataRows = numCols.map(col => {
      const vals = rows.map(r => Number(r[col])).filter(v => !isNaN(v));
      if (!vals.length) return null;
      const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
      const std = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length);
      return [col, vals.length, mean.toFixed(3), std.toFixed(3), Math.min(...vals).toFixed(3), Math.max(...vals).toFixed(3)].join(",");
    }).filter(Boolean);
    const blob = new Blob([[header, ...dataRows].join("\n")], { type:"text/csv" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "statistics.csv"; a.click();
  };

  const generatePDF = async () => {
    setPdfLoad(true); setPdfMsg(null);
    try {
      const r = await api.post("/reports/pdf", { title:pdfTitle, include_insights:pdfInsights }, { responseType:"blob" });
      const a = document.createElement("a"); a.href = URL.createObjectURL(r.data); a.download = `${pdfTitle}.pdf`; a.click();
      setPdfMsg({ ok:true, t:"PDF downloaded" });
    } catch(e) { setPdfMsg({ ok:false, t:e.response?.data?.detail || "PDF generation failed" }); }
    finally { setPdfLoad(false); }
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
      {/* Data exports */}
      <Card title="Data Export">
        <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
          <button onClick={downloadCSV} style={S.btn}>📥 CSV</button>
          <button onClick={downloadExcel} style={S.btn}>📊 Excel (multi-sheet)</button>
          <button onClick={downloadJSON} style={S.btn}>📋 JSON</button>
          <button onClick={downloadStatCSV} style={{ ...S.btn, background:"rgba(99,102,241,.15)", color:"#818cf8", border:"1px solid rgba(99,102,241,.3)" }}>📈 Statistics CSV</button>
        </div>
      </Card>

      {/* Chart export */}
      <Card title="Chart Export">
        <div style={{ display:"flex", gap:12, marginBottom:12, flexWrap:"wrap", alignItems:"flex-end" }}>
          <div>
            <label style={S.label}>Chart Type</label>
            <select value={chartType} onChange={e=>setChartType(e.target.value)} style={S.select}>
              {["Histogram","Box","Line","Bar"].map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label style={S.label}>Column</label>
            <select value={chartCol} onChange={e=>setChartCol(e.target.value)} style={S.select}>
              {numCols.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
          <button onClick={buildChart} style={S.btn}>📊 Preview Chart</button>
        </div>
        {chartFig && <PlotlyChart figure={chartFig} />}
      </Card>

      {/* PDF Report */}
      <Card title="PDF Report Generator">
        {pdfMsg && <div style={{ padding:"8px 12px", borderRadius:8, border:"1px solid", fontSize:12, marginBottom:10,
          background:pdfMsg.ok?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)",
          borderColor:pdfMsg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",
          color:pdfMsg.ok?"#34d399":"#f87171" }}>{pdfMsg.t}</div>}
        <div style={{ marginBottom:10 }}>
          <label style={S.label}>Report Title</label>
          <input value={pdfTitle} onChange={e=>setPdfTitle(e.target.value)} style={{ ...S.input, width:"100%", boxSizing:"border-box" }} />
        </div>
        <div style={{ marginBottom:10 }}>
          <label style={S.label}>Executive Summary (optional)</label>
          <textarea value={pdfSummary} onChange={e=>setPdfSummary(e.target.value)} rows={3}
            style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none" }} />
        </div>
        <label style={{ display:"flex", alignItems:"center", gap:8, cursor:"pointer", fontSize:13, color:"#71717a", marginBottom:12 }}>
          <input type="checkbox" checked={pdfInsights} onChange={e=>setPdfInsights(e.target.checked)} style={{ accentColor:"#6366f1" }} />
          Include AI insights (requires API key)
        </label>
        <button onClick={generatePDF} disabled={pdfLoading} style={S.btn}>
          {pdfLoading ? <><span className="spinner" style={{ width:14, height:14 }} /> Generating…</> : "📄 Generate & Download PDF"}
        </button>
      </Card>
    </div>
  );
}
function DataProfilingTab() {
  const [profiles, setProfiles] = useState(null);
  const [loading, setLoad]      = useState(false);

  const load = async () => {
    setLoad(true);
    try { setProfiles((await api.get("/reports/profile")).data); }
    catch { setProfiles([]); }
    finally { setLoad(false); }
  };

  useEffect(() => { load(); }, []);

  const completenessColor = (pct) => pct >= 90 ? "#22c55e" : pct >= 70 ? "#f59e0b" : "#ef4444";

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:14 }}>
        <span style={{ fontSize:13, color:"#71717a" }}>{profiles?.length || 0} columns profiled</span>
        <button onClick={load} disabled={loading} style={S.btn}>{loading ? "Loading…" : "↺ Refresh"}</button>
      </div>
      {loading && <div style={{ textAlign:"center", padding:"40px 0", color:"#52525b" }}>Profiling columns…</div>}
      <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
        {(profiles || []).slice(0, 20).map((col, i) => (
          <div key={i} style={{ background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:"14px 16px" }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:8 }}>
              <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                <span style={{ fontSize:13, fontWeight:600, color:"#f4f4f5" }}>{col.column}</span>
                <span style={{ fontSize:10, padding:"2px 8px", borderRadius:20, background:"rgba(99,102,241,.12)", color:"#818cf8" }}>{col.dtype}</span>
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <span style={{ fontSize:11, color:"#52525b" }}>{col.unique} unique</span>
                <span style={{ fontSize:11, color:col.nulls > 0 ? "#f59e0b" : "#22c55e" }}>{col.nulls} nulls</span>
              </div>
            </div>
            {/* Completeness bar */}
            <div style={{ marginBottom:8 }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:3 }}>
                <span style={{ fontSize:10, color:"#52525b" }}>Completeness</span>
                <span style={{ fontSize:10, color:completenessColor(col.completeness), fontWeight:600 }}>{col.completeness}%</span>
              </div>
              <div style={{ height:4, borderRadius:2, background:"rgba(255,255,255,.06)" }}>
                <div style={{ height:"100%", borderRadius:2, width:`${col.completeness}%`, background:completenessColor(col.completeness), transition:"width .3s" }} />
              </div>
            </div>
            {/* Stats */}
            {col.mean !== undefined && (
              <div style={{ display:"flex", gap:12, flexWrap:"wrap" }}>
                {[["Mean", col.mean], ["Std", col.std], ["Min", col.min], ["Max", col.max]].map(([l, v]) => (
                  <span key={l} style={{ fontSize:11, color:"#71717a" }}>{l}: <span style={{ color:"#a1a1aa" }}>{v}</span></span>
                ))}
              </div>
            )}
            {col.top_values && (
              <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginTop:4 }}>
                {Object.entries(col.top_values).slice(0, 5).map(([k, v]) => (
                  <span key={k} style={{ fontSize:10, padding:"2px 8px", borderRadius:20, background:"rgba(255,255,255,.04)", color:"#71717a" }}>
                    {String(k).slice(0, 20)}: {v}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {!loading && !profiles?.length && <p style={{ color:"#52525b", fontSize:13 }}>No profile data available.</p>}
      </div>
    </div>
  );
}

function ScheduledReportsTab() {
  const [schedules, setSchedules] = useState([]);
  const [form, setForm]           = useState({ name:"", frequency:"Daily", report_type:"pdf", email:"" });
  const [msg, setMsg]             = useState(null);
  const [running, setRunning]     = useState(false);

  const load = async () => {
    try { setSchedules((await api.get("/reports/schedule")).data); } catch { setSchedules([]); }
  };

  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!form.name.trim()) return;
    try {
      await api.post("/reports/schedule", form);
      setMsg({ ok:true, t:"Schedule created" });
      setForm({ name:"", frequency:"Daily", report_type:"pdf", email:"" });
      await load();
    } catch(e) { setMsg({ ok:false, t:e.response?.data?.detail || "Failed" }); }
  };

  const toggle = async (id) => {
    try { await api.patch(`/reports/schedule/${id}`); await load(); } catch {}
  };

  const del = async (id) => {
    try { await api.delete(`/reports/schedule/${id}`); await load(); } catch {}
  };

  const runAll = async () => {
    setRunning(true);
    try {
      const { data } = await api.post("/reports/schedule/run-all");
      setMsg({ ok:true, t:`Ran ${data.ran} schedule(s)` });
    } catch(e) { setMsg({ ok:false, t:e.response?.data?.detail || "Failed" }); }
    finally { setRunning(false); }
  };

  const freqColor = { Daily:"#6366f1", Weekly:"#10b981", Monthly:"#f59e0b", "On Upload":"#8b5cf6" };

  return (
    <div>
      {msg && <div style={{ padding:"8px 12px", borderRadius:8, border:"1px solid", fontSize:12, marginBottom:12,
        background:msg.ok?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)",
        borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",
        color:msg.ok?"#34d399":"#f87171" }}>{msg.t}</div>}

      {/* Create form */}
      <Card title="Create Schedule" style={{ marginBottom:14 }}>
        <div style={{ display:"flex", gap:12, flexWrap:"wrap", marginBottom:12 }}>
          <div style={{ flex:2, minWidth:160 }}>
            <label style={S.label}>Report Name</label>
            <input value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="My Report" style={{ ...S.input, width:"100%", boxSizing:"border-box" }} />
          </div>
          <div>
            <label style={S.label}>Frequency</label>
            <select value={form.frequency} onChange={e=>setForm(f=>({...f,frequency:e.target.value}))} style={S.select}>
              {["Daily","Weekly","Monthly","On Upload"].map(f => <option key={f}>{f}</option>)}
            </select>
          </div>
          <div>
            <label style={S.label}>Type</label>
            <select value={form.report_type} onChange={e=>setForm(f=>({...f,report_type:e.target.value}))} style={S.select}>
              {["pdf","csv","excel"].map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
        </div>
        <div style={{ display:"flex", gap:10 }}>
          <button onClick={create} style={S.btn}>+ Create Schedule</button>
          <button onClick={runAll} disabled={running} style={{ ...S.btn, background:"rgba(16,185,129,.15)", color:"#34d399", border:"1px solid rgba(16,185,129,.3)" }}>
            {running ? "Running…" : "▶ Run All Active Now"}
          </button>
        </div>
      </Card>

      {/* Active schedules */}
      <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
        {schedules.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No schedules yet.</p>}
        {schedules.map(s => (
          <div key={s.id} style={{ display:"flex", alignItems:"center", gap:12, padding:"12px 16px",
            background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:10 }}>
            <div style={{ flex:1 }}>
              <div style={{ fontSize:13, fontWeight:600, color:"#f4f4f5" }}>{s.name}</div>
              <div style={{ fontSize:11, color:"#52525b", marginTop:2 }}>
                Last run: {s.last_run ? new Date(s.last_run).toLocaleString() : "Never"}
              </div>
            </div>
            <span style={{ fontSize:10, padding:"3px 10px", borderRadius:20, background:`${freqColor[s.frequency] || "#6366f1"}18`, color:freqColor[s.frequency] || "#6366f1" }}>{s.frequency}</span>
            <span style={{ fontSize:10, padding:"3px 10px", borderRadius:20, background:"rgba(255,255,255,.04)", color:"#71717a" }}>{s.report_type}</span>
            <span style={{ fontSize:11, color:s.active?"#22c55e":"#52525b" }}>{s.active?"Active":"Paused"}</span>
            <button onClick={() => toggle(s.id)} style={{ padding:"4px 10px", borderRadius:6, border:"1px solid rgba(255,255,255,.09)", background:"transparent", color:"#71717a", fontSize:11, cursor:"pointer" }}>
              {s.active ? "⏸ Pause" : "▶ Resume"}
            </button>
            <button onClick={() => del(s.id)} style={{ padding:"4px 10px", borderRadius:6, border:"1px solid rgba(239,68,68,.3)", background:"transparent", color:"#f87171", fontSize:11, cursor:"pointer" }}>
              🗑
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
// ── Shared helpers ────────────────────────────────────────────────────────────
function Card({ title, children, style = {} }) {
  return (
    <div style={{ background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"14px 12px 8px", overflow:"hidden", ...style }}>
      {title && <div style={{ fontSize:11, fontWeight:600, color:"#3f3f46", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:6, paddingLeft:4 }}>{title}</div>}
      {children}
    </div>
  );
}
function Spinner() {
  return <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#09090b", gap:12 }}><span className="spinner" style={{ width:28, height:28 }} /><span style={{ color:"#52525b" }}>Loading…</span></div>;
}
function Empty({ msg }) {
  return <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#09090b" }}><div style={{ textAlign:"center", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.07)", borderRadius:16, padding:"48px 56px" }}><div style={{ fontSize:40, marginBottom:12 }}>📂</div><p style={{ color:"#a1a1aa", fontSize:15 }}>{msg}</p></div></div>;
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  kpi:    { flex:"1 1 120px", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:"14px 18px" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  label:  { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:  { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  select: { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none" },
};
