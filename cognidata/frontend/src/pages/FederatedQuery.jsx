import { useState, useEffect, useCallback, Component } from "react";
import { api } from "../api/client";
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

const DB_TYPES = ["postgres","mysql","sqlite","snowflake"];
const DB_ICONS = { postgres:"🐘", mysql:"🐬", sqlite:"📁", snowflake:"❄️" };

export default function FederatedQuery() {
  const [tab, setTab]         = useState(0);
  const [connections, setConns] = useState([]);
  const [form, setForm]       = useState({ name:"", type:"postgres", host:"localhost", port:5432, database:"", username:"", password:"", path:"" });
  const [selected, setSelected] = useState("");
  const [schema, setSchema]   = useState(null);
  const [query, setQuery]     = useState("SELECT * FROM ");
  const [nlQuery, setNlQuery] = useState("");
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [msg, setMsg]         = useState(null);

  const load = useCallback(async () => {
    try { setConns((await api.get("/federated/connections")).data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (ok, t) => { setMsg({ok,t}); setTimeout(() => setMsg(null), 3000); };

  const addConn = async () => {
    setLoad(true);
    try {
      await api.post("/federated/connections", form);
      setForm({ name:"", type:"postgres", host:"localhost", port:5432, database:"", username:"", password:"", path:"" });
      await load(); flash(true, "Connection saved");
    } catch(e) { flash(false, e.response?.data?.detail || "Failed"); }
    setLoad(false);
  };

  const testConn = async (name) => {
    try {
      const { data } = await api.post(`/federated/connections/${name}/test`);
      flash(data.success, data.message);
    } catch(e) { flash(false, e.response?.data?.detail || "Test failed"); }
  };

  const deleteConn = async (name) => {
    try { await api.delete(`/federated/connections/${name}`); await load(); } catch {}
  };

  const loadSchema = async (name) => {
    setSelected(name);
    try { setSchema((await api.post(`/federated/connections/${name}/schema`)).data); } catch {}
  };

  const runQuery = async () => {
    setLoad(true);
    try {
      const { data } = await api.post("/federated/query", { connection_name:selected, query, limit:500 });
      setResult(data); flash(true, `${data.rows} rows loaded into dataset`);
    } catch(e) { flash(false, e.response?.data?.detail || "Query failed"); }
    setLoad(false);
  };

  const runNL = async () => {
    setLoad(true);
    try {
      const apiKey = localStorage.getItem("openai_key") || localStorage.getItem("aiml_key") || "";
      const { data } = await api.post("/federated/nl-query", { connection_name:selected, question:nlQuery, api_key:apiKey });
      setResult(data); setQuery(data.sql || query);
      flash(true, `${data.rows} rows returned`);
    } catch(e) { flash(false, e.response?.data?.detail || "NL query failed"); }
    setLoad(false);
  };

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>🔌</div>
        <div>
          <div style={S.title}>Federated Query</div>
          <div style={S.sub}>Query remote databases without uploading data</div>
        </div>
      </div>

      <div style={S.tabs}>
        {["🔌 Connections","🗄️ Query Editor","📋 Schema"].map((t,i) => (
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
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:12}}>Add Connection</div>
            <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
              <div style={{flex:1,minWidth:140}}>
                <label style={S.label}>Name</label>
                <input value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="my-db" style={S.input} />
              </div>
              <div>
                <label style={S.label}>Type</label>
                <select value={form.type} onChange={e=>setForm(f=>({...f,type:e.target.value}))} style={S.select}>
                  {DB_TYPES.map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              {form.type !== "sqlite" ? (
                <>
                  <div style={{flex:2,minWidth:160}}>
                    <label style={S.label}>Host</label>
                    <input value={form.host} onChange={e=>setForm(f=>({...f,host:e.target.value}))} style={S.input} />
                  </div>
                  <div style={{minWidth:80}}>
                    <label style={S.label}>Port</label>
                    <input type="number" value={form.port} onChange={e=>setForm(f=>({...f,port:parseInt(e.target.value)||5432}))} style={S.input} />
                  </div>
                  <div style={{flex:1,minWidth:120}}>
                    <label style={S.label}>Database</label>
                    <input value={form.database} onChange={e=>setForm(f=>({...f,database:e.target.value}))} style={S.input} />
                  </div>
                  <div style={{flex:1,minWidth:120}}>
                    <label style={S.label}>Username</label>
                    <input value={form.username} onChange={e=>setForm(f=>({...f,username:e.target.value}))} style={S.input} />
                  </div>
                  <div style={{flex:1,minWidth:120}}>
                    <label style={S.label}>Password</label>
                    <input type="password" value={form.password} onChange={e=>setForm(f=>({...f,password:e.target.value}))} style={S.input} />
                  </div>
                </>
              ) : (
                <div style={{flex:3,minWidth:200}}>
                  <label style={S.label}>File Path</label>
                  <input value={form.path} onChange={e=>setForm(f=>({...f,path:e.target.value}))} placeholder="/path/to/db.sqlite" style={S.input} />
                </div>
              )}
            </div>
            <button onClick={addConn} disabled={loading||!form.name.trim()} style={S.btn}>+ Add Connection</button>
          </div>

          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {connections.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No connections yet.</p>}
            {connections.map(c => (
              <div key={c.name} style={{display:"flex",alignItems:"center",gap:12,padding:"12px 16px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10}}>
                <span style={{fontSize:18}}>{DB_ICONS[c.type] || "🗄️"}</span>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>{c.name}</div>
                  <div style={{fontSize:11,color:"#52525b"}}>{c.type} · {c.host || c.path} · {c.database}</div>
                </div>
                <button onClick={() => testConn(c.name)} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(99,102,241,.3)",background:"transparent",color:"#818cf8",fontSize:11,cursor:"pointer"}}>Test</button>
                <button onClick={() => { loadSchema(c.name); setTab(2); }} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:11,cursor:"pointer"}}>Schema</button>
                <button onClick={() => { setSelected(c.name); setTab(1); }} style={S.btn}>Query</button>
                <button onClick={() => deleteConn(c.name)} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",fontSize:11,cursor:"pointer"}}>✕</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 1 && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:12,alignItems:"center"}}>
            <label style={S.label}>Connection:</label>
            <select value={selected} onChange={e=>setSelected(e.target.value)} style={S.select}>
              <option value="">-- select --</option>
              {connections.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
          {/* NL Query */}
          <div style={S.card}>
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:8}}>Natural Language Query</div>
            <div style={{display:"flex",gap:8}}>
              <input value={nlQuery} onChange={e=>setNlQuery(e.target.value)} placeholder="Show me top 10 customers by revenue…"
                style={{...S.input,flex:1}} />
              <button onClick={runNL} disabled={loading||!selected||!nlQuery.trim()} style={S.btn}>
                {loading ? <span className="spinner" style={{width:14,height:14}}/> : "🤖 Ask"}
              </button>
            </div>
          </div>
          {/* SQL Editor */}
          <div style={S.card}>
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:8}}>SQL Editor</div>
            <textarea value={query} onChange={e=>setQuery(e.target.value)} rows={6}
              style={{...S.input,width:"100%",boxSizing:"border-box",fontFamily:"monospace",resize:"vertical",marginBottom:10}} />
            <button onClick={runQuery} disabled={loading||!selected||!query.trim()} style={S.btn}>
              {loading ? <><span className="spinner" style={{width:14,height:14}}/> Running…</> : "▶ Run Query"}
            </button>
          </div>
          {result && (
            <div style={S.card}>
              <div style={{fontSize:12,color:"#52525b",marginBottom:8}}>{result.rows} rows · {result.columns} columns · loaded into dataset</div>
              <Table data={result.data?.slice(0,20) || []} />
            </div>
          )}
        </div>
      )}

      {tab === 2 && (
        <div>
          {!schema ? (
            <p style={{color:"#52525b",fontSize:13}}>Select a connection and click Schema to view its tables.</p>
          ) : (
            <div>
              <div style={{fontSize:12,color:"#52525b",marginBottom:12}}>{schema.count} tables</div>
              {Object.entries(schema.tables || {}).map(([table, cols]) => (
                <div key={table} style={{...S.card,marginBottom:10}}>
                  <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5",marginBottom:8}}>📋 {table}</div>
                  <div style={{display:"flex",flexWrap:"wrap",gap:6}}>
                    {cols.map(c => (
                      <span key={c.name} style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:"rgba(99,102,241,.08)",color:"#818cf8"}}>
                        {c.name} <span style={{color:"#52525b"}}>({c.type})</span>
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#0ea5e9,#6366f1)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  card:   { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"16px", marginBottom:14 },
  label:  { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:  { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  select: { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  alert:  { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
};
