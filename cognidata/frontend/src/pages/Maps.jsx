import { useEffect, useState, useCallback, useMemo, Component } from "react";
import { api } from "../api/client";
import PlotlyChart from "../components/PlotlyChart";
import LeafletMap from "../components/LeafletMap";

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

const TABS = ["🗺️ Choropleth","🔷 H3 Hex","🔀 Flow Map","🛰️ Satellite","🔵 Geo Cluster","🤖 AI Insight","🏙️ Digital Twin","✂️ Polygon Filter","⏱️ Geo Diff","⏱️ Isochrone"];
const COLOR_SCALES = ["Viridis","RdYlGn","Blues","Reds","Plasma","Turbo","Cividis","RdBu"];
const SCOPES = ["world","usa","europe","asia","africa","north america","south america"];
const MAP_STYLES = ["carto-darkmatter","carto-positron","open-street-map","stamen-terrain","stamen-watercolor","white-bg"];

export default function Maps() {
  const [tab, setTab]   = useState(0);
  const [cols, setCols] = useState({ all_cols:[], lat_hints:[], lon_hints:[], location_hints:[], numeric_cols:[] });
  const [error, setErr] = useState(null);

  useEffect(() => {
    api.get("/maps/columns").then(({data}) => setCols(data)).catch(e => setErr(e.response?.data?.detail || "Upload a dataset first"));
  }, []);

  if (error) return <Empty msg={error} />;

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>🗺️</div>
        <div>
          <div style={S.title}>Advanced Maps</div>
          <div style={S.sub}>Choropleth · H3 Hex Binning · Flow Maps</div>
        </div>
      </div>
      <div style={S.tabs}>
        {TABS.map((t,i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>
            {t}
          </button>
        ))}
      </div>
      {tab === 0 && <ChoroplethTab cols={cols} />}
      {tab === 1 && <H3Tab cols={cols} />}
      {tab === 2 && <FlowTab cols={cols} />}
      {tab === 3 && <SatelliteTab cols={cols} />}
      {tab === 4 && <GeoClusterTab cols={cols} />}
      {tab === 5 && <AIGeoInsightTab cols={cols} />}
      {tab === 6 && <DigitalTwinTab cols={cols} />}
      {tab === 7 && <PolygonFilterTab cols={cols} />}
      {tab === 8 && <GeoDiffTab cols={cols} />}
      {tab === 9 && <IsochroneTab cols={cols} />}
    </div>
    </ErrorBoundary>
  );
}

function ChoroplethTab({ cols }) {
  const [locCol, setLocCol]   = useState(cols.location_hints?.[0] || cols.all_cols?.[0] || "");
  const [valCol, setValCol]   = useState(cols.numeric_cols?.[0] || "");
  const [scope, setScope]     = useState("world");
  const [scale, setScale]     = useState("Viridis");
  const [title, setTitle]     = useState("Choropleth Map");
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [err, setErr]         = useState(null);

  useEffect(() => {
    if (cols.location_hints?.[0]) setLocCol(cols.location_hints[0]);
    if (cols.numeric_cols?.[0]) setValCol(cols.numeric_cols[0]);
  }, [cols]);

  const generate = async () => {
    setLoad(true); setErr(null);
    try {
      const { data } = await api.post("/maps/choropleth", { location_col:locCol, value_col:valCol, scope, color_scale:scale, title });
      setResult(data);
    } catch(e) { setErr(e.response?.data?.detail || "Failed"); }
    finally { setLoad(false); }
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Location Column" val={locCol} set={setLocCol} opts={cols.all_cols} />
          <Sel label="Value Column" val={valCol} set={setValCol} opts={cols.numeric_cols} />
          <Sel label="Scope" val={scope} set={setScope} opts={SCOPES} />
          <Sel label="Color Scale" val={scale} set={setScale} opts={COLOR_SCALES} />
          <div style={{flex:2,minWidth:200}}>
            <label style={S.label}>Title</label>
            <input value={title} onChange={e=>setTitle(e.target.value)} style={S.input} />
          </div>
        </div>
        <button onClick={generate} disabled={loading||!locCol||!valCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Generating…</> : "🗺️ Generate Choropleth"}
        </button>
        {err && <div style={S.err}>{err}</div>}
      </div>
      {result && (
        <div style={S.chartCard}>
          <PlotlyChart figure={result.plotly_json} style={{height:500}} />
          <div style={{padding:"8px 12px",fontSize:12,color:"#52525b"}}>{result.rows?.toLocaleString()} rows mapped</div>
        </div>
      )}
      {!result && (
        <div style={{padding:"40px",textAlign:"center",color:"#52525b",fontSize:13}}>
          Select a location column (country names) and a value column, then click Generate.
        </div>
      )}
    </div>
  );
}

function H3Tab({ cols }) {
  const [latCol, setLatCol]   = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol]   = useState(cols.lon_hints?.[0] || "");
  const [valCol, setValCol]   = useState(cols.numeric_cols?.[0] || "");
  const [res, setRes]         = useState(4);
  const [scale, setScale]     = useState("Viridis");
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [err, setErr]         = useState(null);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
    if (cols.numeric_cols?.[0]) setValCol(cols.numeric_cols[0]);
  }, [cols]);

  const generate = async () => {
    setLoad(true); setErr(null);
    try {
      const { data } = await api.post("/maps/h3", { lat_col:latCol, lon_col:lonCol, value_col:valCol||null, resolution:res, color_scale:scale });
      setResult(data);
    } catch(e) { setErr(e.response?.data?.detail || "Failed"); }
    finally { setLoad(false); }
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude Column" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude Column" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <Sel label="Value Column (optional)" val={valCol} set={setValCol} opts={["(count only)",...cols.numeric_cols]} />
          <Sel label="Color Scale" val={scale} set={setScale} opts={COLOR_SCALES} />
          <div style={{minWidth:180}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
              <label style={S.label}>H3 Resolution</label>
              <span style={{fontSize:11,color:"#6366f1",fontWeight:600}}>{res}</span>
            </div>
            <input type="range" min={2} max={8} value={res} onChange={e=>setRes(Number(e.target.value))} style={{width:"100%",accentColor:"#6366f1"}} />
            <div style={{display:"flex",justifyContent:"space-between",fontSize:9,color:"#3f3f46",marginTop:2}}>
              <span>2 (large)</span><span>8 (fine)</span>
            </div>
          </div>
        </div>
        <button onClick={generate} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Generating…</> : "🔷 Generate H3 Map"}
        </button>
        {err && <div style={S.err}>{err}</div>}
      </div>
      {result && (
        <div style={S.chartCard}>
          <PlotlyChart figure={result.plotly_json} style={{height:500}} />
          <div style={{padding:"8px 12px",fontSize:12,color:"#52525b"}}>{result.hex_count} H3 cells at resolution {result.resolution}</div>
        </div>
      )}
    </div>
  );
}

function FlowTab({ cols }) {
  const [oLat, setOLat]   = useState(cols.lat_hints?.[0] || "");
  const [oLon, setOLon]   = useState(cols.lon_hints?.[0] || "");
  const [dLat, setDLat]   = useState("");
  const [dLon, setDLon]   = useState("");
  const [valCol, setValCol] = useState(cols.numeric_cols?.[0] || "");
  const [result, setResult] = useState(null);
  const [loading, setLoad]  = useState(false);
  const [err, setErr]       = useState(null);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setOLat(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setOLon(cols.lon_hints[0]);
    if (cols.lat_hints?.[1]) setDLat(cols.lat_hints[1]);
    if (cols.lon_hints?.[1]) setDLon(cols.lon_hints[1]);
  }, [cols]);

  const generate = async () => {
    setLoad(true); setErr(null);
    try {
      const { data } = await api.post("/maps/flow", { origin_lat:oLat, origin_lon:oLon, dest_lat:dLat, dest_lon:dLon, value_col:valCol||null });
      setResult(data);
    } catch(e) { setErr(e.response?.data?.detail || "Failed"); }
    finally { setLoad(false); }
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Origin Latitude" val={oLat} set={setOLat} opts={cols.all_cols} />
          <Sel label="Origin Longitude" val={oLon} set={setOLon} opts={cols.all_cols} />
          <Sel label="Destination Latitude" val={dLat} set={setDLat} opts={cols.all_cols} />
          <Sel label="Destination Longitude" val={dLon} set={setDLon} opts={cols.all_cols} />
          <Sel label="Flow Value (optional)" val={valCol} set={setValCol} opts={["(equal weight)",...cols.numeric_cols]} />
        </div>
        <button onClick={generate} disabled={loading||!oLat||!oLon||!dLat||!dLon} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Generating…</> : "🔀 Generate Flow Map"}
        </button>
        {err && <div style={S.err}>{err}</div>}
      </div>
      {result && (
        <div style={S.chartCard}>
          <PlotlyChart figure={result.plotly_json} style={{height:500}} />
          <div style={{padding:"8px 12px",fontSize:12,color:"#52525b"}}>{result.flows} flow lines rendered</div>
        </div>
      )}
    </div>
  );
}

function Sel({ label, val, set, opts }) {
  return (
    <div style={{flex:1,minWidth:140}}>
      <label style={S.label}>{label}</label>
      <select value={val} onChange={e=>set(e.target.value)} style={S.select}>
        {opts.map(o=><option key={o}>{o}</option>)}
      </select>
    </div>
  );
}

function Empty({ msg }) {
  return <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",background:"#09090b"}}><div style={{textAlign:"center",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.07)",borderRadius:16,padding:"48px 56px"}}><div style={{fontSize:40,marginBottom:12}}>🗺️</div><p style={{color:"#a1a1aa",fontSize:15}}>{msg}</p></div></div>;
}

const S = {
  page:      { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar:    { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:      { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:     { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:       { fontSize:11, color:"#52525b" },
  tabs:      { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:       { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  configCard:{ background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"16px", marginBottom:16 },
  chartCard: { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, overflow:"hidden" },
  label:     { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:     { padding:"8px 12px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", width:"100%", boxSizing:"border-box" },
  select:    { padding:"8px 12px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:12, outline:"none", width:"100%" },
  btn:       { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  err:       { padding:"8px 12px", borderRadius:8, background:"rgba(239,68,68,.1)", border:"1px solid rgba(239,68,68,.3)", color:"#f87171", fontSize:13, marginTop:10 },
};

// ── Satellite + Street Layer Toggle ──────────────────────────────────────────
function SatelliteTab({ cols }) {
  const [latCol, setLatCol] = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol] = useState(cols.lon_hints?.[0] || "");
  const [valCol, setValCol] = useState(cols.numeric_cols?.[0] || "");
  const [tileStyle, setTileStyle] = useState("dark");
  const [result, setResult] = useState(null);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
    if (cols.numeric_cols?.[0]) setValCol(cols.numeric_cols[0]);
  }, [cols]);

  const generate = async () => {
    setLoad(true);
    try {
      const { data: preview } = await api.get("/data/preview?n=500");
      const rows = preview.data || [];
      const points = rows.map(r => ({
        lat: parseFloat(r[latCol]),
        lon: parseFloat(r[lonCol]),
        value: valCol ? parseFloat(r[valCol]) : null,
        label: valCol ? `${valCol}: ${r[valCol]}` : `${r[latCol]}, ${r[lonCol]}`,
      })).filter(p => !isNaN(p.lat) && !isNaN(p.lon));
      setResult(points);
    } catch(e) { console.error(e); }
    setLoad(false);
  };

  const TILE_OPTIONS = [
    { id:"dark", label:"🌑 Dark" },
    { id:"street", label:"🗺️ Street" },
    { id:"satellite", label:"🛰️ Satellite" },
  ];

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <Sel label="Value (optional)" val={valCol} set={setValCol} opts={cols.numeric_cols} />
          <div style={{flex:1,minWidth:180}}>
            <label style={S.label}>Map Style</label>
            <div style={{display:"flex",gap:6,marginTop:4}}>
              {TILE_OPTIONS.map(t => (
                <button key={t.id} onClick={() => setTileStyle(t.id)}
                  style={{padding:"5px 12px",borderRadius:20,fontSize:11,cursor:"pointer",border:"1px solid",
                    background:tileStyle===t.id?"rgba(99,102,241,.2)":"transparent",
                    borderColor:tileStyle===t.id?"rgba(99,102,241,.5)":"rgba(255,255,255,.09)",
                    color:tileStyle===t.id?"#818cf8":"#71717a"}}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        <button onClick={generate} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? "Loading…" : "🛰️ Render Map"}
        </button>
      </div>
      {result && (
        <div style={S.chartCard}>
          <LeafletMap points={result} height="500px" tileStyle={tileStyle} satellite={tileStyle==="satellite"} dark={tileStyle==="dark"} />
        </div>
      )}
    </div>
  );
}

// ── Geo Clustering (Marker Cluster) ───────────────────────────────────────────
function GeoClusterTab({ cols }) {
  const [latCol, setLatCol] = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol] = useState(cols.lon_hints?.[0] || "");
  const [valCol, setValCol] = useState(cols.numeric_cols?.[0] || "");
  const [clusterSize, setClusterSize] = useState(50);
  const [result, setResult] = useState(null);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
    if (cols.numeric_cols?.[0]) setValCol(cols.numeric_cols[0]);
  }, [cols]);

  const generate = async () => {
    setLoad(true);
    try {
      const { data: preview } = await api.get("/data/preview?n=500");
      const rows = preview.data || [];
      // Client-side clustering: group nearby points
      const clusters = {};
      rows.forEach(r => {
        const lat = parseFloat(r[latCol]);
        const lon = parseFloat(r[lonCol]);
        if (isNaN(lat) || isNaN(lon)) return;
        const key = `${Math.round(lat * (100/clusterSize))}:${Math.round(lon * (100/clusterSize))}`;
        if (!clusters[key]) clusters[key] = { lat:0, lon:0, count:0, val:0 };
        clusters[key].lat += lat; clusters[key].lon += lon;
        clusters[key].count++;
        if (valCol && r[valCol]) clusters[key].val += parseFloat(r[valCol]) || 0;
      });
      const pts = Object.values(clusters);
      const fig = {
        data: [{
          type: "scattermapbox",
          lat: pts.map(p => p.lat / p.count),
          lon: pts.map(p => p.lon / p.count),
          mode: "markers",
          marker: {
            size: pts.map(p => Math.max(8, Math.min(40, p.count * 2))),
            color: pts.map(p => p.count),
            colorscale: "Viridis", opacity: 0.75,
            colorbar: { title:"Count", thickness:12 },
          },
          text: pts.map(p => `${p.count} points${valCol ? ` · val: ${(p.val/p.count).toFixed(1)}` : ""}`),
          hoverinfo: "text",
        }],
        layout: {
          mapbox: { style:"carto-darkmatter", zoom:3, center:{ lat:pts[0]?.lat/pts[0]?.count||0, lon:pts[0]?.lon/pts[0]?.count||0 } },
          height:500, margin:{l:0,r:0,t:0,b:0},
        }
      };
      setResult({ fig, clusters: pts.length, points: rows.length });
    } catch(e) { console.error(e); }
    setLoad(false);
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <Sel label="Value (optional)" val={valCol} set={setValCol} opts={cols.numeric_cols} />
          <div style={{minWidth:180}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
              <label style={S.label}>Cluster Radius</label>
              <span style={{fontSize:11,color:"#6366f1",fontWeight:600}}>{clusterSize}</span>
            </div>
            <input type="range" min={10} max={200} value={clusterSize} onChange={e=>setClusterSize(Number(e.target.value))} style={{width:"100%",accentColor:"#6366f1"}} />
          </div>
        </div>
        <button onClick={generate} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Clustering…</> : "🔵 Cluster Points"}
        </button>
      </div>
      {result && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:10,flexWrap:"wrap"}}>
            {[["Clusters",result.clusters,"#6366f1"],["Points",result.points,"#10b981"]].map(([l,v,c])=>(
              <div key={l} style={{flex:"1 1 120px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10,padding:"10px 14px"}}>
                <div style={{fontSize:20,fontWeight:700,color:c}}>{v}</div>
                <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{l}</div>
              </div>
            ))}
          </div>
          <div style={S.chartCard}><LeafletMap plotlyFig={result.fig} height="500px" /></div>
        </div>
      )}
    </div>
  );
}

// ── AI-Powered Geo Insight ────────────────────────────────────────────────────
function AIGeoInsightTab({ cols }) {
  const [latCol, setLatCol] = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol] = useState(cols.lon_hints?.[0] || "");
  const [valCol, setValCol] = useState(cols.numeric_cols?.[0] || "");
  const [insight, setInsight] = useState(null);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
    if (cols.numeric_cols?.[0]) setValCol(cols.numeric_cols[0]);
  }, [cols]);

  const generate = async () => {
    setLoad(true);
    try {
      const { data: preview } = await api.get("/data/preview?n=200");
      const rows = preview.data || [];
      const apiKey = localStorage.getItem("openai_key") || localStorage.getItem("aiml_key") || "";

      // Build geo summary
      const lats = rows.map(r => parseFloat(r[latCol])).filter(v => !isNaN(v));
      const lons = rows.map(r => parseFloat(r[lonCol])).filter(v => !isNaN(v));
      const vals = valCol ? rows.map(r => parseFloat(r[valCol])).filter(v => !isNaN(v)) : [];
      const summary = `${rows.length} geo points. Lat range: ${Math.min(...lats).toFixed(2)} to ${Math.max(...lats).toFixed(2)}. Lon range: ${Math.min(...lons).toFixed(2)} to ${Math.max(...lons).toFixed(2)}.${vals.length ? ` Value (${valCol}): mean=${(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(2)}, max=${Math.max(...vals).toFixed(2)}, min=${Math.min(...vals).toFixed(2)}.` : ""}`;

      const { data } = await api.post("/ai/chat", {
        query: `Analyze this geographic dataset: ${summary}. Identify: 1) Geographic clusters or hotspots, 2) Spatial patterns, 3) Anomalous locations, 4) Business recommendations. Be specific with coordinates.`
      }, { headers: { "X-Api-Key": apiKey } });

      // Also build a map
      const fig = {
        data: [{
          type: "scattermapbox",
          lat: lats, lon: lons,
          mode: "markers",
          marker: { size:8, color:vals.length?vals:"#6366f1", colorscale:"RdYlGn", opacity:0.8 },
          text: rows.map((r,i) => `Lat:${lats[i]?.toFixed(2)} Lon:${lons[i]?.toFixed(2)}${vals[i]!==undefined?` Val:${vals[i]?.toFixed(1)}`:""}`)
        }],
        layout: { mapbox:{style:"carto-darkmatter",zoom:3,center:{lat:lats.reduce((a,b)=>a+b,0)/lats.length||0,lon:lons.reduce((a,b)=>a+b,0)/lons.length||0}}, height:350, margin:{l:0,r:0,t:0,b:0} }
      };
      setInsight({ text: data?.data || data?.answer || "No insight", fig });
    } catch(e) { setInsight({ text: `Analysis failed: ${e.message}`, fig: null }); }
    setLoad(false);
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <Sel label="Value (optional)" val={valCol} set={setValCol} opts={cols.numeric_cols} />
        </div>
        <button onClick={generate} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Analyzing…</> : "🤖 Generate Geo Insight"}
        </button>
      </div>
      {insight && (
        <div>
          {insight.fig && <div style={{...S.chartCard,marginBottom:14}}><LeafletMap plotlyFig={insight.fig} height="350px" /></div>}
          <div style={{padding:"16px 20px",background:"rgba(99,102,241,.06)",border:"1px solid rgba(99,102,241,.2)",borderRadius:12}}>
            <div style={{fontSize:12,fontWeight:600,color:"#818cf8",marginBottom:8}}>🤖 AI Geo Analysis</div>
            <div style={{fontSize:13,color:"#a1a1aa",lineHeight:1.7,whiteSpace:"pre-wrap"}}>{insight.text}</div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Digital Twin City View ────────────────────────────────────────────────────
function DigitalTwinTab({ cols }) {
  const [latCol, setLatCol] = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol] = useState(cols.lon_hints?.[0] || "");
  const [heightCol, setHeightCol] = useState(cols.numeric_cols?.[0] || "");
  const [colorCol, setColorCol] = useState(cols.numeric_cols?.[1] || cols.numeric_cols?.[0] || "");
  const [result, setResult] = useState(null);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
    if (cols.numeric_cols?.[0]) setHeightCol(cols.numeric_cols[0]);
    if (cols.numeric_cols?.[1]) setColorCol(cols.numeric_cols[1]);
  }, [cols]);

  const generate = async () => {
    setLoad(true);
    try {
      const { data: preview } = await api.get("/data/preview?n=300");
      const rows = preview.data || [];
      const lats = rows.map(r => parseFloat(r[latCol])).filter(v => !isNaN(v));
      const lons = rows.map(r => parseFloat(r[lonCol])).filter(v => !isNaN(v));
      const heights = rows.map(r => parseFloat(r[heightCol]) || 0);
      const colors = colorCol ? rows.map(r => parseFloat(r[colorCol]) || 0) : heights;
      const maxH = Math.max(...heights) || 1;

      const fig = {
        data: [{
          type: "scattermapbox",
          lat: lats, lon: lons,
          mode: "markers",
          marker: {
            size: heights.map(h => Math.max(6, Math.min(30, (h/maxH)*25))),
            color: colors, colorscale: "RdYlGn", opacity: 0.85,
            colorbar: { title: colorCol || heightCol, thickness:12 },
          },
          text: rows.map((r,i) => `Height: ${heights[i]?.toFixed(1)}<br>Color: ${colors[i]?.toFixed(1)}`),
          hoverinfo: "text",
        }],
        layout: {
          mapbox: { style:"carto-darkmatter", zoom:10, pitch:45, bearing:0,
            center: { lat:lats.reduce((a,b)=>a+b,0)/lats.length||0, lon:lons.reduce((a,b)=>a+b,0)/lons.length||0 } },
          height:500, margin:{l:0,r:0,t:0,b:0},
        }
      };
      setResult(fig);
    } catch(e) { console.error(e); }
    setLoad(false);
  };

  return (
    <div>
      <div style={S.configCard}>
        <p style={{fontSize:12,color:"#52525b",marginBottom:12}}>Extruded building-style view — bubble size = height metric, color = performance tier.</p>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <Sel label="Height (revenue/value)" val={heightCol} set={setHeightCol} opts={cols.numeric_cols} />
          <Sel label="Color (performance)" val={colorCol} set={setColorCol} opts={cols.numeric_cols} />
        </div>
        <button onClick={generate} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Building…</> : "🏙️ Render Digital Twin"}
        </button>
      </div>
      {result && <div style={S.chartCard}><LeafletMap plotlyFig={result} height="500px" /></div>}
    </div>
  );
}

// ── Point-in-Polygon Filter ───────────────────────────────────────────────────
function PolygonFilterTab({ cols }) {
  const [latCol, setLatCol] = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol] = useState(cols.lon_hints?.[0] || "");
  const [polygon, setPolygon] = useState("40.7,-74.1\n40.7,-73.9\n40.8,-73.9\n40.8,-74.1");
  const [result, setResult] = useState(null);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
  }, [cols]);

  const filter = async () => {
    setLoad(true);
    try {
      const { data: preview } = await api.get("/data/preview?n=1000");
      const rows = preview.data || [];
      // Parse polygon vertices
      const verts = polygon.trim().split("\n").map(line => {
        const [lat, lon] = line.split(",").map(Number);
        return { lat, lon };
      }).filter(v => !isNaN(v.lat) && !isNaN(v.lon));

      // Point-in-polygon (ray casting)
      const pip = (lat, lon) => {
        let inside = false;
        for (let i = 0, j = verts.length - 1; i < verts.length; j = i++) {
          const xi = verts[i].lon, yi = verts[i].lat;
          const xj = verts[j].lon, yj = verts[j].lat;
          if (((yi > lat) !== (yj > lat)) && (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi)) inside = !inside;
        }
        return inside;
      };

      const inside = [], outside = [];
      rows.forEach(r => {
        const lat = parseFloat(r[latCol]), lon = parseFloat(r[lonCol]);
        if (!isNaN(lat) && !isNaN(lon)) {
          if (pip(lat, lon)) inside.push(r); else outside.push(r);
        }
      });

      const polyLats = [...verts.map(v=>v.lat), verts[0]?.lat];
      const polyLons = [...verts.map(v=>v.lon), verts[0]?.lon];

      const fig = {
        data: [
          { type:"scattermapbox", lat:outside.map(r=>parseFloat(r[latCol])), lon:outside.map(r=>parseFloat(r[lonCol])), mode:"markers", marker:{size:5,color:"#52525b",opacity:0.4}, name:"Outside" },
          { type:"scattermapbox", lat:inside.map(r=>parseFloat(r[latCol])), lon:inside.map(r=>parseFloat(r[lonCol])), mode:"markers", marker:{size:7,color:"#22c55e",opacity:0.9}, name:"Inside polygon" },
          { type:"scattermapbox", lat:polyLats, lon:polyLons, mode:"lines", line:{color:"#ef4444",width:2}, name:"Polygon" },
        ],
        layout: { mapbox:{style:"carto-darkmatter",zoom:8,center:{lat:verts[0]?.lat||0,lon:verts[0]?.lon||0}}, height:450, margin:{l:0,r:0,t:0,b:0}, showlegend:true }
      };
      setResult({ fig, inside:inside.length, outside:outside.length, total:rows.length });
    } catch(e) { console.error(e); }
    setLoad(false);
  };

  const downloadFiltered = () => {
    if (!result) return;
    // Re-run to get data — simplified: show count
    alert(`${result.inside} rows inside polygon. Use the dataset filter to export.`);
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <div style={{flex:2,minWidth:200}}>
            <label style={S.label}>Polygon Vertices (lat,lon per line)</label>
            <textarea value={polygon} onChange={e=>setPolygon(e.target.value)} rows={4}
              style={{...S.input,width:"100%",boxSizing:"border-box",fontFamily:"monospace",resize:"vertical"}} />
          </div>
        </div>
        <button onClick={filter} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Filtering…</> : "✂️ Filter by Polygon"}
        </button>
      </div>
      {result && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:10,flexWrap:"wrap"}}>
            {[["Inside",result.inside,"#22c55e"],["Outside",result.outside,"#52525b"],["Total",result.total,"#6366f1"]].map(([l,v,c])=>(
              <div key={l} style={{flex:"1 1 100px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10,padding:"10px 14px"}}>
                <div style={{fontSize:20,fontWeight:700,color:c}}>{v}</div>
                <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{l}</div>
              </div>
            ))}
          </div>
          <div style={S.chartCard}><LeafletMap plotlyFig={result.fig} height="450px" /></div>
        </div>
      )}
    </div>
  );
}

// ── Geo Diff — Before/After ───────────────────────────────────────────────────
function GeoDiffTab({ cols }) {
  const [latCol, setLatCol] = useState(cols.lat_hints?.[0] || "");
  const [lonCol, setLonCol] = useState(cols.lon_hints?.[0] || "");
  const [valCol, setValCol] = useState(cols.numeric_cols?.[0] || "");
  const [splitPos, setSplitPos] = useState(50);
  const [result, setResult] = useState(null);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    if (cols.lat_hints?.[0]) setLatCol(cols.lat_hints[0]);
    if (cols.lon_hints?.[0]) setLonCol(cols.lon_hints[0]);
    if (cols.numeric_cols?.[0]) setValCol(cols.numeric_cols[0]);
  }, [cols]);

  const generate = async () => {
    setLoad(true);
    try {
      const { data: preview } = await api.get("/data/preview?n=400");
      const rows = preview.data || [];
      const half = Math.floor(rows.length / 2);
      const before = rows.slice(0, half);
      const after = rows.slice(half);

      const makeFig = (pts, title, color) => ({
        data: [{
          type:"scattermapbox", lat:pts.map(r=>parseFloat(r[latCol])), lon:pts.map(r=>parseFloat(r[lonCol])),
          mode:"markers", marker:{size:7,color:valCol?pts.map(r=>parseFloat(r[valCol])||0):color,colorscale:"RdYlGn",opacity:0.8},
          text:pts.map(r=>`${valCol}: ${r[valCol]}`), hoverinfo:"text",
        }],
        layout:{ mapbox:{style:"carto-darkmatter",zoom:3,center:{lat:pts[0]?parseFloat(pts[0][latCol]):0,lon:pts[0]?parseFloat(pts[0][lonCol]):0}}, height:380, margin:{l:0,r:0,t:30,b:0}, title:{text:title,font:{size:12,color:"#a1a1aa"}} }
      });

      setResult({ before:makeFig(before,"Before (first half)","#6366f1"), after:makeFig(after,"After (second half)","#10b981"), beforeCount:before.length, afterCount:after.length });
    } catch(e) { console.error(e); }
    setLoad(false);
  };

  return (
    <div>
      <div style={S.configCard}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <Sel label="Latitude" val={latCol} set={setLatCol} opts={cols.all_cols} />
          <Sel label="Longitude" val={lonCol} set={setLonCol} opts={cols.all_cols} />
          <Sel label="Value" val={valCol} set={setValCol} opts={cols.numeric_cols} />
        </div>
        <button onClick={generate} disabled={loading||!latCol||!lonCol} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Comparing…</> : "⏱️ Compare Before/After"}
        </button>
      </div>
      {result && (
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
          <div style={S.chartCard}><LeafletMap plotlyFig={result.before} height="380px" /></div>
          <div style={S.chartCard}><LeafletMap plotlyFig={result.after} height="380px" /></div>
        </div>
      )}
    </div>
  );
}

// ── Isochrone / Radius Map ────────────────────────────────────────────────────
function IsochroneTab({ cols }) {
  const [mode, setMode]         = useState("isochrone");  // isochrone | radius
  const [lat, setLat]           = useState("40.7128");
  const [lon, setLon]           = useState("-74.0060");
  const [travelMode, setTravel] = useState("driving");
  const [minutes, setMinutes]   = useState("5,10,20");
  const [radii, setRadii]       = useState("1,5,10");
  const [label, setLabel]       = useState("Origin");
  const [osrmUrl, setOsrmUrl]   = useState("http://localhost:5000");
  const [result, setResult]     = useState(null);
  const [loading, setLoad]      = useState(false);
  const [err, setErr]           = useState(null);
  const [msg, setMsg]           = useState(null);

  // Auto-fill from dataset if lat/lon columns exist
  useEffect(() => {
    if (cols.lat_hints?.[0] && cols.lon_hints?.[0]) {
      api.get("/data/preview?n=1").then(({ data }) => {
        const row = data.data?.[0];
        if (row) {
          const latVal = parseFloat(row[cols.lat_hints[0]]);
          const lonVal = parseFloat(row[cols.lon_hints[0]]);
          if (!isNaN(latVal)) setLat(latVal.toFixed(4));
          if (!isNaN(lonVal)) setLon(lonVal.toFixed(4));
        }
      }).catch(() => {});
    }
  }, [cols]);

  const generate = async () => {
    setLoad(true); setErr(null);
    try {
      let data;
      if (mode === "isochrone") {
        const mins = minutes.split(",").map(m => parseInt(m.trim())).filter(m => !isNaN(m) && m > 0);
        const resp = await api.post("/isochrone/compute", {
          lat: parseFloat(lat), lon: parseFloat(lon),
          minutes: mins, mode: travelMode, osrm_url: osrmUrl,
        });
        data = resp.data;
      } else {
        const rads = radii.split(",").map(r => parseFloat(r.trim())).filter(r => !isNaN(r) && r > 0);
        const resp = await api.post("/isochrone/radius", {
          lat: parseFloat(lat), lon: parseFloat(lon),
          radii_km: rads, label,
        });
        data = resp.data;
      }
      setResult(data);
      if (data.method === "geometric") {
        setMsg({ ok:null, t:"Using geometric circles (OSRM/Valhalla not detected). Start OSRM for real travel-time isochrones." });
      } else {
        setMsg({ ok:true, t:`Rendered via ${data.method.toUpperCase()}` });
      }
    } catch(e) { setErr(e.response?.data?.detail || "Failed"); }
    setLoad(false);
  };

  const TRAVEL_MODES = ["driving","walking","cycling"];
  const PRESETS = [
    { name:"New York", lat:"40.7128", lon:"-74.0060" },
    { name:"London",   lat:"51.5074", lon:"-0.1278" },
    { name:"Mumbai",   lat:"19.0760", lon:"72.8777" },
    { name:"Tokyo",    lat:"35.6762", lon:"139.6503" },
  ];

  return (
    <div>
      <div style={S.configCard}>
        {/* Mode toggle */}
        <div style={{display:"flex",gap:8,marginBottom:14}}>
          {[["isochrone","⏱️ Travel Time Isochrone"],["radius","⭕ Distance Radius"]].map(([m,label]) => (
            <button key={m} onClick={() => setMode(m)}
              style={{padding:"7px 14px",borderRadius:8,border:"1px solid",fontSize:12,cursor:"pointer",
                background:mode===m?"rgba(99,102,241,.15)":"transparent",
                borderColor:mode===m?"rgba(99,102,241,.4)":"rgba(255,255,255,.09)",
                color:mode===m?"#818cf8":"#52525b"}}>
              {label}
            </button>
          ))}
        </div>

        {/* Coordinate inputs */}
        <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
          <div style={{flex:1,minWidth:120}}>
            <label style={S.label}>Latitude</label>
            <input value={lat} onChange={e=>setLat(e.target.value)} style={S.input} />
          </div>
          <div style={{flex:1,minWidth:120}}>
            <label style={S.label}>Longitude</label>
            <input value={lon} onChange={e=>setLon(e.target.value)} style={S.input} />
          </div>
          <div>
            <label style={S.label}>Quick Presets</label>
            <div style={{display:"flex",gap:4,flexWrap:"wrap",marginTop:4}}>
              {PRESETS.map(p => (
                <button key={p.name} onClick={() => { setLat(p.lat); setLon(p.lon); setLabel(p.name); }}
                  style={{padding:"4px 10px",borderRadius:20,fontSize:10,cursor:"pointer",border:"1px solid rgba(99,102,241,.2)",background:"rgba(99,102,241,.06)",color:"#818cf8"}}>
                  {p.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {mode === "isochrone" ? (
          <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
            <div style={{flex:1,minWidth:200}}>
              <label style={S.label}>Travel Time Rings (minutes, comma-separated)</label>
              <input value={minutes} onChange={e=>setMinutes(e.target.value)} placeholder="5,10,20" style={S.input} />
            </div>
            <div>
              <label style={S.label}>Travel Mode</label>
              <div style={{display:"flex",gap:6,marginTop:4}}>
                {TRAVEL_MODES.map(m => (
                  <button key={m} onClick={() => setTravel(m)}
                    style={{padding:"5px 12px",borderRadius:8,border:"1px solid",fontSize:11,cursor:"pointer",
                      background:travelMode===m?"rgba(99,102,241,.15)":"transparent",
                      borderColor:travelMode===m?"rgba(99,102,241,.4)":"rgba(255,255,255,.09)",
                      color:travelMode===m?"#818cf8":"#52525b"}}>
                    {m==="driving"?"🚗":m==="walking"?"🚶":"🚴"} {m}
                  </button>
                ))}
              </div>
            </div>
            <div style={{flex:2,minWidth:200}}>
              <label style={S.label}>OSRM URL (optional — for real routing)</label>
              <input value={osrmUrl} onChange={e=>setOsrmUrl(e.target.value)} placeholder="http://localhost:5000" style={S.input} />
              <div style={{fontSize:10,color:"#3f3f46",marginTop:3}}>
                Start OSRM: <code style={{color:"#818cf8"}}>docker run -p 5000:5000 osrm/osrm-backend</code>
              </div>
            </div>
          </div>
        ) : (
          <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
            <div style={{flex:1,minWidth:200}}>
              <label style={S.label}>Radii (km, comma-separated)</label>
              <input value={radii} onChange={e=>setRadii(e.target.value)} placeholder="1,5,10" style={S.input} />
            </div>
            <div style={{flex:1,minWidth:140}}>
              <label style={S.label}>Center Label</label>
              <input value={label} onChange={e=>setLabel(e.target.value)} placeholder="Store / Hospital…" style={S.input} />
            </div>
          </div>
        )}

        <button onClick={generate} disabled={loading||!lat||!lon} style={S.btn}>
          {loading ? <><span className="spinner" style={{width:14,height:14}}/> Computing…</> : mode==="isochrone"?"⏱️ Generate Isochrone":"⭕ Generate Radius Rings"}
        </button>
        {err && <div style={{...S.err,marginTop:10}}>{err}</div>}
      </div>

      {msg && (
        <div style={{padding:"8px 12px",borderRadius:8,border:"1px solid",fontSize:12,marginBottom:12,
          background:msg.ok===true?"rgba(16,185,129,.08)":msg.ok===null?"rgba(99,102,241,.08)":"rgba(239,68,68,.08)",
          borderColor:msg.ok===true?"rgba(16,185,129,.3)":msg.ok===null?"rgba(99,102,241,.3)":"rgba(239,68,68,.3)",
          color:msg.ok===true?"#34d399":msg.ok===null?"#818cf8":"#f87171"}}>
          {msg.t}
        </div>
      )}

      {result && (
        <div>
          {/* Stats */}
          <div style={{display:"flex",gap:10,marginBottom:12,flexWrap:"wrap"}}>
            <div style={{flex:"1 1 140px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10,padding:"10px 14px"}}>
              <div style={{fontSize:11,color:"#52525b",marginBottom:4}}>Method</div>
              <div style={{fontSize:14,fontWeight:600,color:"#818cf8"}}>{result.method?.toUpperCase()}</div>
            </div>
            {Object.entries(result.areas_km2 || {}).map(([k, v]) => (
              <div key={k} style={{flex:"1 1 120px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10,padding:"10px 14px"}}>
                <div style={{fontSize:11,color:"#52525b",marginBottom:4}}>{mode==="isochrone"?`${k} min`:`${k} km`}</div>
                <div style={{fontSize:14,fontWeight:600,color:"#6366f1"}}>{v} km²</div>
              </div>
            ))}
          </div>
          <div style={S.chartCard}>
            <PlotlyChart figure={result.plotly_json} style={{height:520}} />
          </div>
          {mode === "isochrone" && result.method === "geometric" && (
            <div style={{marginTop:12,padding:"12px 16px",borderRadius:10,background:"rgba(99,102,241,.06)",border:"1px solid rgba(99,102,241,.2)"}}>
              <div style={{fontSize:12,fontWeight:600,color:"#818cf8",marginBottom:6}}>🐳 Enable Real Routing with OSRM</div>
              <div style={{fontSize:12,color:"#71717a",lineHeight:1.7}}>
                Currently showing geometric circles. For real travel-time isochrones:<br/>
                <code style={{color:"#a5f3fc",background:"rgba(0,0,0,.3)",padding:"2px 8px",borderRadius:4,display:"inline-block",marginTop:4}}>
                  docker run -p 5000:5000 osrm/osrm-backend
                </code>
                <br/>Then set the OSRM URL above and regenerate.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
