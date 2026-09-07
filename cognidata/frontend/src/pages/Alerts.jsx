import { useState, useEffect, useCallback } from "react";
import { api } from "../api/client";

const CONDITIONS = ["gt","lt","gte","lte","eq"];
const COND_LABELS = { gt:">", lt:"<", gte:"≥", lte:"≤", eq:"=" };
const LEVEL_COLORS = { critical:"#ef4444", warning:"#f59e0b", info:"#6366f1" };

export default function Alerts() {
  const [rules, setRules]     = useState([]);
  const [history, setHistory] = useState([]);
  const [tab, setTab]         = useState(0);
  const [form, setForm]       = useState({ metric:"", condition:"gt", threshold:"", message:"", notify_email:false });
  const [msg, setMsg]         = useState(null);
  const [testData, setTestData] = useState("");
  const [testResult, setTestResult] = useState(null);

  const load = useCallback(async () => {
    try {
      const [r, h] = await Promise.all([api.get("/alerts/rules"), api.get("/alerts/history")]);
      setRules(r.data); setHistory(h.data?.alerts || []);
    } catch {}
  }, []);

  useEffect(() => { load(); }, [load]);

  const createRule = async () => {
    if (!form.metric.trim() || !form.threshold) return;
    try {
      await api.post("/alerts/rules", { ...form, threshold: parseFloat(form.threshold) });
      setForm({ metric:"", condition:"gt", threshold:"", message:"", notify_email:false });
      setMsg({ ok:true, t:"Rule created" });
      await load();
    } catch(e) { setMsg({ ok:false, t:e.response?.data?.detail || "Failed" }); }
    setTimeout(() => setMsg(null), 2500);
  };

  const deleteRule = async (id) => {
    try { await api.delete(`/alerts/rules/${id}`); await load(); } catch {}
  };

  const testAlert = async () => {
    try {
      const data = JSON.parse(testData || "{}");
      const { data: result } = await api.post("/alerts/check", data);
      setTestResult(result);
    } catch(e) { setMsg({ ok:false, t:"Invalid JSON or request failed" }); }
  };

  const clearHistory = async () => {
    try { await api.delete("/alerts/history"); setHistory([]); } catch {}
  };

  return (
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>🚨</div>
        <div>
          <div style={S.title}>KPI Threshold Alerts</div>
          <div style={S.sub}>{rules.length} rules · {history.length} triggered</div>
        </div>
      </div>

      <div style={S.tabs}>
        {["📋 Rules","📜 History","🧪 Test"].map((t,i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>
            {t}
          </button>
        ))}
      </div>

      {msg && <div style={{...S.alert, background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)", borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)", color:msg.ok?"#34d399":"#f87171", marginBottom:14}}>{msg.t}</div>}

      {tab === 0 && (
        <div>
          {/* Create rule */}
          <div style={S.card}>
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:12}}>Create Alert Rule</div>
            <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
              <div style={{flex:2,minWidth:160}}>
                <label style={S.label}>Metric Name</label>
                <input value={form.metric} onChange={e=>setForm(f=>({...f,metric:e.target.value}))} placeholder="e.g. revenue, error_rate" style={S.input} />
              </div>
              <div>
                <label style={S.label}>Condition</label>
                <select value={form.condition} onChange={e=>setForm(f=>({...f,condition:e.target.value}))} style={S.select}>
                  {CONDITIONS.map(c => <option key={c} value={c}>{COND_LABELS[c]} ({c})</option>)}
                </select>
              </div>
              <div style={{minWidth:120}}>
                <label style={S.label}>Threshold</label>
                <input type="number" value={form.threshold} onChange={e=>setForm(f=>({...f,threshold:e.target.value}))} placeholder="0" style={S.input} />
              </div>
              <div style={{flex:2,minWidth:200}}>
                <label style={S.label}>Message (optional)</label>
                <input value={form.message} onChange={e=>setForm(f=>({...f,message:e.target.value}))} placeholder="Alert message…" style={S.input} />
              </div>
            </div>
            <div style={{display:"flex",gap:12,alignItems:"center"}}>
              <label style={{display:"flex",alignItems:"center",gap:6,cursor:"pointer",fontSize:13,color:"#71717a"}}>
                <input type="checkbox" checked={form.notify_email} onChange={e=>setForm(f=>({...f,notify_email:e.target.checked}))} style={{accentColor:"#6366f1"}} />
                Email notification
              </label>
              <button onClick={createRule} disabled={!form.metric.trim()||!form.threshold} style={S.btn}>+ Create Rule</button>
            </div>
          </div>

          {/* Rules list */}
          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {rules.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No rules yet. Create one above.</p>}
            {rules.map(r => (
              <div key={r.id} style={{display:"flex",alignItems:"center",gap:12,padding:"12px 16px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:10}}>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>
                    {r.metric} <span style={{color:"#6366f1"}}>{COND_LABELS[r.condition]}</span> <span style={{color:"#f59e0b"}}>{r.threshold}</span>
                  </div>
                  {r.message && <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{r.message}</div>}
                </div>
                {r.notify_email && <span style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:"rgba(99,102,241,.12)",color:"#818cf8"}}>📧 email</span>}
                <button onClick={() => deleteRule(r.id)} style={{padding:"4px 10px",borderRadius:6,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",fontSize:11,cursor:"pointer"}}>Delete</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 1 && (
        <div>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
            <span style={{fontSize:13,color:"#71717a"}}>{history.length} alerts triggered</span>
            <button onClick={clearHistory} style={{padding:"5px 12px",borderRadius:8,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",fontSize:11,cursor:"pointer"}}>Clear History</button>
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:6}}>
            {history.length === 0 && <p style={{color:"#52525b",fontSize:13}}>No alerts triggered yet.</p>}
            {history.map((a, i) => (
              <div key={i} style={{padding:"10px 14px",borderRadius:10,background:"rgba(24,24,27,.8)",border:`1px solid ${LEVEL_COLORS[a.level] || "#52525b"}22`,display:"flex",alignItems:"center",gap:12}}>
                <span style={{fontSize:10,fontWeight:600,padding:"2px 8px",borderRadius:20,background:`${LEVEL_COLORS[a.level] || "#52525b"}18`,color:LEVEL_COLORS[a.level] || "#52525b"}}>{a.level?.toUpperCase()}</span>
                <span style={{fontSize:13,color:"#a1a1aa",flex:1}}>{a.message}</span>
                <span style={{fontSize:11,color:"#3f3f46",whiteSpace:"nowrap"}}>{String(a.ts || "").slice(11, 19)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 2 && (
        <div style={{maxWidth:520}}>
          <p style={{color:"#71717a",fontSize:13,marginBottom:12}}>Paste a JSON object with metric values to test your rules.</p>
          <textarea value={testData} onChange={e=>setTestData(e.target.value)} rows={5}
            placeholder={'{\n  "revenue": 3500,\n  "error_rate": 5.2\n}'}
            style={{...S.input,resize:"none",width:"100%",boxSizing:"border-box",fontFamily:"monospace",marginBottom:10}} />
          <button onClick={testAlert} style={S.btn}>🧪 Test Rules</button>
          {testResult && (
            <div style={{marginTop:14}}>
              <div style={{fontSize:12,color:"#52525b",marginBottom:8}}>{testResult.count} rule(s) triggered</div>
              {testResult.triggered.map((a, i) => (
                <div key={i} style={{padding:"10px 14px",borderRadius:10,background:"rgba(239,68,68,.08)",border:"1px solid rgba(239,68,68,.2)",marginBottom:6}}>
                  <div style={{fontSize:13,color:"#f87171",fontWeight:600}}>{a.message}</div>
                  <div style={{fontSize:11,color:"#52525b",marginTop:2}}>Value: {a.value} | Threshold: {a.threshold}</div>
                </div>
              ))}
              {testResult.count === 0 && <p style={{color:"#22c55e",fontSize:13}}>✅ No rules triggered — all metrics within thresholds.</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#ef4444,#f97316)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  card:   { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"16px", marginBottom:16 },
  label:  { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  input:  { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  select: { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  alert:  { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
};
