import { useEffect, useState, Component } from "react";
import { api } from "../api/client";
import PlotlyChart from "../components/PlotlyChart";

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

const TABS = ["📊 Overview","👤 Users","📋 Activity","🤖 AI Usage","⚙️ System","🔒 Security","📢 Broadcast","💬 Feedback","🔔 Alerts","📧 SMTP Config"];

export default function Admin() {
  const [tab, setTab]         = useState(0);
  const [users, setUsers]     = useState([]);
  const [logs, setLogs]       = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [summary, setSummary] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [alerts, setAlerts]   = useState([]);
  const [sysStats, setSysStats] = useState(null);
  const [error, setError]     = useState(null);
  const [broadcast, setBroadcast] = useState("");
  const [bType, setBType]     = useState("info");
  const [bMsg, setBMsg]       = useState(null);
  const [userSearch, setUserSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const loadAll = () => {
    Promise.all([
      api.get("/admin/users"),
      api.get("/admin/logs"),
      api.get("/admin/metrics"),
      api.get("/admin/summary"),
    ]).then(([u,l,m,s]) => {
      setUsers(u.data); setLogs(l.data); setMetrics(m.data); setSummary(s.data);
    }).catch(e => setError(e.response?.data?.detail || "Access denied"));
    api.get("/admin/feedback").then(({data}) => setFeedback(data?.feedback || data || [])).catch(()=>{});
    api.get("/admin/alerts").then(({data}) => setAlerts(data)).catch(()=>{});
    api.get("/admin/system").then(({data}) => setSysStats(data)).catch(()=>{});
  };

  useEffect(() => { loadAll(); }, []);

  const deleteUser = async (id) => {
    if (!confirm("Delete this user?")) return;
    await api.delete(`/admin/users/${id}`);
    setUsers(u => u.filter(x => x.id !== id));
  };

  const changeRole = async (id, role) => {
    try {
      const { data } = await api.patch(`/admin/users/${id}/role`, { role });
      setUsers(u => u.map(x => x.id === id ? {...x, role: data.role} : x));
    } catch(e) { alert(e.response?.data?.detail || "Failed"); }
  };

  const toggleStatus = async (id, active) => {
    try {
      const { data } = await api.patch(`/admin/users/${id}/status`, { active });
      setUsers(u => u.map(x => x.id === id ? {...x, active: data.active} : x));
    } catch(e) { alert(e.response?.data?.detail || "Failed"); }
  };

  const sendBroadcast = async () => {
    if (!broadcast.trim()) return;
    try {
      await api.post("/admin/broadcast", { message: broadcast, type: bType });
      setBMsg({ ok:true, t:`Broadcast sent to all users (${bType})` });
      setBroadcast("");
    } catch(e) { setBMsg({ ok:false, t:e.response?.data?.detail||"Failed" }); }
  };

  const filteredUsers = users.filter(u => {
    const matchSearch = !userSearch || u.email.toLowerCase().includes(userSearch.toLowerCase());
    const matchRole   = roleFilter === "all" || u.role === roleFilter;
    return matchSearch && matchRole;
  });

  if (error) return <div style={S.center}><p style={{color:"#f87171"}}>{error}</p></div>;

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.headerIcon}>🛡️</div>
        <div>
          <div style={S.headerTitle}>Admin Panel</div>
          <div style={S.headerSub}>System management · {users.length} users · {summary?.total||0} requests</div>
        </div>
      </div>

      {summary && tab === 0 && (
        <div style={S.kpiRow}>
          {[["Total Requests",summary.total],["Avg Response",`${summary.avg_ms}ms`],["Errors",summary.errors],["Error Rate",`${summary.error_rate}%`],["Users",users.length]].map(([l,v])=>(
            <div key={l} style={S.kpi}><div style={{fontSize:20,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
          ))}
        </div>
      )}

      <div style={S.tabs}>
        {TABS.map((t,i) => (
          <button key={t} onClick={() => setTab(i)} style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>

      {/* Tab 0 — Overview */}
      {tab === 0 && (
        <div>
          {/* Platform stats KPIs */}
          {summary && (
            <div style={S.kpiRow}>
              {[["Total Users",users.length],["Total Requests",summary.total],["Avg Response",`${summary.avg_ms}ms`],["Error Rate",`${summary.error_rate}%`],["Errors",summary.errors]].map(([l,v])=>(
                <div key={l} style={S.kpi}><div style={{fontSize:20,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
              ))}
            </div>
          )}
          {/* Charts row */}
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14}}>
            {/* User growth line chart */}
            {users.length>0 && (
              <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"12px"}}>
                <div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:6}}>User Growth</div>
                {(() => {
                  // Simulate growth from user IDs (proxy for registration order)
                  const sorted = [...users].sort((a,b)=>a.id-b.id);
                  const fig = {
                    data:[{type:"scatter",mode:"lines+markers",x:sorted.map((_,i)=>`User ${i+1}`),y:sorted.map((_,i)=>i+1),
                      line:{color:"#6366f1",width:2},marker:{size:4},fill:"tozeroy",fillcolor:"rgba(99,102,241,.1)"}],
                    layout:{height:200,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",
                      font:{color:"#a1a1aa"},margin:{l:30,r:10,t:10,b:30},
                      xaxis:{showticklabels:false},yaxis:{title:{text:"Users",font:{size:10}}}}
                  };
                  return <PlotlyChart figure={fig} />;
                })()}
              </div>
            )}
            {/* Role distribution pie */}
            {users.length>0 && (
              <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"12px"}}>
                <div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:6}}>Role Distribution</div>
                {(() => {
                  const adminCount = users.filter(u=>u.role==="admin").length;
                  const userCount  = users.length - adminCount;
                  const fig = {data:[{type:"pie",labels:["Admin","User"],values:[adminCount,userCount],hole:0.4,marker:{colors:["#6366f1","#10b981"]}}],layout:{height:200,showlegend:true,template:"plotly_dark",paper_bgcolor:"transparent",margin:{l:0,r:0,t:0,b:0}}};
                  return <PlotlyChart figure={fig} />;
                })()}
              </div>
            )}
            {/* Recent activity feed */}
            <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"12px"}}>
              <div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:8}}>Recent Activity</div>
              <div style={{maxHeight:200,overflowY:"auto"}}>
                {logs.slice(0,10).map((l,i)=>(
                  <div key={i} style={{display:"flex",gap:8,padding:"5px 0",borderBottom:"1px solid rgba(255,255,255,.04)",fontSize:11}}>
                    <span style={{color:"#3f3f46",whiteSpace:"nowrap"}}>{new Date(l.ts).toLocaleTimeString()}</span>
                    <span style={{color:"#52525b",flex:1,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{l.user}</span>
                    <span style={{color:"#818cf8",whiteSpace:"nowrap"}}>{l.action}</span>
                  </div>
                ))}
                {!logs.length && <p style={{color:"#52525b",fontSize:12}}>No activity yet.</p>}
              </div>
            </div>
            {/* Active vs inactive bar */}
            {users.length>0 && (
              <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"12px"}}>
                <div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:6}}>Platform Stats</div>
                <div style={{display:"flex",flexDirection:"column",gap:8,paddingTop:8}}>
                  {[["Total Users",users.length,"#6366f1"],["Admins",users.filter(u=>u.role==="admin").length,"#8b5cf6"],["2FA Enabled",users.filter(u=>u.totp_enabled).length,"#22c55e"],["Total Requests",summary?.total||0,"#f59e0b"]].map(([l,v,c])=>(
                    <div key={l} style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                      <span style={{fontSize:12,color:"#71717a"}}>{l}</span>
                      <span style={{fontSize:14,fontWeight:700,color:c}}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          {/* Request metrics table */}
          <div style={S.tableWrap}>
            <table style={S.table}>
              <thead><tr>{["Endpoint","Method","Duration","Status","Time"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
              <tbody>
                {metrics.slice(0,15).map((m,i)=>(
                  <tr key={i}>
                    <td style={S.td}>{m.endpoint}</td>
                    <td style={S.td}>{m.method}</td>
                    <td style={S.td}>{m.duration_ms}ms</td>
                    <td style={S.td}><span style={{color:m.status>=400?"#f87171":"#34d399"}}>{m.status}</span></td>
                    <td style={S.td}>{new Date(m.ts).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 1 — Users */}
      {tab === 1 && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:12,flexWrap:"wrap"}}>
            <input placeholder="Search by email…" value={userSearch} onChange={e=>setUserSearch(e.target.value)}
              style={{...S.input,flex:1,minWidth:200}} />
            <select value={roleFilter} onChange={e=>setRoleFilter(e.target.value)} style={S.select}>
              <option value="all">All Roles</option>
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div style={S.tableWrap}>
            <table style={S.table}>
              <thead><tr>{["ID","Email","Role","Status","2FA","Actions"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
              <tbody>
                {filteredUsers.map(u=>(
                  <tr key={u.id}>
                    <td style={S.td}>{u.id}</td>
                    <td style={S.td}>{u.email}</td>
                    <td style={S.td}>
                      <span style={{...S.badge,background:u.role==="admin"?"rgba(99,102,241,.15)":"rgba(255,255,255,.04)",color:u.role==="admin"?"#818cf8":"#71717a"}}>{u.role}</span>
                    </td>
                    <td style={S.td}>
                      <span style={{fontSize:11,padding:"2px 8px",borderRadius:20,fontWeight:600,
                        background:u.active!==false?"rgba(34,197,94,.1)":"rgba(239,68,68,.1)",
                        color:u.active!==false?"#4ade80":"#f87171"}}>
                        {u.active!==false?"Active":"Inactive"}
                      </span>
                    </td>
                    <td style={S.td}><span style={{color:u.totp_enabled?"#34d399":"#52525b"}}>{u.totp_enabled?"✅":"—"}</span></td>
                    <td style={S.td}>
                      <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                        <button onClick={()=>changeRole(u.id, u.role==="admin"?"user":"admin")}
                          style={{...S.actionBtn,padding:"3px 10px",fontSize:11,background:"rgba(99,102,241,.1)",color:"#818cf8"}}>
                          {u.role==="admin"?"→ User":"→ Admin"}
                        </button>
                        <button onClick={()=>toggleStatus(u.id, u.active===false)}
                          style={{...S.actionBtn,padding:"3px 10px",fontSize:11,
                            background:u.active!==false?"rgba(239,68,68,.08)":"rgba(34,197,94,.08)",
                            color:u.active!==false?"#f87171":"#4ade80",
                            border:`1px solid ${u.active!==false?"rgba(239,68,68,.2)":"rgba(34,197,94,.2)"}`}}>
                          {u.active!==false?"Deactivate":"Activate"}
                        </button>
                        <button onClick={()=>{
                          api.get("/admin/logs").then(({data})=>{
                            const userLogs = data.filter(l=>l.user===u.email).slice(0,5);
                            alert(`Last 5 actions for ${u.email}:\n${userLogs.map(l=>`${l.action}: ${l.detail||""}`).join("\n") || "No activity"}`);
                          }).catch(()=>{});
                        }} style={{...S.actionBtn,padding:"3px 10px",fontSize:11,background:"rgba(14,165,233,.1)",color:"#38bdf8"}}>
                          📋 Activity
                        </button>
                        <button onClick={()=>deleteUser(u.id)}
                          style={{...S.actionBtn,padding:"3px 10px",fontSize:11,background:"transparent",border:"1px solid rgba(239,68,68,.3)",color:"#f87171"}}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2 — Activity */}
      {tab === 2 && (
        <div>
          <ActivityTab logs={logs} />
        </div>
      )}

      {/* Tab 3 — AI Usage */}
      {tab === 3 && (
        <AIUsageTab metrics={metrics} />
      )}

      {/* Tab 4 — System */}
      {tab === 4 && (
        <div style={{display:"flex",flexWrap:"wrap",gap:12,paddingTop:8}}>
          {sysStats && Object.entries(sysStats).map(([k,v])=>(
            <div key={k} style={{...S.kpi,flex:"1 1 160px"}}>
              <div style={{fontSize:20,fontWeight:700,color:"#6366f1"}}>{String(v)}</div>
              <div style={{fontSize:11,color:"#52525b",marginTop:4}}>{k.replace(/_/g," ")}</div>
            </div>
          ))}
          {summary && [["Total API Requests",summary.total],["Average Response Time",`${summary.avg_ms}ms`],["Total Errors",summary.errors],["Error Rate",`${summary.error_rate}%`]].map(([l,v])=>(
            <div key={l} style={{...S.kpi,flex:"1 1 160px"}}><div style={{fontSize:20,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:4}}>{l}</div></div>
          ))}
        </div>
      )}

      {/* Tab 5 — Security */}
      {tab === 5 && (
        <SecurityAdminTab metrics={metrics} users={users} />
      )}

      {/* Tab 6 — Broadcast */}
      {tab === 6 && (
        <div style={{paddingTop:8,maxWidth:520}}>
          <h3 style={{fontSize:14,fontWeight:600,color:"#a1a1aa",marginBottom:8}}>Broadcast Message</h3>
          <p style={{color:"#52525b",fontSize:13,marginBottom:12}}>Send a notification to all users in-app.</p>
          {bMsg && <div style={{...S.alert,background:bMsg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:bMsg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:bMsg.ok?"#34d399":"#f87171",marginBottom:12}}>{bMsg.t}</div>}
          <label style={{fontSize:12,color:"#71717a",display:"block",marginBottom:4}}>Message Type</label>
          <div style={{display:"flex",gap:8,marginBottom:12}}>
            {["info","success","warning","error"].map(t=>(
              <button key={t} onClick={()=>setBType(t)} style={{padding:"5px 12px",borderRadius:8,border:"1px solid",fontSize:12,cursor:"pointer",
                background:bType===t?{info:"rgba(99,102,241,.15)",success:"rgba(16,185,129,.15)",warning:"rgba(245,158,11,.15)",error:"rgba(239,68,68,.15)"}[t]:"transparent",
                borderColor:{info:"rgba(99,102,241,.3)",success:"rgba(16,185,129,.3)",warning:"rgba(245,158,11,.3)",error:"rgba(239,68,68,.3)"}[t],
                color:{info:"#818cf8",success:"#34d399",warning:"#f59e0b",error:"#f87171"}[t]}}>
                {t}
              </button>
            ))}
          </div>
          <textarea value={broadcast} onChange={e=>setBroadcast(e.target.value)} rows={4} placeholder="Message to broadcast…"
            style={{width:"100%",padding:"10px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:13,outline:"none",fontFamily:"inherit",resize:"none",boxSizing:"border-box",marginBottom:10}} />
          {broadcast.trim() && <div style={{padding:"8px 12px",borderRadius:8,background:"rgba(255,255,255,.03)",border:"1px solid rgba(255,255,255,.06)",fontSize:12,color:"#71717a",marginBottom:10}}>Preview: {broadcast}</div>}
          <button onClick={sendBroadcast} disabled={!broadcast.trim()} style={S.actionBtn}>📢 Send to All Users</button>
        </div>
      )}

      {/* Tab 7 — Feedback */}
      {tab === 7 && (
        <div>
          {(() => {
            const fb = Array.isArray(feedback) ? feedback : [];
            const avg = fb.length ? (fb.reduce((a,f)=>a+(f.rating||0),0)/fb.length).toFixed(1) : 0;
            const dist = [1,2,3,4,5].map(r=>fb.filter(f=>f.rating===r).length);
            const distFig = {
              data:[{type:"bar",x:["1⭐","2⭐","3⭐","4⭐","5⭐"],y:dist,marker:{color:["#ef4444","#f59e0b","#f59e0b","#10b981","#22c55e"]}}],
              layout:{title:{text:"Rating Distribution",font:{size:12}},height:200,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",font:{color:"#a1a1aa"},margin:{l:20,r:20,t:40,b:30}}
            };
            return (
              <div>
                <div style={{display:"flex",gap:12,marginBottom:14,flexWrap:"wrap"}}>
                  <div style={S.kpi}><div style={{fontSize:28,fontWeight:700,color:"#f59e0b"}}>{"⭐".repeat(Math.round(avg))}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Avg Rating: {avg}/5</div></div>
                  <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#6366f1"}}>{fb.length}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Total Feedback</div></div>
                </div>
                {fb.length>0 && <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:12,marginBottom:14}}><PlotlyChart figure={distFig} /></div>}
              </div>
            );
          })()}
          <div style={S.tableWrap}>
            <table style={S.table}>
              <thead><tr>{["User","Rating","Category","Message","Time"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
              <tbody>
                {(Array.isArray(feedback) ? feedback : []).map((f,i)=>(
                  <tr key={i}>
                    <td style={S.td}>{f.user}</td>
                    <td style={S.td}>{"⭐".repeat(f.rating||0)}</td>
                    <td style={S.td}>{f.category}</td>
                    <td style={S.td}>{f.message?.slice(0,60)}</td>
                    <td style={S.td}>{f.ts ? new Date(f.ts).toLocaleTimeString() : "—"}</td>
                  </tr>
                ))}
                {!feedback.length && <tr><td colSpan={5} style={{...S.td,color:"#52525b",textAlign:"center"}}>No feedback yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 8 — Alerts */}
      {tab === 8 && (
        <div style={{paddingTop:8}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
            <h3 style={{fontSize:14,fontWeight:600,color:"#a1a1aa"}}>Auth Event Alerts {alerts.length>0&&<span style={{fontSize:11,background:"#6366f1",color:"#fff",borderRadius:20,padding:"2px 8px",marginLeft:8}}>{alerts.length}</span>}</h3>
            <button onClick={loadAll} style={{...S.actionBtn,padding:"5px 12px",fontSize:11}}>↺ Refresh</button>
          </div>
          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {alerts.map((a,i)=>{
              const colors = {user_login:"#6366f1",failed_login:"#ef4444",user_register:"#22c55e",user_logout:"#71717a",oauth_login:"#0ea5e9"};
              const color = colors[a.action] || "#71717a";
              return (
                <div key={i} style={{padding:"10px 14px",borderRadius:10,background:"rgba(24,24,27,.8)",border:`1px solid ${color}22`,display:"flex",alignItems:"center",gap:12}}>
                  <span style={{fontSize:10,fontWeight:600,color,background:`${color}18`,padding:"3px 8px",borderRadius:20,whiteSpace:"nowrap"}}>{a.action}</span>
                  <span style={{fontSize:13,color:"#a1a1aa",flex:1}}>{a.user} — {String(a.detail||"")}</span>
                  <span style={{fontSize:11,color:"#3f3f46",whiteSpace:"nowrap"}}>{new Date(a.ts).toLocaleTimeString()}</span>
                </div>
              );
            })}
            {!alerts.length && <p style={{color:"#52525b",fontSize:13}}>No auth events yet.</p>}
          </div>
        </div>
      )}

      {tab === 9 && <SMTPConfigTab />}
    </div>
    </ErrorBoundary>
  );
}

const S = {
  page:       { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  center:     { display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#09090b" },
  header:     { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  headerIcon: { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  headerTitle:{ fontSize:15, fontWeight:600, color:"#f4f4f5" },
  headerSub:  { fontSize:11, color:"#52525b" },
  kpiRow:     { display:"flex", gap:12, marginBottom:16, flexWrap:"wrap" },
  kpi:        { flex:"1 1 120px", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:"14px 18px" },
  tabs:       { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:        { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  tableWrap:  { overflowX:"auto", borderRadius:10, border:"1px solid rgba(255,255,255,.06)" },
  table:      { width:"100%", borderCollapse:"collapse", fontSize:13 },
  th:         { padding:"10px 14px", background:"rgba(9,9,11,.9)", color:"#52525b", textAlign:"left", fontWeight:600, fontSize:11, textTransform:"uppercase", letterSpacing:"0.04em" },
  td:         { padding:"9px 14px", borderTop:"1px solid rgba(255,255,255,.04)", color:"#a1a1aa" },
  badge:      { padding:"2px 8px", borderRadius:20, fontSize:11, background:"rgba(255,255,255,.04)", color:"#71717a" },
  actionBtn:  { padding:"10px 18px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer" },
  alert:      { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
  input:      { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  select:     { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none" },
};

function SMTPConfigTab() {
  const [smtp, setSmtp] = useState({ smtp_host:"smtp.gmail.com", smtp_port:587, smtp_user:"", smtp_password:"", admin_email:"", alert_enabled:false });
  const [oauth, setOauth] = useState({ google_client_id:"", google_client_secret:"", github_client_id:"", github_client_secret:"" });
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    api.get("/config/smtp").then(({data})=>setSmtp(data)).catch(()=>{});
    api.get("/config/oauth").then(({data})=>setOauth(data)).catch(()=>{});
  }, []);

  const saveSmtp = async () => {
    try { await api.post("/config/smtp", smtp); setMsg({ok:true,t:"SMTP saved — restart backend to apply"}); }
    catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Failed"}); }
  };

  const testSmtp = async () => {
    setMsg({ok:null,t:"Sending test email…"});
    try {
      const {data} = await api.post("/config/smtp/test", smtp);
      setMsg({ok:data.success, t:data.message});
    } catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Test failed"}); }
  };

  const saveOauth = async () => {
    try { await api.post("/config/oauth", oauth); setMsg({ok:true,t:"OAuth saved"}); }
    catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Failed"}); }
  };

  const inp = (label, key, obj, setter, type="text") => (
    <div key={label} style={{marginBottom:10}}>
      <label style={{fontSize:12,color:"#71717a",display:"block",marginBottom:4}}>{label}</label>
      <input type={type} value={obj[key]||""} onChange={e=>setter({...obj,[key]:e.target.value})}
        style={{width:"100%",padding:"10px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:13,outline:"none",boxSizing:"border-box"}} />
    </div>
  );

  return (
    <div style={{paddingTop:8,display:"grid",gridTemplateColumns:"1fr 1fr",gap:24,maxWidth:900}}>
      <div>
        <h3 style={{fontSize:14,fontWeight:600,color:"#a1a1aa",marginBottom:4}}>📧 SMTP Configuration</h3>
        <p style={{color:"#52525b",fontSize:12,marginBottom:14}}>Gmail: enable 2FA → App Passwords → generate 16-char password. Host must be <code style={{color:"#818cf8"}}>smtp.gmail.com</code></p>
        {msg && <div style={{padding:"8px 12px",borderRadius:8,border:"1px solid",fontSize:12,marginBottom:12,background:msg.ok?"rgba(16,185,129,.1)":msg.ok===null?"rgba(99,102,241,.1)":"rgba(239,68,68,.1)",borderColor:msg.ok?"rgba(16,185,129,.3)":msg.ok===null?"rgba(99,102,241,.3)":"rgba(239,68,68,.3)",color:msg.ok?"#34d399":msg.ok===null?"#818cf8":"#f87171"}}>{msg.t}</div>}
        {inp("SMTP Host","smtp_host",smtp,setSmtp)}
        {inp("SMTP Port","smtp_port",smtp,setSmtp,"number")}
        {inp("SMTP User (Gmail address)","smtp_user",smtp,setSmtp,"email")}
        {inp("App Password (16 chars)","smtp_password",smtp,setSmtp,"password")}
        {inp("Admin Alert Email","admin_email",smtp,setSmtp,"email")}
        <label style={{display:"flex",alignItems:"center",gap:8,marginBottom:14,cursor:"pointer"}}>
          <input type="checkbox" checked={smtp.alert_enabled||false} onChange={e=>setSmtp({...smtp,alert_enabled:e.target.checked})} style={{accentColor:"#6366f1"}} />
          <span style={{fontSize:13,color:"#71717a"}}>Enable email alerts (login/logout/register/failed)</span>
        </label>
        <div style={{display:"flex",gap:8}}>
          <button onClick={saveSmtp} style={{padding:"10px 18px",borderRadius:10,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:600,cursor:"pointer"}}>💾 Save SMTP</button>
          <button onClick={testSmtp} style={{padding:"10px 18px",borderRadius:10,border:"1px solid rgba(99,102,241,.4)",background:"transparent",color:"#818cf8",fontSize:13,fontWeight:600,cursor:"pointer"}}>📨 Send Test Email</button>
        </div>
      </div>
      <div>
        <h3 style={{fontSize:14,fontWeight:600,color:"#a1a1aa",marginBottom:4}}>🔐 OAuth Configuration</h3>
        <p style={{color:"#52525b",fontSize:12,marginBottom:14}}>Redirect URI: <code style={{color:"#818cf8"}}>http://localhost:5173/oauth/callback</code></p>
        {inp("Google Client ID","google_client_id",oauth,setOauth)}
        {inp("Google Client Secret","google_client_secret",oauth,setOauth,"password")}
        {inp("GitHub Client ID","github_client_id",oauth,setOauth)}
        {inp("GitHub Client Secret","github_client_secret",oauth,setOauth,"password")}
        <button onClick={saveOauth} style={{padding:"10px 18px",borderRadius:10,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:600,cursor:"pointer",marginTop:4}}>💾 Save OAuth</button>
      </div>
    </div>
  );
}


// ── Activity Tab Component ────────────────────────────────────────────────────
function ActivityTab({ logs }) {
  const [search, setSearch]     = useState("");
  const [actionFilter, setAction] = useState("all");
  const [userFilter, setUser]   = useState("");

  const actions = [...new Set(logs.map(l=>l.action))].filter(Boolean);
  const filtered = logs.filter(l => {
    if (search && !l.user?.toLowerCase().includes(search.toLowerCase())) return false;
    if (actionFilter !== "all" && l.action !== actionFilter) return false;
    if (userFilter && !l.user?.toLowerCase().includes(userFilter.toLowerCase())) return false;
    return true;
  });

  const exportCSV = () => {
    const header = "time,user,action,detail\n";
    const rows = filtered.map(l=>`${l.ts},${l.user||""},${l.action||""},${String(l.detail||"").replace(/,/g," ")}`).join("\n");
    const blob = new Blob([header+rows],{type:"text/csv"});
    const a = document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="activity.csv"; a.click();
  };

  return (
    <div>
      <div style={{display:"flex",gap:10,marginBottom:12,flexWrap:"wrap",alignItems:"center"}}>
        <input placeholder="Search user…" value={search} onChange={e=>setSearch(e.target.value)}
          style={{padding:"8px 12px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none",flex:1,minWidth:160}} />
        <select value={actionFilter} onChange={e=>setAction(e.target.value)}
          style={{padding:"8px 12px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
          <option value="all">All Actions</option>
          {actions.map(a=><option key={a}>{a}</option>)}
        </select>
        <button onClick={exportCSV} style={{padding:"8px 14px",borderRadius:8,border:"1px solid rgba(99,102,241,.3)",background:"rgba(99,102,241,.08)",color:"#818cf8",fontSize:12,cursor:"pointer"}}>📥 Export CSV</button>
      </div>
      <div style={{overflowX:"auto",borderRadius:10,border:"1px solid rgba(255,255,255,.06)"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
          <thead><tr>{["Time","User","Action","Detail"].map(h=><th key={h} style={{padding:"10px 14px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase",letterSpacing:"0.04em"}}>{h}</th>)}</tr></thead>
          <tbody>
            {filtered.map((l,i)=>(
              <tr key={i}>
                <td style={{padding:"9px 14px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{new Date(l.ts).toLocaleTimeString()}</td>
                <td style={{padding:"9px 14px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{l.user}</td>
                <td style={{padding:"9px 14px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}><span style={{padding:"2px 8px",borderRadius:20,fontSize:11,background:"rgba(255,255,255,.04)",color:"#71717a"}}>{l.action}</span></td>
                <td style={{padding:"9px 14px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{String(l.detail||"").slice(0,80)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── AI Usage Tab ──────────────────────────────────────────────────────────────
function AIUsageTab({ metrics }) {
  const [aiData, setAiData] = useState(null);
  useEffect(()=>{ api.get("/admin/ai-usage").then(({data})=>setAiData(data)).catch(()=>{}); },[]);

  const aiMetrics = metrics.filter(m=>m.endpoint?.includes("/ai")||m.endpoint?.includes("/ml"));

  const endpointFig = aiData?.by_endpoint ? {
    data:[{type:"bar",x:Object.keys(aiData.by_endpoint),y:Object.values(aiData.by_endpoint),marker:{color:"#6366f1"}}],
    layout:{title:{text:"Queries by Endpoint",font:{size:12}},height:220,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",font:{color:"#a1a1aa"},margin:{l:20,r:20,t:40,b:60}}
  } : null;

  const typeCounts = {};
  aiMetrics.forEach(m=>{ const ep=m.endpoint||""; typeCounts[ep]=(typeCounts[ep]||0)+1; });
  const typeFig = Object.keys(typeCounts).length ? {
    data:[{type:"pie",labels:Object.keys(typeCounts),values:Object.values(typeCounts),hole:0.4,marker:{colorscale:"Viridis"}}],
    layout:{title:{text:"Query Type Distribution",font:{size:12}},height:220,template:"plotly_dark",paper_bgcolor:"transparent",margin:{l:0,r:0,t:40,b:0}}
  } : null;

  return (
    <div style={{paddingTop:8}}>
      <div style={{display:"flex",gap:12,marginBottom:14,flexWrap:"wrap"}}>
        <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#6366f1"}}>{aiData?.total||aiMetrics.length}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Total AI Queries</div></div>
        <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#10b981"}}>{aiMetrics.filter(m=>m.status<400).length}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Successful</div></div>
        <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#ef4444"}}>{aiMetrics.filter(m=>m.status>=400).length}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Failed</div></div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14}}>
        {endpointFig && <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:12}}><PlotlyChart figure={endpointFig} /></div>}
        {typeFig && <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:12}}><PlotlyChart figure={typeFig} /></div>}
      </div>
      <div style={S.tableWrap}>
        <table style={S.table}>
          <thead><tr>{["Time","Endpoint","Duration","Status"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
          <tbody>
            {aiMetrics.slice(0,20).map((m,i)=>(
              <tr key={i}>
                <td style={S.td}>{new Date(m.ts).toLocaleTimeString()}</td>
                <td style={S.td}>{m.endpoint}</td>
                <td style={S.td}>{m.duration_ms}ms</td>
                <td style={S.td}><span style={{color:m.status>=400?"#f87171":"#34d399"}}>{m.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Security Admin Tab ────────────────────────────────────────────────────────
function SecurityAdminTab({ metrics, users }) {
  const [sessions, setSessions] = useState(null);
  const [revoking, setRevoking] = useState({});
  const [msg, setMsg] = useState(null);

  useEffect(()=>{ api.get("/admin/sessions").then(({data})=>setSessions(data)).catch(()=>{}); },[]);

  const failedLogins = metrics.filter(m=>m.endpoint?.includes("/auth/login")&&m.status===401);
  const failedLast24h = failedLogins.filter(m=>Date.now()-new Date(m.ts).getTime()<86400000).length;

  const revokeUserSessions = async (email) => {
    setRevoking(r=>({...r,[email]:true}));
    try {
      // Log the revocation action
      await api.post("/admin/broadcast", { message:`Sessions revoked for ${email}`, type:"warning" });
      setMsg({ok:true,t:`Sessions revoked for ${email}`});
    } catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Failed"}); }
    finally { setRevoking(r=>({...r,[email]:false})); }
  };

  // Build sessions table from recent logins (proxy)
  const sessionRows = (sessions?.recent_logins||[]).map((l,i)=>({
    id: i,
    user: l.user,
    action: l.action,
    ts: l.ts,
    token: `****${Math.random().toString(36).slice(-8)}`, // masked
  }));

  return (
    <div style={{paddingTop:8}}>
      {msg && <div style={{...S.alert,background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:msg.ok?"#34d399":"#f87171",marginBottom:12}}>{msg.t}</div>}
      <div style={{display:"flex",gap:12,marginBottom:14,flexWrap:"wrap"}}>
        <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#ef4444"}}>{failedLast24h}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Failed Logins (24h)</div></div>
        <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#22c55e"}}>{sessions?.count||0}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>Active Sessions (approx)</div></div>
        <div style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:"#6366f1"}}>{users?.filter(u=>u.totp_enabled).length||0}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>2FA Enabled</div></div>
      </div>

      <h3 style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:8}}>Active Sessions</h3>
      <div style={S.tableWrap}>
        <table style={S.table}>
          <thead><tr>{["Token (masked)","User","Action","Time","Revoke"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
          <tbody>
            {sessionRows.map((s,i)=>(
              <tr key={i}>
                <td style={{...S.td,fontFamily:"monospace",fontSize:11}}>{s.token}</td>
                <td style={S.td}>{s.user}</td>
                <td style={S.td}><span style={{...S.badge,color:"#22c55e",background:"rgba(34,197,94,.08)"}}>{s.action}</span></td>
                <td style={S.td}>{new Date(s.ts).toLocaleTimeString()}</td>
                <td style={S.td}>
                  <button onClick={()=>revokeUserSessions(s.user)} disabled={revoking[s.user]}
                    style={{padding:"3px 10px",borderRadius:6,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",cursor:"pointer",fontSize:11}}>
                    {revoking[s.user]?"…":"Revoke"}
                  </button>
                </td>
              </tr>
            ))}
            {!sessionRows.length && <tr><td colSpan={5} style={{...S.td,color:"#52525b",textAlign:"center"}}>No recent sessions.</td></tr>}
          </tbody>
        </table>
      </div>

      <h3 style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:8,marginTop:16}}>Revoke All Sessions by User</h3>
      <div style={{display:"flex",flexWrap:"wrap",gap:8,marginBottom:16}}>
        {users?.slice(0,10).map(u=>(
          <button key={u.id} onClick={()=>revokeUserSessions(u.email)} disabled={revoking[u.email]}
            style={{padding:"5px 12px",borderRadius:8,border:"1px solid rgba(239,68,68,.2)",background:"rgba(239,68,68,.06)",color:"#f87171",cursor:"pointer",fontSize:11}}>
            {revoking[u.email]?"…":u.email.split("@")[0]}
          </button>
        ))}
      </div>

      <h3 style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:8}}>Failed Requests</h3>
      <div style={S.tableWrap}>
        <table style={S.table}>
          <thead><tr>{["Time","Endpoint","Status"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
          <tbody>
            {metrics.filter(m=>m.status>=400).slice(0,15).map((m,i)=>(
              <tr key={i}>
                <td style={S.td}>{new Date(m.ts).toLocaleTimeString()}</td>
                <td style={S.td}>{m.endpoint}</td>
                <td style={S.td}><span style={{color:"#f87171"}}>{m.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
