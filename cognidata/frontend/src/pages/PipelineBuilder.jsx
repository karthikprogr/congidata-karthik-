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

const STEP_COLORS = { clean:"#22c55e", transform:"#6366f1", aggregate:"#f59e0b", filter:"#0ea5e9", chart:"#8b5cf6", export:"#ec4899" };
const PRESETS = [
  "Clean, aggregate by category, and export as CSV",
  "Remove duplicates, fill missing values, and generate charts",
  "Filter outliers, normalize numeric columns, and cluster",
  "Group by region, calculate totals, and create a bar chart",
];

export default function PipelineBuilder() {
  const [pipelines, setPipelines] = useState([]);
  const [prompt, setPrompt]       = useState("");
  const [loading, setLoad]        = useState(false);
  const [running, setRunning]     = useState({});
  const [stepResults, setStepResults] = useState({});
  const [msg, setMsg]             = useState(null);

  const load = useCallback(async () => {
    try { setPipelines((await api.get("/pipeline/pipelines")).data); } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const flash = (ok, t) => { setMsg({ok,t}); setTimeout(() => setMsg(null), 3000); };

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoad(true);
    try {
      const apiKey = localStorage.getItem("openai_key") || localStorage.getItem("aiml_key") || "";
      const { data } = await api.post("/pipeline/generate", { description:prompt, api_key:apiKey });
      await load();
      setPrompt("");
      flash(true, `Pipeline "${data.description}" created with ${data.steps?.length} steps`);
    } catch(e) { flash(false, e.response?.data?.detail || "Generation failed"); }
    setLoad(false);
  };

  const runStep = async (pipelineId, stepIndex, stepName) => {
    const key = `${pipelineId}-${stepIndex}`;
    setRunning(r => ({...r, [key]: true}));
    try {
      const { data } = await api.post("/pipeline/run-step", { pipeline_id:pipelineId, step_index:stepIndex });
      setStepResults(r => ({...r, [key]: data}));
      if (data.status === "ok") flash(true, `Step "${stepName}" completed — ${data.rows || ""} rows`);
      else flash(false, `Step "${stepName}" failed: ${data.error}`);
    } catch(e) { flash(false, e.response?.data?.detail || "Step failed"); }
    setRunning(r => ({...r, [key]: false}));
  };

  const deletePipeline = async (id) => {
    try { await api.delete(`/pipeline/pipelines/${id}`); await load(); } catch {}
  };

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>⚙️</div>
        <div>
          <div style={S.title}>Agentic Pipeline Builder</div>
          <div style={S.sub}>Describe your ETL in plain English — AI generates executable steps</div>
        </div>
      </div>

      {msg && <div style={{...S.alert, background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)", borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)", color:msg.ok?"#34d399":"#f87171", marginBottom:14}}>{msg.t}</div>}

      {/* Generator */}
      <div style={S.card}>
        <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10}}>Describe Your Pipeline</div>
        <div style={{display:"flex",gap:6,flexWrap:"wrap",marginBottom:10}}>
          {PRESETS.map(p => (
            <button key={p} onClick={() => setPrompt(p)}
              style={{padding:"4px 10px",borderRadius:20,fontSize:11,background:"rgba(99,102,241,.08)",border:"1px solid rgba(99,102,241,.2)",color:"#818cf8",cursor:"pointer"}}>
              {p.slice(0,40)}…
            </button>
          ))}
        </div>
        <div style={{display:"flex",gap:8}}>
          <input value={prompt} onChange={e=>setPrompt(e.target.value)}
            placeholder="e.g. Clean the data, group by country, and export as CSV"
            style={{...S.input,flex:1}} />
          <button onClick={generate} disabled={loading||!prompt.trim()} style={S.btn}>
            {loading ? <><span className="spinner" style={{width:14,height:14}}/> Generating…</> : "🤖 Generate Pipeline"}
          </button>
        </div>
      </div>

      {/* Pipelines */}
      <div style={{display:"flex",flexDirection:"column",gap:16}}>
        {pipelines.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No pipelines yet. Describe one above.</p>}
        {[...pipelines].reverse().map(p => (
          <div key={p.id} style={S.card}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
              <div>
                <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>{p.description}</div>
                <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{p.steps?.length} steps · {p.status}</div>
              </div>
              <button onClick={() => deletePipeline(p.id)} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",fontSize:11,cursor:"pointer"}}>Delete</button>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:8}}>
              {(p.steps || []).map((step, i) => {
                const key = `${p.id}-${i}`;
                const res = stepResults[key];
                const isRunning = running[key];
                return (
                  <div key={i} style={{display:"flex",gap:12,padding:"10px 14px",background:"rgba(9,9,11,.6)",border:`1px solid ${STEP_COLORS[step.type]||"#52525b"}22`,borderRadius:10,alignItems:"flex-start"}}>
                    <div style={{width:24,height:24,borderRadius:6,background:`${STEP_COLORS[step.type]||"#52525b"}22`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:STEP_COLORS[step.type]||"#52525b",flexShrink:0,marginTop:2}}>
                      {i+1}
                    </div>
                    <div style={{flex:1}}>
                      <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
                        <span style={{fontSize:12,fontWeight:600,color:"#f4f4f5"}}>{step.name}</span>
                        <span style={{fontSize:9,padding:"1px 6px",borderRadius:20,background:`${STEP_COLORS[step.type]||"#52525b"}18`,color:STEP_COLORS[step.type]||"#52525b"}}>{step.type}</span>
                      </div>
                      <div style={{fontSize:11,color:"#71717a",marginBottom:6}}>{step.description}</div>
                      <code style={{fontSize:10,color:"#a5f3fc",background:"rgba(0,0,0,.3)",padding:"4px 8px",borderRadius:6,display:"block",whiteSpace:"pre-wrap",wordBreak:"break-all"}}>{step.code}</code>
                      {res && (
                        <div style={{marginTop:8,padding:"6px 10px",borderRadius:8,background:res.status==="ok"?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)",border:`1px solid ${res.status==="ok"?"rgba(16,185,129,.2)":"rgba(239,68,68,.2)"}`,fontSize:11,color:res.status==="ok"?"#34d399":"#f87171"}}>
                          {res.status==="ok" ? `✅ ${res.rows ? `${res.rows} rows` : res.result || "Done"}` : `❌ ${res.error}`}
                        </div>
                      )}
                    </div>
                    <button onClick={() => runStep(p.id, i, step.name)} disabled={isRunning}
                      style={{padding:"5px 12px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:11,fontWeight:600,cursor:"pointer",flexShrink:0,opacity:isRunning?0.5:1}}>
                      {isRunning ? <span className="spinner" style={{width:12,height:12}} /> : "▶ Run"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
    </ErrorBoundary>
  );
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#f59e0b,#ef4444)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  card:   { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"16px", marginBottom:14 },
  label:  { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:  { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  alert:  { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
};
