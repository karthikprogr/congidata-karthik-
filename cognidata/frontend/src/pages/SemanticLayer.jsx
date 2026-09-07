import { useState, useEffect, useCallback, Component } from "react";
import { api } from "../api/client";

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

export default function SemanticLayer() {
  const [metrics, setMetrics] = useState([]);
  const [lineage, setLineage] = useState([]);
  const [results, setResults] = useState([]);
  const [form, setForm]       = useState({ name:"", description:"", formula:"", unit:"", category:"general", tags:"" });
  const [msg, setMsg]         = useState(null);
  const [loading, setLoad]    = useState(false);
  const [tab, setTab]         = useState(0);

  const load = useCallback(async () => {
    try {
      const [m, l] = await Promise.all([api.get("/semantic/metrics"), api.get("/semantic/lineage")]);
      setMetrics(m.data); setLineage(l.data?.lineage || []);
    } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (ok, t) => { setMsg({ok,t}); setTimeout(() => setMsg(null), 3000); };

  const create = async () => {
    if (!form.name.trim() || !form.formula.trim()) return;
    setLoad(true);
    try {
      await api.post("/semantic/metrics", form);
      setForm({ name:"", description:"", formula:"", unit:"", category:"general", tags:"" });
      await load(); flash(true, "Metric defined");
    } catch(e) { flash(false, e.response?.data?.detail || "Failed"); }
    setLoad(false);
  };

  const compute = async (name) => {
    try {
      const { data } = await api.post(`/semantic/metrics/${name}/compute`);
      flash(true, `${name} = ${data.value} ${data.unit}`);
    } catch(e) { flash(false, e.response?.data?.detail || "Compute failed"); }
  };

  const computeAll = async () => {
    setLoad(true);
    try {
      const { data } = await api.post("/semantic/metrics/compute-all");
      setResults(data.results || []);
    } catch {}
    setLoad(false);
  };

  const del = async (name) => {
    try { await api.delete(`/semantic/metrics/${name}`); await load(); } catch {}
  };

  const FORMULA_EXAMPLES = [
    { label:"Total Sales", formula:"df['sales'].sum()" },
    { label:"Avg Revenue", formula:"df['revenue'].mean()" },
    { label:"Conversion Rate", formula:"df['converted'].sum() / len(df) * 100" },
    { label:"Missing %", formula:"df.isnull().mean().mean() * 100" },
  ];

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>🧮</div>
        <div>
          <div style={S.title}>Semantic Metric Layer</div>
          <div style={S.sub}>Define metrics in plain English — consistent across all agents</div>
        </div>
      </div>

      <div style={S.tabs}>
        {["📐 Define Metrics","📊 Compute","📜 Lineage"].map((t,i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>
            {t}
          </button>
        ))}
      </div>

      {msg && <div style={{...S.alert, background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)", borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)", color:msg.ok?"#34d399":"#f87171", marginBottom:14}}>{msg.t}</div>}

      {tab === 0 && (
        <div>
          <div style={S.card}>
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:12}}>Define New Metric</div>
            <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
              <div style={{flex:1,minWidth:140}}>
                <label style={S.label}>Metric Name</label>
                <input value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="total_revenue" style={S.input} />
              </div>
              <div style={{flex:1,minWidth:120}}>
                <label style={S.label}>Unit</label>
                <input value={form.unit} onChange={e=>setForm(f=>({...f,unit:e.target.value}))} placeholder="USD, %, count…" style={S.input} />
              </div>
              <div style={{flex:1,minWidth:120}}>
                <label style={S.label}>Category</label>
                <input value={form.category} onChange={e=>setForm(f=>({...f,category:e.target.value}))} placeholder="revenue, ops…" style={S.input} />
              </div>
            </div>
            <div style={{marginBottom:10}}>
              <label style={S.label}>Description</label>
              <input value={form.description} onChange={e=>setForm(f=>({...f,description:e.target.value}))} placeholder="Total revenue from completed orders" style={{...S.input,width:"100%",boxSizing:"border-box"}} />
            </div>
            <div style={{marginBottom:10}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
                <label style={S.label}>Formula (pandas expression, result in df)</label>
                <div style={{display:"flex",gap:4}}>
                  {FORMULA_EXAMPLES.map(ex => (
                    <button key={ex.label} onClick={() => setForm(f=>({...f,formula:ex.formula}))}
                      style={{padding:"2px 8px",borderRadius:6,border:"1px solid rgba(99,102,241,.2)",background:"rgba(99,102,241,.06)",color:"#818cf8",fontSize:10,cursor:"pointer"}}>
                      {ex.label}
                    </button>
                  ))}
                </div>
              </div>
              <input value={form.formula} onChange={e=>setForm(f=>({...f,formula:e.target.value}))}
                placeholder="df['sales'].sum()" style={{...S.input,width:"100%",boxSizing:"border-box",fontFamily:"monospace"}} />
            </div>
            <button onClick={create} disabled={loading||!form.name.trim()||!form.formula.trim()} style={S.btn}>+ Define Metric</button>
          </div>

          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {metrics.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No metrics defined yet.</p>}
            {metrics.map(m => (
              <div key={m.name} style={{display:"flex",alignItems:"center",gap:12,padding:"12px 16px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10}}>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>{m.name} {m.unit && <span style={{fontSize:11,color:"#52525b"}}>({m.unit})</span>}</div>
                  {m.description && <div style={{fontSize:11,color:"#71717a",marginTop:2}}>{m.description}</div>}
                  <code style={{fontSize:10,color:"#a5f3fc",background:"rgba(0,0,0,.3)",padding:"2px 6px",borderRadius:4,marginTop:4,display:"inline-block"}}>{m.formula}</code>
                </div>
                <span style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:"rgba(99,102,241,.08)",color:"#818cf8"}}>{m.category}</span>
                <button onClick={() => compute(m.name)} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(99,102,241,.3)",background:"transparent",color:"#818cf8",fontSize:11,cursor:"pointer"}}>▶ Compute</button>
                <button onClick={() => del(m.name)} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",fontSize:11,cursor:"pointer"}}>✕</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 1 && (
        <div>
          <button onClick={computeAll} disabled={loading} style={{...S.btn,marginBottom:16}}>
            {loading ? <><span className="spinner" style={{width:14,height:14}}/> Computing…</> : "▶ Compute All Metrics"}
          </button>
          <div style={{display:"flex",flexWrap:"wrap",gap:12}}>
            {results.map(r => (
              <div key={r.metric} style={{flex:"1 1 180px",background:"rgba(24,24,27,.8)",border:`1px solid ${r.status==="ok"?"rgba(99,102,241,.2)":"rgba(239,68,68,.2)"}`,borderRadius:12,padding:"16px 18px"}}>
                <div style={{fontSize:11,color:"#52525b",marginBottom:4}}>{r.metric}</div>
                <div style={{fontSize:24,fontWeight:700,color:r.status==="ok"?"#6366f1":"#f87171"}}>
                  {r.status==="ok" ? (typeof r.value === "number" ? r.value.toLocaleString(undefined,{maximumFractionDigits:2}) : r.value) : "Error"}
                </div>
                {r.unit && <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{r.unit}</div>}
                {r.error && <div style={{fontSize:10,color:"#f87171",marginTop:4}}>{r.error}</div>}
              </div>
            ))}
            {results.length === 0 && <p style={{color:"#52525b",fontSize:13}}>Click Compute All to evaluate all metrics against your dataset.</p>}
          </div>
        </div>
      )}

      {tab === 2 && (
        <div>
          <div style={{display:"flex",flexDirection:"column",gap:6}}>
            {lineage.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No lineage recorded yet.</p>}
            {lineage.map((l, i) => (
              <div key={i} style={{display:"flex",gap:12,padding:"8px 12px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:8,fontSize:12}}>
                <span style={{color:"#3f3f46",whiteSpace:"nowrap"}}>{String(l.ts||"").slice(11,19)}</span>
                <span style={{color:"#818cf8"}}>{l.action}</span>
                <span style={{color:"#a1a1aa",flex:1}}>{l.metric}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#10b981,#6366f1)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  card:   { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"16px", marginBottom:14 },
  label:  { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:  { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  alert:  { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
};
