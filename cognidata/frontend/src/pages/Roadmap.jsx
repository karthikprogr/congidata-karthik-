import { useState, useEffect, Component } from "react";
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

const TABS = ["📋 Kanban","📝 List","➕ Add Feature","🤖 AI Generate","📊 Analytics"];
const PRIORITIES = ["High","Medium","Low"];
const CATEGORIES = ["Feature","Bug","Enhancement","Infrastructure","Research"];
const STATUSES = ["Planned","In Progress","Done"];
const STATUS_COLORS = { "Planned":"#6366f1", "In Progress":"#f59e0b", "Done":"#10b981" };

export default function Roadmap() {
  const [tab, setTab]         = useState(0);
  const [features, setFeatures] = useState([]);
  const [loading, setLoad]    = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiCount, setAiCount] = useState(5);
  const [form, setForm]       = useState({ title:"", description:"", priority:"Medium", category:"Feature", status:"Planned" });
  // Filters
  const [filterCat, setFilterCat]   = useState("All");
  const [filterPri, setFilterPri]   = useState("All");
  const [filterSearch, setSearch]   = useState("");
  const [filterStatus, setFilterSt] = useState("All");

  useEffect(() => { loadFeatures(); }, []);

  const loadFeatures = async () => {
    try {
      const {data} = await api.get("/roadmap/features");
      setFeatures(data);
    } catch { setFeatures([]); }
  };

  const filtered = features.filter(f => {
    if (filterCat !== "All" && f.category !== filterCat) return false;
    if (filterPri !== "All" && f.priority !== filterPri) return false;
    if (filterStatus !== "All" && f.status !== filterStatus) return false;
    if (filterSearch && !f.title.toLowerCase().includes(filterSearch.toLowerCase()) &&
        !f.description?.toLowerCase().includes(filterSearch.toLowerCase())) return false;
    return true;
  });

  const addFeature = async () => {
    if (!form.title.trim()) return;
    setLoad(true);
    try {
      await api.post("/roadmap/features", form);
      setForm({ title:"", description:"", priority:"Medium", category:"Feature", status:"Planned" });
      setShowAdd(false);
      await loadFeatures();
    } catch {} finally { setLoad(false); }
  };

  const updateStatus = async (id, status) => {
    try {
      await api.patch(`/roadmap/features/${id}`, { status });
      setFeatures(f => f.map(x => x.id===id ? {...x, status} : x));
    } catch {}
  };

  const deleteFeature = async (id) => {
    try {
      await api.delete(`/roadmap/features/${id}`);
      setFeatures(f => f.filter(x => x.id !== id));
    } catch {}
  };

  const aiGenerate = async () => {
    if (!aiPrompt.trim()) return;
    setLoad(true);
    try {
      const {data} = await api.post("/roadmap/generate", { prompt: aiPrompt, count: aiCount });
      await loadFeatures();
      setAiPrompt("");
    } catch {} finally { setLoad(false); }
  };

  const byStatus = (status) => filtered.filter(f => f.status === status);

  const FilterBar = ({ showStatus = false }) => (
    <div style={{display:"flex",gap:8,marginBottom:14,flexWrap:"wrap",alignItems:"center"}}>
      <input value={filterSearch} onChange={e=>setSearch(e.target.value)} placeholder="Search…"
        style={{padding:"6px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none",width:160}} />
      <select value={filterCat} onChange={e=>setFilterCat(e.target.value)} style={{...S.select,padding:"6px 10px",fontSize:11}}>
        <option value="All">All Categories</option>
        {CATEGORIES.map(c=><option key={c}>{c}</option>)}
      </select>
      <select value={filterPri} onChange={e=>setFilterPri(e.target.value)} style={{...S.select,padding:"6px 10px",fontSize:11}}>
        <option value="All">All Priorities</option>
        {PRIORITIES.map(p=><option key={p}>{p}</option>)}
      </select>
      {showStatus && (
        <select value={filterStatus} onChange={e=>setFilterSt(e.target.value)} style={{...S.select,padding:"6px 10px",fontSize:11}}>
          <option value="All">All Statuses</option>
          {STATUSES.map(s=><option key={s}>{s}</option>)}
        </select>
      )}
      {(filterSearch||filterCat!=="All"||filterPri!=="All"||filterStatus!=="All") && (
        <button onClick={()=>{setSearch("");setFilterCat("All");setFilterPri("All");setFilterSt("All");}}
          style={{padding:"5px 10px",borderRadius:8,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:11,cursor:"pointer"}}>
          ↺ Clear
        </button>
      )}
      <span style={{fontSize:11,color:"#52525b",marginLeft:"auto"}}>{filtered.length} / {features.length}</span>
    </div>
  );

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.headerIcon}>🗺️</div>
        <div>
          <div style={S.headerTitle}>Product Roadmap</div>
          <div style={S.headerSub}>{features.length} features · AI-powered planning</div>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} style={S.addBtn}>+ Add Feature</button>
      </div>

      {showAdd && (
        <div style={S.addForm}>
          <input placeholder="Feature title *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} style={S.input} />
          <textarea placeholder="Description" value={form.description} onChange={e=>setForm({...form,description:e.target.value})} rows={2} style={{...S.input,resize:"none"}} />
          <div style={{display:"flex",gap:10}}>
            {[["priority",PRIORITIES],["category",CATEGORIES],["status",STATUSES]].map(([key,opts])=>(
              <select key={key} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})} style={S.select}>
                {opts.map(o=><option key={o}>{o}</option>)}
              </select>
            ))}
          </div>
          <div style={{display:"flex",gap:10}}>
            <button onClick={addFeature} disabled={loading} style={S.btn}>Add</button>
            <button onClick={() => setShowAdd(false)} style={{...S.btn,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)"}}>Cancel</button>
          </div>
        </div>
      )}

      <div style={S.tabs}>
        {TABS.map((t,i) => (
          <button key={t} onClick={() => setTab(i)} style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>

      {tab === 0 && (
        <div>
          <FilterBar />
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16}}>
          {STATUSES.map(status => (
            <div key={status} style={S.column}>
              <div style={{...S.columnHeader, color:STATUS_COLORS[status]}}>
                {status} <span style={{fontSize:11,color:"#52525b"}}>({byStatus(status).length})</span>
              </div>
              {byStatus(status).map(f => (
                <div key={f.id} style={S.card}>
                  <div style={S.cardTitle}>{f.title}</div>
                  {f.description && <div style={S.cardDesc}>{f.description}</div>}
                  <div style={{display:"flex",gap:6,marginTop:8,flexWrap:"wrap"}}>
                    <span style={{...S.tag, color:f.priority==="High"?"#ef4444":f.priority==="Medium"?"#f59e0b":"#10b981"}}>{f.priority}</span>
                    <span style={S.tag}>{f.category}</span>
                    {f.tags && f.tags.split(",").filter(Boolean).map(t=>(
                      <span key={t} style={{...S.tag,color:"#818cf8",background:"rgba(99,102,241,.08)"}}>{t.trim()}</span>
                    ))}
                  </div>
                  <div style={{display:"flex",gap:6,marginTop:8}}>
                    {STATUSES.filter(s=>s!==status).map(s=>(
                      <button key={s} onClick={()=>updateStatus(f.id,s)} style={S.miniBtn}>→ {s}</button>
                    ))}
                    <button onClick={()=>deleteFeature(f.id)} style={{...S.miniBtn,color:"#f87171"}}>✕</button>
                  </div>
                </div>
              ))}
            </div>
          ))}
          </div>
        </div>
      )}

      {tab === 1 && (
        <div>
          <FilterBar showStatus />
          <div style={{display:"flex",flexDirection:"column",gap:8}}>
          {filtered.map(f => (
            <div key={f.id} style={{...S.card,display:"flex",alignItems:"center",gap:12}}>
              <div style={{flex:1}}>
                <div style={S.cardTitle}>{f.title}</div>
                {f.description && <div style={S.cardDesc}>{f.description}</div>}
              </div>
              <select value={f.status} onChange={e=>updateStatus(f.id,e.target.value)} style={{...S.select,margin:0,fontSize:11}}>
                {STATUSES.map(s=><option key={s}>{s}</option>)}
              </select>
              <span style={{...S.tag,color:STATUS_COLORS[f.status]}}>{f.status}</span>
              {f.tags && <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>{f.tags.split(",").filter(Boolean).map(t=><span key={t} style={{...S.tag,color:"#818cf8",background:"rgba(99,102,241,.08)",fontSize:9}}>{t.trim()}</span>)}</div>}
              <button onClick={()=>deleteFeature(f.id)} style={{...S.miniBtn,color:"#f87171"}}>✕</button>
            </div>
          ))}
          {filtered.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No features match filters.</p>}
          </div>
        </div>
      )}

      {tab === 2 && (
        <div style={{maxWidth:500}}>
          <h3 style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:12}}>Add New Feature</h3>
          <input placeholder="Feature title *" value={form.title} onChange={e=>setForm({...form,title:e.target.value})} style={{...S.input,width:"100%",boxSizing:"border-box",marginBottom:10}} />
          <textarea placeholder="Description" value={form.description} onChange={e=>setForm({...form,description:e.target.value})} rows={3} style={{...S.input,resize:"none",width:"100%",boxSizing:"border-box",marginBottom:10}} />
          <div style={{display:"flex",gap:10,marginBottom:10,flexWrap:"wrap"}}>
            {[["priority",PRIORITIES],["category",CATEGORIES],["status",STATUSES]].map(([key,opts])=>(
              <select key={key} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})} style={S.select}>
                {opts.map(o=><option key={o}>{o}</option>)}
              </select>
            ))}
          </div>
          <input placeholder="Tags (comma separated)" value={form.tags||""} onChange={e=>setForm({...form,tags:e.target.value})} style={{...S.input,width:"100%",boxSizing:"border-box",marginBottom:12}} />
          <button onClick={addFeature} disabled={loading||!form.title.trim()} style={S.btn}>
            {loading?<><span className="spinner" style={{width:14,height:14}}/> Adding…</>:"+ Add Feature"}
          </button>
        </div>
      )}

      {tab === 3 && (
        <div style={{maxWidth:520}}>
          <p style={{color:"#71717a",fontSize:13,marginBottom:12}}>Describe your product and let AI generate roadmap features.</p>
          <div style={{display:"flex",gap:8,flexWrap:"wrap",marginBottom:10}}>
            {["A data analytics SaaS platform","An e-commerce marketplace","A project management tool","A healthcare patient portal"].map(p=>(
              <button key={p} onClick={()=>setAiPrompt(p)} style={{padding:"5px 12px",borderRadius:20,fontSize:11,background:"rgba(99,102,241,.08)",border:"1px solid rgba(99,102,241,.2)",color:"#818cf8",cursor:"pointer"}}>{p}</button>
            ))}
          </div>
          <textarea value={aiPrompt} onChange={e=>setAiPrompt(e.target.value)} rows={3}
            placeholder="e.g. A data analytics platform for small businesses..."
            style={{...S.input,resize:"none",width:"100%",boxSizing:"border-box",marginBottom:10}} />
          <div style={{display:"flex",gap:10,alignItems:"center",marginBottom:12}}>
            <label style={{fontSize:12,color:"#71717a"}}>Generate</label>
            <input type="range" min={3} max={10} value={aiCount} onChange={e=>setAiCount(parseInt(e.target.value)||5)}
              style={{accentColor:"#6366f1",width:120}} />
            <span style={{fontSize:12,color:"#6366f1",fontWeight:600}}>{aiCount} features</span>
          </div>
          <button onClick={aiGenerate} disabled={loading||!aiPrompt.trim()} style={S.btn}>
            {loading ? <><span className="spinner" style={{width:14,height:14}} /> Generating…</> : "🤖 Generate Features"}
          </button>
        </div>
      )}

      {tab === 4 && <RoadmapAnalytics features={features} />}
    </div>
    </ErrorBoundary>
  );
}

function RoadmapAnalytics({ features }) {
  if (!features.length) return <p style={{color:"#52525b",fontSize:13,paddingTop:16}}>No features to analyze.</p>;

  const byStatus   = STATUSES.reduce((a,s) => ({...a,[s]:features.filter(f=>f.status===s).length}),{});
  const byPriority = PRIORITIES.reduce((a,p) => ({...a,[p]:features.filter(f=>f.priority===p).length}),{});
  const byCategory = CATEGORIES.reduce((a,c) => ({...a,[c]:features.filter(f=>f.category===c).length}),{});

  // Features added over time (by index as proxy for time)
  const timeData = features.map((f,i) => ({ x:i+1, y:i+1, label:`Feature ${i+1}` }));

  return (
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))",gap:16,paddingTop:16}}>
      {/* Status pie */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:12}}>By Status</div>
        {Object.entries(byStatus).map(([k,v],i)=>(
          <div key={k} style={{display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
            <div style={{width:80,fontSize:12,color:"#71717a"}}>{k}</div>
            <div style={{flex:1,height:8,borderRadius:4,background:"rgba(255,255,255,.06)"}}>
              <div style={{width:`${features.length?v/features.length*100:0}%`,height:"100%",borderRadius:4,background:["#6366f1","#f59e0b","#10b981"][i]}} />
            </div>
            <div style={{fontSize:12,color:"#a1a1aa",width:20,textAlign:"right"}}>{v}</div>
          </div>
        ))}
      </div>

      {/* Priority bar */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:12}}>By Priority</div>
        {Object.entries(byPriority).map(([k,v],i)=>(
          <div key={k} style={{display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
            <div style={{width:80,fontSize:12,color:"#71717a"}}>{k}</div>
            <div style={{flex:1,height:8,borderRadius:4,background:"rgba(255,255,255,.06)"}}>
              <div style={{width:`${features.length?v/features.length*100:0}%`,height:"100%",borderRadius:4,background:["#ef4444","#f59e0b","#10b981"][i]}} />
            </div>
            <div style={{fontSize:12,color:"#a1a1aa",width:20,textAlign:"right"}}>{v}</div>
          </div>
        ))}
      </div>

      {/* Category horizontal bar */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:12}}>By Category</div>
        {Object.entries(byCategory).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).map(([k,v],i)=>(
          <div key={k} style={{display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
            <div style={{width:100,fontSize:11,color:"#71717a",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{k}</div>
            <div style={{flex:1,height:8,borderRadius:4,background:"rgba(255,255,255,.06)"}}>
              <div style={{width:`${features.length?v/features.length*100:0}%`,height:"100%",borderRadius:4,background:`hsl(${i*60+200},70%,60%)`}} />
            </div>
            <div style={{fontSize:12,color:"#a1a1aa",width:20,textAlign:"right"}}>{v}</div>
          </div>
        ))}
      </div>

      {/* Features added over time — area chart */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:16,gridColumn:"1/-1"}}>
        <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:12}}>Features Added Over Time</div>
        <div style={{position:"relative",height:80}}>
          <svg width="100%" height="80" viewBox={`0 0 ${Math.max(features.length,1)} 80`} preserveAspectRatio="none">
            <defs>
              <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity="0.4"/>
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0.02"/>
              </linearGradient>
            </defs>
            {features.length > 1 && (
              <>
                <path
                  d={`M 0 80 ${features.map((_,i)=>`L ${i} ${80-(i+1)/features.length*70}`).join(" ")} L ${features.length-1} 80 Z`}
                  fill="url(#areaGrad)"
                />
                <path
                  d={`M 0 80 ${features.map((_,i)=>`L ${i} ${80-(i+1)/features.length*70}`).join(" ")}`}
                  fill="none" stroke="#6366f1" strokeWidth="0.5"
                />
              </>
            )}
          </svg>
          <div style={{position:"absolute",bottom:0,left:0,right:0,display:"flex",justifyContent:"space-between",fontSize:10,color:"#3f3f46"}}>
            <span>Feature 1</span>
            <span style={{color:"#6366f1",fontWeight:600}}>{features.length} total</span>
            <span>Feature {features.length}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

const S = {
  page:        { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  header:      { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  headerIcon:  { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  headerTitle: { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  headerSub:   { fontSize:11, color:"#52525b" },
  addBtn:      { marginLeft:"auto", padding:"8px 16px", borderRadius:8, border:"1px solid rgba(99,102,241,.3)", background:"rgba(99,102,241,.08)", color:"#818cf8", cursor:"pointer", fontSize:13, fontWeight:500 },
  addForm:     { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:16, marginBottom:16, display:"flex", flexDirection:"column", gap:10 },
  tabs:        { display:"flex", gap:4, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)" },
  tab:         { padding:"8px 14px", background:"transparent", border:"none", fontSize:13, fontWeight:500, cursor:"pointer" },
  column:      { background:"rgba(24,24,27,.6)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:14, display:"flex", flexDirection:"column", gap:10, minHeight:200 },
  columnHeader:{ fontSize:13, fontWeight:700, marginBottom:4 },
  card:        { background:"rgba(9,9,11,.6)", border:"1px solid rgba(255,255,255,.06)", borderRadius:10, padding:12 },
  cardTitle:   { fontSize:13, fontWeight:500, color:"#f4f4f5" },
  cardDesc:    { fontSize:11, color:"#52525b", marginTop:4, lineHeight:1.5 },
  tag:         { fontSize:10, padding:"2px 8px", borderRadius:20, background:"rgba(255,255,255,.05)", color:"#71717a" },
  miniBtn:     { fontSize:10, padding:"3px 8px", borderRadius:6, background:"transparent", border:"1px solid rgba(255,255,255,.08)", color:"#52525b", cursor:"pointer" },
  input:       { padding:"10px 14px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  select:      { padding:"8px 12px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:12, outline:"none" },
  btn:         { padding:"10px 18px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
};
