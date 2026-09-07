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

export default function DataCatalog() {
  const [catalog, setCatalog] = useState([]);
  const [lineage, setLineage] = useState([]);
  const [loading, setLoad]    = useState(false);
  const [autoLoading, setAutoLoad] = useState(false);
  const [msg, setMsg]         = useState(null);
  const [tab, setTab]         = useState(0);
  const [search, setSearch]   = useState("");
  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState({});

  const load = useCallback(async () => {
    setLoad(true);
    try {
      const [c, l] = await Promise.all([api.get("/catalog/columns"), api.get("/catalog/lineage")]);
      setCatalog(c.data); setLineage(l.data?.lineage || []);
    } catch {}
    setLoad(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (ok, t) => { setMsg({ok,t}); setTimeout(() => setMsg(null), 3000); };

  const autoDocument = async () => {
    setAutoLoad(true);
    try {
      const apiKey = localStorage.getItem("openai_key") || localStorage.getItem("aiml_key") || "";
      const { data } = await api.post("/catalog/auto-document", null, { headers: { "X-Api-Key": apiKey } });
      await load();
      flash(true, `Auto-documented ${data.documented} columns${data.method === "rule-based" ? " (rule-based)" : ""}`);
    } catch(e) { flash(false, e.response?.data?.detail || "Failed"); }
    setAutoLoad(false);
  };

  const saveAnnotation = async () => {
    if (!editing) return;
    try {
      await api.post("/catalog/columns/annotate", { column:editing, ...editForm });
      setEditing(null); await load(); flash(true, "Annotation saved");
    } catch(e) { flash(false, e.response?.data?.detail || "Failed"); }
  };

  const qualityColor = (score) => score >= 90 ? "#22c55e" : score >= 70 ? "#f59e0b" : "#ef4444";

  const filtered = catalog.filter(c =>
    !search || c.column.toLowerCase().includes(search.toLowerCase()) ||
    c.description?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>📚</div>
        <div>
          <div style={S.title}>AI Data Catalog</div>
          <div style={S.sub}>Auto-document columns · quality scores · lineage tracking</div>
        </div>
        <button onClick={autoDocument} disabled={autoLoading} style={{...S.btn,marginLeft:"auto"}}>
          {autoLoading ? <><span className="spinner" style={{width:14,height:14}}/> Documenting…</> : "🤖 Auto-Document All"}
        </button>
      </div>

      <div style={S.tabs}>
        {["📋 Columns","📜 Lineage"].map((t,i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>
            {t}
          </button>
        ))}
      </div>

      {msg && <div style={{...S.alert, background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)", borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)", color:msg.ok?"#34d399":"#f87171", marginBottom:14}}>{msg.t}</div>}

      {tab === 0 && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:14,alignItems:"center"}}>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search columns…"
              style={{...S.input,flex:1,maxWidth:300}} />
            <span style={{fontSize:12,color:"#52525b"}}>{filtered.length} / {catalog.length} columns</span>
            <button onClick={load} disabled={loading} style={{padding:"7px 14px",borderRadius:8,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:12,cursor:"pointer"}}>↺ Refresh</button>
          </div>

          {/* Edit modal */}
          {editing && (
            <div style={{position:"fixed",inset:0,background:"rgba(0,0,0,.7)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:100}}>
              <div style={{background:"rgba(14,14,16,.95)",border:"1px solid rgba(99,102,241,.3)",borderRadius:16,padding:"28px 32px",width:480}}>
                <h3 style={{fontSize:15,fontWeight:600,color:"#f4f4f5",marginBottom:16}}>Annotate: {editing}</h3>
                {[["Description","description","text"],["Tags","tags","text"],["Owner","owner","text"]].map(([label,key,type]) => (
                  <div key={key} style={{marginBottom:12}}>
                    <label style={S.label}>{label}</label>
                    <input type={type} value={editForm[key]||""} onChange={e=>setEditForm(f=>({...f,[key]:e.target.value}))}
                      style={{...S.input,width:"100%",boxSizing:"border-box"}} />
                  </div>
                ))}
                <label style={{display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13,color:"#71717a",marginBottom:16}}>
                  <input type="checkbox" checked={editForm.pii||false} onChange={e=>setEditForm(f=>({...f,pii:e.target.checked}))} style={{accentColor:"#ef4444"}} />
                  Contains PII (Personally Identifiable Information)
                </label>
                <div style={{display:"flex",gap:8}}>
                  <button onClick={saveAnnotation} style={S.btn}>💾 Save</button>
                  <button onClick={() => setEditing(null)} style={{padding:"9px 16px",borderRadius:10,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:13,cursor:"pointer"}}>Cancel</button>
                </div>
              </div>
            </div>
          )}

          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {loading && <p style={{color:"#52525b",fontSize:13}}>Loading catalog…</p>}
            {!loading && filtered.length === 0 && <p style={{color:"#52525b",fontSize:13}}>Upload a dataset to see the catalog.</p>}
            {filtered.map(col => (
              <div key={col.column} style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"14px 16px"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                  <div style={{display:"flex",alignItems:"center",gap:8}}>
                    <span style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>{col.column}</span>
                    <span style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:"rgba(99,102,241,.1)",color:"#818cf8"}}>{col.dtype}</span>
                    {col.pii && <span style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:"rgba(239,68,68,.1)",color:"#f87171"}}>🔒 PII</span>}
                  </div>
                  <div style={{display:"flex",alignItems:"center",gap:8}}>
                    <div style={{textAlign:"right"}}>
                      <div style={{fontSize:14,fontWeight:700,color:qualityColor(col.quality_score)}}>{col.quality_score}</div>
                      <div style={{fontSize:9,color:"#52525b"}}>quality</div>
                    </div>
                    <button onClick={() => { setEditing(col.column); setEditForm({description:col.description||"",tags:col.tags||"",owner:col.owner||"",pii:col.pii||false}); }}
                      style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(99,102,241,.3)",background:"transparent",color:"#818cf8",fontSize:11,cursor:"pointer"}}>
                      ✏️ Edit
                    </button>
                  </div>
                </div>
                {/* Completeness bar */}
                <div style={{marginBottom:8}}>
                  <div style={{height:3,borderRadius:2,background:"rgba(255,255,255,.06)"}}>
                    <div style={{height:"100%",borderRadius:2,width:`${col.completeness}%`,background:qualityColor(col.completeness)}} />
                  </div>
                  <div style={{display:"flex",justifyContent:"space-between",fontSize:9,color:"#3f3f46",marginTop:2}}>
                    <span>{col.completeness}% complete · {col.nulls} nulls · {col.unique} unique</span>
                    {col.owner && <span>Owner: {col.owner}</span>}
                  </div>
                </div>
                {col.description ? (
                  <div style={{fontSize:12,color:"#a1a1aa"}}>{col.description}</div>
                ) : (
                  <div style={{fontSize:11,color:"#3f3f46",fontStyle:"italic"}}>No description — click Edit or Auto-Document</div>
                )}
                {col.tags && <div style={{marginTop:6,display:"flex",gap:4,flexWrap:"wrap"}}>{col.tags.split(",").filter(Boolean).map(t=><span key={t} style={{fontSize:9,padding:"1px 6px",borderRadius:20,background:"rgba(255,255,255,.04)",color:"#71717a"}}>{t.trim()}</span>)}</div>}
                {col.mean !== undefined && (
                  <div style={{marginTop:6,display:"flex",gap:12,fontSize:11,color:"#52525b"}}>
                    <span>mean: <span style={{color:"#a1a1aa"}}>{col.mean}</span></span>
                    <span>std: <span style={{color:"#a1a1aa"}}>{col.std}</span></span>
                  </div>
                )}
                {col.top_values && (
                  <div style={{marginTop:6,display:"flex",gap:4,flexWrap:"wrap"}}>
                    {Object.entries(col.top_values).map(([k,v]) => (
                      <span key={k} style={{fontSize:9,padding:"1px 6px",borderRadius:20,background:"rgba(255,255,255,.04)",color:"#71717a"}}>{k}: {v}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 1 && (
        <div style={{display:"flex",flexDirection:"column",gap:6}}>
          {lineage.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No lineage recorded yet.</p>}
          {lineage.map((l, i) => (
            <div key={i} style={{display:"flex",gap:12,padding:"8px 12px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:8,fontSize:12}}>
              <span style={{color:"#3f3f46",whiteSpace:"nowrap"}}>{String(l.ts||"").slice(11,19)}</span>
              <span style={{color:"#818cf8"}}>{l.action}</span>
              <span style={{color:"#a1a1aa",flex:1}}>{l.target}</span>
            </div>
          ))}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#8b5cf6,#6366f1)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  label:  { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:  { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  alert:  { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
};
