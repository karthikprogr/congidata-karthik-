import { useEffect, useState } from "react";
import { api, workspaceApi } from "../api/client";

const S = {
  page:  { padding:"16px 20px", background:"#09090b", minHeight:"100vh", color:"#f4f4f5" },
  card:  { background:"rgba(24,24,27,.9)", border:"1px solid rgba(255,255,255,.07)", borderRadius:12, padding:12, marginBottom:10 },
  btn:   { padding:"6px 12px", borderRadius:7, border:"1px solid rgba(99,102,241,.3)", background:"rgba(99,102,241,.15)", color:"#818cf8", fontSize:12, fontWeight:600, cursor:"pointer", whiteSpace:"nowrap", flexShrink:0 },
  btnRed:{ padding:"6px 12px", borderRadius:7, border:"1px solid rgba(239,68,68,.3)", background:"rgba(239,68,68,.08)", color:"#f87171", fontSize:12, fontWeight:600, cursor:"pointer", whiteSpace:"nowrap", flexShrink:0 },
  btnGreen:{ padding:"6px 12px", borderRadius:7, border:"1px solid rgba(16,185,129,.3)", background:"rgba(16,185,129,.08)", color:"#34d399", fontSize:12, fontWeight:600, cursor:"pointer", whiteSpace:"nowrap", flexShrink:0 },
  input: { background:"rgba(9,9,11,.9)", border:"1px solid rgba(255,255,255,.1)", borderRadius:7, padding:"6px 9px", color:"#f4f4f5", fontSize:12, outline:"none", minWidth:0 },
  select:{ background:"rgba(9,9,11,.9)", border:"1px solid rgba(255,255,255,.1)", borderRadius:7, padding:"6px 9px", color:"#f4f4f5", fontSize:12, cursor:"pointer", flexShrink:0 },
  label: { fontSize:10, color:"#52525b", display:"block", marginBottom:3, textTransform:"uppercase", letterSpacing:".05em" },
  tab:   (a) => ({ padding:"5px 10px", background:"transparent", border:"none", fontSize:11, fontWeight:500, cursor:"pointer", borderBottom: a?"2px solid #6366f1":"2px solid transparent", color:a?"#818cf8":"#52525b", whiteSpace:"nowrap" }),
  badge: (c) => ({ padding:"2px 7px", borderRadius:20, fontSize:10, fontWeight:600, background:`${c}18`, color:c, flexShrink:0 }),
};

const ROLE_COLOR = { owner:"#f59e0b", admin:"#ef4444", editor:"#6366f1", viewer:"#52525b" };
const TABS = ["🏠 My Workspaces","➕ Create","🔗 Join","📊 Analytics","📌 Pinned","🗂 Shared Data","📋 Activity"];

export default function Workspaces() {
  const [workspaces, setWorkspaces] = useState([]);
  const [tab, setTab]       = useState(0);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [msg, setMsg]       = useState(null);
  const [loading, setLoad]  = useState(false);

  // Create
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  // Invite
  const [invEmail, setInvEmail] = useState("");
  const [invRole, setInvRole]   = useState("editor");
  const [invitations, setInvitations] = useState([]);
  // Join
  const [joinToken, setJoinToken] = useState("");
  const [joinInfo, setJoinInfo]   = useState(null);
  // Members
  const [members, setMembers] = useState([]);
  // Activity
  const [activity, setActivity] = useState([]);
  // Pins
  const [pins, setPins]     = useState([]);
  const [pinTitle, setPinTitle] = useState("");
  const [pinType, setPinType]   = useState("bar");
  const [pinX, setPinX]     = useState("");
  const [pinY, setPinY]     = useState("");
  // Shared datasets
  const [sharedDs, setSharedDs] = useState([]);
  // Analytics
  const [wsAnalytics, setWsAnalytics] = useState(null);
  // Transfer
  const [transferEmail, setTransferEmail] = useState("");
  // Settings
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  const flash = (ok, text) => { setMsg({ok,text}); setTimeout(()=>setMsg(null),4000); };

  const load = async () => {
    try { const {data} = await workspaceApi.list(); setWorkspaces(data); }
    catch {}
  };

  // Load templates on mount
  useEffect(() => {
    api.get("/workspaces/templates").then(r => setTemplates(r.data?.templates || [])).catch(()=>{});
  }, []);

  const loadDetailFull = async (ws) => {
    setSelected(ws);
    // Only load essential data immediately — rest loads lazily when tab is clicked
    try {
      const [mem, anl, det] = await Promise.allSettled([
        api.get(`/workspaces/${ws.id}/members`),
        api.get(`/workspaces/${ws.id}/analytics`),
        api.get(`/workspaces/${ws.id}`),
      ]);
      if (mem.status==="fulfilled") setMembers(mem.value.data);
      if (anl.status==="fulfilled") setWsAnalytics(anl.value.data);
      if (det.status==="fulfilled") {
        setDetail(det.value.data);
        setEditName(det.value.data.name);
        setEditDesc(det.value.data.description);
      }
    } catch {}
  };

  // Lazy load tab data on demand
  const loadTab = async (ws, tabIndex) => {
    if (!ws) return;
    const id = ws.id;
    try {
      if (tabIndex === 11) { const r = await api.get(`/workspaces/${id}/invitations`); setInvitations(r.data); }
      else if (tabIndex === 12) { const r = await api.get(`/workspaces/${id}/datasets`); setSharedDs(r.data?.datasets||[]); }
      else if (tabIndex === 13) { const r = await api.get(`/workspaces/${id}/pins`); setPins(r.data?.pins||[]); }
      else if (tabIndex === 14) { const r = await api.get(`/workspaces/${id}/chat`); setChatMsgs(r.data?.messages||[]); }
      else if (tabIndex === 15) { const r = await api.get(`/workspaces/${id}/queries`); setQueries(r.data?.queries||[]); }
      else if (tabIndex === 16) { const r = await api.get(`/workspaces/${id}/announcements`); setAnnouncements(r.data?.announcements||[]); }
      else if (tabIndex === 17) { const r = await api.get(`/workspaces/${id}/presence`); setPresence(r.data?.presence||[]); }
      else if (tabIndex === 18) { const r = await api.get(`/workspaces/${id}/reports`); setWsReports(r.data?.reports||[]); }
      else if (tabIndex === 19) { const r = await api.get(`/workspaces/${id}/notebooks`); setNotebooks(r.data?.notebooks||[]); }
      else if (tabIndex === 20) { const r = await api.get(`/workspaces/${id}/tasks`); setTasks(r.data||{board:{todo:[],in_progress:[],review:[],done:[]}}); }
      else if (tabIndex === 21) { const r = await api.get(`/workspaces/${id}/goals`); setGoals(r.data?.goals||[]); }
      else if (tabIndex === 22) { const r = await api.get(`/workspaces/${id}/webhooks`); setWebhooks(r.data?.webhooks||[]); }
      else if (tabIndex === 23) { const r = await api.get(`/workspaces/${id}/versions`); setVersions(r.data?.versions||[]); }
      else if (tabIndex === 24) { const r = await api.get(`/workspaces/${id}/leaderboard`); setLeaderboard(r.data?.leaderboard||[]); }
      else if (tabIndex === 25) { const r = await api.get(`/workspaces/${id}/summary`); setWsSummary(r.data); }
      else if (tabIndex === 26) { const r = await api.get(`/workspaces/${id}/polls`); setPolls(r.data?.polls||[]); }
      else if (tabIndex === 27) { const r = await api.get(`/workspaces/${id}/contracts`); setContracts(r.data?.contracts||[]); }
      else if (tabIndex === 28) { const r = await api.get(`/workspaces/${id}/integrations`); setIntegrations(r.data?.integrations||[]); }
      else if (tabIndex === 29) { const r = await api.get(`/workspaces/${id}/permissions`); setPermMatrix(r.data||{matrix:[],features:[]}); }
      else if (tabIndex === 30) { const r = await api.get(`/workspaces/${id}/changelog`); setChangelog(r.data?.changelog||[]); }
      else if (tabIndex === 31) { const r = await api.get(`/workspaces/${id}/metrics`); setMetrics(r.data?.metrics||[]); }
      else if (tabIndex === 32) { const r = await api.get(`/workspaces/${id}/digest`); setDigest(r.data); }
      else if (tabIndex === 33) { const r = await api.get(`/workspaces/${id}/activity`); setActivity(r.data?.events||[]); }
    } catch {}
  };

  useEffect(() => {
    load();
    const params = new URLSearchParams(window.location.search);
    const t = params.get("token");
    if (t) { setJoinToken(t); setTab(2); }
  }, []);

  // Replace all loadDetail calls with loadDetailFull
  const loadDetail = loadDetailFull;

  const create = async () => {
    if (!newName.trim()) return;
    setLoad(true);
    try {
      await workspaceApi.create(newName, newDesc);
      setNewName(""); setNewDesc(""); await load();
      flash(true, `Workspace "${newName}" created`);
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
    finally { setLoad(false); }
  };

  const invite = async () => {
    if (!invEmail.trim() || !selected) return;
    setLoad(true);
    try {
      await workspaceApi.invite(selected.id, invEmail, invRole);
      setInvEmail(""); await loadDetail(selected);
      flash(true, `Invitation sent to ${invEmail}`);
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
    finally { setLoad(false); }
  };

  const lookupJoin = async () => {
    if (!joinToken.trim()) return;
    try {
      const {data} = await api.get(`/workspaces/join/info?token=${joinToken}`);
      setJoinInfo(data);
    } catch(e) { flash(false, e.response?.data?.detail||"Invalid token"); }
  };

  const join = async () => {
    setLoad(true);
    try {
      await workspaceApi.join(joinToken);
      setJoinToken(""); setJoinInfo(null); await load();
      flash(true, "Joined workspace!");
      setTab(0);
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
    finally { setLoad(false); }
  };

  const changeRole = async (userId, role) => {
    try {
      await api.patch(`/workspaces/${selected.id}/members/${userId}/role`, {role});
      await loadDetail(selected);
      flash(true, "Role updated");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const removeMember = async (userId) => {
    try {
      await api.delete(`/workspaces/${selected.id}/members/${userId}`);
      await loadDetail(selected);
      flash(true, "Member removed");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const shareDataset = async () => {
    try {
      const {data} = await api.post(`/workspaces/${selected.id}/datasets/share`);
      await loadDetail(selected);
      flash(true, data.message);
    } catch(e) { flash(false, e.response?.data?.detail||"No dataset uploaded"); }
  };

  const loadSharedDs = async (name) => {
    try {
      await api.post(`/workspaces/${selected.id}/datasets/${name}/load`);
      flash(true, `Dataset '${name}' loaded as your active dataset`);
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const pinChart = async () => {
    if (!pinTitle || !pinType) return;
    try {
      await api.post(`/workspaces/${selected.id}/pins`, {title:pinTitle, chart_type:pinType, x_col:pinX, y_col:pinY});
      setPinTitle(""); await loadDetail(selected);
      flash(true, "Chart pinned to workspace");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const deletePin = async (pinId) => {
    try {
      await api.delete(`/workspaces/${selected.id}/pins/${pinId}`);
      await loadDetail(selected);
    } catch {}
  };

  const updateSettings = async () => {
    try {
      await api.patch(`/workspaces/${selected.id}`, {name:editName, description:editDesc});
      await load(); await loadDetail(selected);
      flash(true, "Workspace updated");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const transferOwnership = async () => {
    if (!transferEmail.trim()) return;
    try {
      await api.post(`/workspaces/${selected.id}/transfer-ownership`, {new_owner_email:transferEmail});
      setTransferEmail(""); await load(); await loadDetail(selected);
      flash(true, `Ownership transferred to ${transferEmail}`);
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const deleteWs = async (id) => {
    try {
      await workspaceApi.delete(id); await load();
      if (selected?.id === id) { setSelected(null); setDetail(null); }
      flash(true, "Workspace deleted");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const revokeInv = async (invId) => {
    try {
      await api.delete(`/workspaces/${selected.id}/invitations/${invId}`);
      await loadDetail(selected);
    } catch {}
  };

  const resendInv = async (invId) => {
    try {
      await api.post(`/workspaces/${selected.id}/invitations/${invId}/resend`);
      flash(true, "Invitation resent");
    } catch {}
  };

  // Chat
  const sendChat = async () => {
    if (!chatInput.trim() || !selected) return;
    try {
      const {data} = await api.post(`/workspaces/${selected.id}/chat`, {message: chatInput});
      setChatMsgs(prev => [...prev, data]);
      setChatInput("");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const deleteChat = async (msgId) => {
    try {
      await api.delete(`/workspaces/${selected.id}/chat/${msgId}`);
      setChatMsgs(prev => prev.filter(m => m.id !== msgId));
    } catch {}
  };

  // Queries
  const saveQuery = async () => {
    if (!qTitle.trim() || !qText.trim()) return;
    try {
      const {data} = await api.post(`/workspaces/${selected.id}/queries`, {title:qTitle, query:qText, query_type:qType});
      setQueries(prev => [...prev, data]);
      setQTitle(""); setQText("");
      flash(true, "Query saved");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const runQuery = async (qId) => {
    try {
      await api.post(`/workspaces/${selected.id}/queries/${qId}/run`);
      flash(true, "Query marked as run");
      const {data} = await api.get(`/workspaces/${selected.id}/queries`);
      setQueries(data.queries || []);
    } catch {}
  };

  const deleteQuery = async (qId) => {
    try {
      await api.delete(`/workspaces/${selected.id}/queries/${qId}`);
      setQueries(prev => prev.filter(q => q.id !== qId));
    } catch {}
  };

  // Announcements
  const postAnnouncement = async () => {
    if (!annTitle.trim()) return;
    try {
      const {data} = await api.post(`/workspaces/${selected.id}/announcements`, {title:annTitle, body:annBody});
      setAnnouncements(prev => [data, ...prev]);
      setAnnTitle(""); setAnnBody("");
      flash(true, "Announcement posted");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  const deleteAnn = async (annId) => {
    try {
      await api.delete(`/workspaces/${selected.id}/announcements/${annId}`);
      setAnnouncements(prev => prev.filter(a => a.id !== annId));
    } catch {}
  };

  // Workspace reports
  const createWsReport = async () => {
    if (!rptName.trim()) return;
    try {
      const {data} = await api.post(`/workspaces/${selected.id}/reports`, {name:rptName, frequency:rptFreq, report_type:rptType});
      setWsReports(prev => [...prev, data]);
      setRptName("");
      flash(true, "Report scheduled");
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  // Search
  const doSearch = async () => {
    try {
      const {data} = await api.get(`/workspaces/search?q=${encodeURIComponent(searchQ)}`);
      setSearchResults(Array.isArray(data) ? data : []);
    } catch {}
  };

  // Create from template
  const createFromTemplate = async (tmplId) => {
    try {
      const {data} = await api.post("/workspaces/from-template", {template_id:tmplId, name:"", description:""});
      await load();
      flash(true, `Workspace created from template`);
    } catch(e) { flash(false, e.response?.data?.detail||"Failed"); }
  };

  // ── State for new features ────────────────────────────────────────────────
  const [chatMsgs, setChatMsgs] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [queries, setQueries]   = useState([]);
  const [qTitle, setQTitle]     = useState("");
  const [qText, setQText]       = useState("");
  const [qType, setQType]       = useState("natural_language");
  const [announcements, setAnnouncements] = useState([]);
  const [annTitle, setAnnTitle] = useState("");
  const [annBody, setAnnBody]   = useState("");
  const [presence, setPresence] = useState([]);
  const [wsReports, setWsReports] = useState([]);
  const [rptName, setRptName]   = useState("");
  const [rptFreq, setRptFreq]   = useState("Weekly");
  const [rptType, setRptType]   = useState("pdf");
  const [templates, setTemplates] = useState([]);
  const [searchQ, setSearchQ]   = useState("");
  const [searchResults, setSearchResults] = useState([]);

  // State for batch 4 features
  const [polls, setPolls]           = useState([]);
  const [pollQ, setPollQ]           = useState("");
  const [pollOpts, setPollOpts]     = useState("Option A\nOption B");
  const [contracts, setContracts]   = useState([]);
  const [contractName, setContractName] = useState("");
  const [contractSla, setContractSla]   = useState("");
  const [integrations, setIntegrations] = useState([]);
  const [intgType, setIntgType]     = useState("slack");
  const [intgUrl, setIntgUrl]       = useState("");
  const [intgName, setIntgName]     = useState("");
  const [permMatrix, setPermMatrix] = useState({matrix:[], features:[]});
  const [changelog, setChangelog]   = useState([]);
  const [clVersion, setClVersion]   = useState("");
  const [clTitle, setClTitle]       = useState("");
  const [clBody, setClBody]         = useState("");
  const [metrics, setMetrics]       = useState([]);
  const [metricName, setMetricName] = useState("");
  const [metricVal, setMetricVal]   = useState("");
  const [metricUnit, setMetricUnit] = useState("");
  const [digest, setDigest]         = useState(null);
  const [notebooks, setNotebooks] = useState([]);
  const [nbTitle, setNbTitle]     = useState("");
  const [nbContent, setNbContent] = useState("");
  const [activeNb, setActiveNb]   = useState(null);
  const [tasks, setTasks]         = useState({board:{todo:[],in_progress:[],review:[],done:[]}});
  const [taskTitle, setTaskTitle] = useState("");
  const [taskPriority, setTaskPriority] = useState("medium");
  const [taskAssignee, setTaskAssignee] = useState("");
  const [goals, setGoals]         = useState([]);
  const [goalMetric, setGoalMetric] = useState("");
  const [goalTarget, setGoalTarget] = useState("");
  const [goalUnit, setGoalUnit]   = useState("");
  const [webhooks, setWebhooks]   = useState([]);
  const [hookUrl, setHookUrl]     = useState("");
  const [versions, setVersions]   = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [wsSummary, setWsSummary] = useState(null);
  return (
    <div style={S.page}>
      <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:16 }}>
        <div style={{ width:36, height:36, borderRadius:9, background:"rgba(99,102,241,.15)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18 }}>🏢</div>
        <div>
          <div style={{ fontSize:18, fontWeight:700 }}>Workspaces</div>
          <div style={{ fontSize:11, color:"#52525b" }}>Collaborate, share datasets, pin charts</div>
        </div>
      </div>

      {msg && <div style={{ padding:"8px 14px", borderRadius:8, marginBottom:12, fontSize:12, border:"1px solid", background:msg.ok?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)", borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)", color:msg.ok?"#34d399":"#f87171" }}>{msg.text}</div>}

      <div style={{ display:"grid", gridTemplateColumns: selected ? "240px 1fr" : "1fr", gap:14, alignItems:"start" }}>

        {/* Left: workspace list */}
        <div>
          <div style={{ display:"flex", gap:6, marginBottom:12 }}>
            <button onClick={()=>setTab(0)} style={S.tab(tab===0)}>My Workspaces</button>
            <button onClick={()=>setTab(1)} style={S.tab(tab===1)}>Create</button>
            <button onClick={()=>setTab(2)} style={S.tab(tab===2)}>Join</button>
          </div>

          {tab === 0 && (
            <div>
              <div style={{ display:"flex", gap:6, marginBottom:10 }}>
                <input value={searchQ} onChange={e=>setSearchQ(e.target.value)} onKeyDown={e=>e.key==="Enter"&&doSearch()} placeholder="Search workspaces…" style={{ ...S.input, flex:1 }} />
                <button onClick={doSearch} style={S.btn}>🔍</button>
              </div>
              {searchResults.length > 0 && (
                <div style={{ marginBottom:10 }}>
                  <div style={{ fontSize:11, color:"#52525b", marginBottom:6 }}>Search results</div>
                  {searchResults.map(w => (
                    <div key={w.id} style={{ ...S.card, cursor:"pointer" }} onClick={()=>loadDetail(w)}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{w.name}</div>
                      <div style={{ display:"flex", gap:4, marginTop:4 }}>
                        {w.tags?.map(t=><span key={t} style={S.badge("#6366f1")}>{t}</span>)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {workspaces.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No workspaces yet. Create one or join via invite.</p>}
              {workspaces.map(w => (
                <div key={w.id} onClick={() => loadDetail(w)}
                  style={{ ...S.card, cursor:"pointer", borderColor: selected?.id===w.id ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.07)" }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
                    <div>
                      <div style={{ fontSize:14, fontWeight:600 }}>{w.name}</div>
                      <div style={{ fontSize:11, color:"#52525b", marginTop:2 }}>{w.description || "No description"}</div>
                    </div>
                    <span style={S.badge(ROLE_COLOR[w.role] || "#52525b")}>{w.role}</span>
                  </div>
                  <div style={{ display:"flex", gap:10, marginTop:8, fontSize:11, color:"#52525b" }}>
                    <span>👥 {w.member_count}</span>
                    <span>🕐 {w.created_at?.slice(0,10)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {tab === 1 && (
            <div>
              <div style={S.card}>
                <div style={{ fontSize:13, fontWeight:600, marginBottom:12 }}>Create Workspace</div>
                <label style={S.label}>Name</label>
                <input value={newName} onChange={e=>setNewName(e.target.value)} placeholder="My Team" style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
                <label style={S.label}>Description</label>
                <textarea value={newDesc} onChange={e=>setNewDesc(e.target.value)} rows={2} placeholder="What is this workspace for?" style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none", marginBottom:12 }} />
                <button onClick={create} disabled={loading} style={S.btn}>{loading?"Creating…":"+ Create Workspace"}</button>
              </div>
              <div style={{ fontSize:12, fontWeight:600, color:"#52525b", margin:"12px 0 8px" }}>Or start from a template</div>
              {templates.map(t => (
                <div key={t.id} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:13, fontWeight:600 }}>{t.name}</div>
                    <div style={{ fontSize:11, color:"#52525b" }}>{t.description}</div>
                    <div style={{ display:"flex", gap:4, marginTop:4 }}>
                      {t.tags?.map(tag=><span key={tag} style={S.badge("#6366f1")}>{tag}</span>)}
                    </div>
                  </div>
                  <button onClick={()=>createFromTemplate(t.id)} style={S.btnGreen}>Use</button>
                </div>
              ))}
            </div>
          )}

          {tab === 2 && (
            <div style={S.card}>
              <div style={{ fontSize:13, fontWeight:600, marginBottom:12 }}>Join via Invite Token</div>
              <label style={S.label}>Invitation Token</label>
              <input value={joinToken} onChange={e=>setJoinToken(e.target.value)} placeholder="Paste token from email" style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
              <div style={{ display:"flex", gap:8 }}>
                <button onClick={lookupJoin} style={S.btn}>🔍 Preview</button>
                {joinInfo && <button onClick={join} disabled={loading} style={S.btnGreen}>{loading?"Joining…":"✅ Join"}</button>}
              </div>
              {joinInfo && (
                <div style={{ marginTop:12, padding:"10px 12px", borderRadius:8, background:"rgba(99,102,241,.08)", border:"1px solid rgba(99,102,241,.2)" }}>
                  <div style={{ fontSize:13, fontWeight:600 }}>{joinInfo.workspace_name}</div>
                  <div style={{ fontSize:11, color:"#52525b", marginTop:4 }}>You'll join as <span style={{ color:ROLE_COLOR[joinInfo.role] }}>{joinInfo.role}</span></div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: workspace detail */}
        {selected && detail && (
          <div style={{ minWidth:0, overflow:"hidden" }}>
            <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:16 }}>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:18, fontWeight:700 }}>{detail.name}</div>
                <div style={{ fontSize:12, color:"#52525b" }}>{detail.description}</div>
              </div>
              <span style={S.badge(ROLE_COLOR[detail.role])}>{detail.role}</span>
              {detail.role === "owner" && (
                <button onClick={() => deleteWs(selected.id)} style={S.btnRed}>🗑 Delete</button>
              )}
            </div>

            {/* Stats row */}
            <div style={{ display:"flex", gap:8, marginBottom:14, flexWrap:"wrap" }}>
              {[["👥 Members", detail.member_count],["📌 Pins", detail.pinned_count],["🗂 Datasets", detail.shared_datasets],["📋 Events", wsAnalytics?.total_events||0]].map(([l,v])=>(
                <div key={l} style={{ ...S.card, flex:"1 1 80px", textAlign:"center", padding:"8px 10px", marginBottom:0 }}>
                  <div style={{ fontSize:18, fontWeight:700, color:"#818cf8" }}>{v}</div>
                  <div style={{ fontSize:10, color:"#52525b", marginTop:2 }}>{l}</div>
                </div>
              ))}
            </div>

            {/* Sub-tabs */}
            <div style={{ display:"flex", gap:0, borderBottom:"1px solid rgba(255,255,255,.06)", marginBottom:14, overflowX:"auto", scrollbarWidth:"none" }}>
              {["Members","Invite","Datasets","Pins","Chat","Queries","Announcements","Presence","Reports","Notebooks","Tasks","Goals","Webhooks","Versions","Leaderboard","Summary","Polls","Contracts","Integrations","Permissions","Changelog","Metrics","Digest","Activity","Analytics","Settings"].map((t,i)=>(
                <button key={t} onClick={()=>{ setTab(10+i); loadTab(selected, 10+i); }} style={S.tab(tab===10+i)}>{t}</button>
              ))}
            </div>

            {/* Members tab */}
            {tab === 10 && (
              <div>
                {members.map(m => (
                  <div key={m.user_id} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                    <div style={{ width:32, height:32, borderRadius:"50%", background:"rgba(99,102,241,.2)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:14 }}>
                      {m.email?.[0]?.toUpperCase()}
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13 }}>{m.email}</div>
                    </div>
                    {(detail.role === "owner" || detail.role === "admin") ? (
                      <select value={m.role} onChange={e=>changeRole(m.user_id, e.target.value)} style={{ ...S.select, fontSize:11 }}>
                        {["viewer","editor","admin"].map(r=><option key={r}>{r}</option>)}
                      </select>
                    ) : (
                      <span style={S.badge(ROLE_COLOR[m.role]||"#52525b")}>{m.role}</span>
                    )}
                    {detail.role === "owner" && (
                      <button onClick={()=>removeMember(m.user_id)} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                    )}
                  </div>
                ))}
                {members.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No members yet. Invite someone.</p>}
              </div>
            )}

            {/* Invite tab */}
            {tab === 11 && (
              <div>
                <div style={S.card}>
                  <div style={{ fontSize:13, fontWeight:600, marginBottom:12 }}>Invite Member</div>
                  <div style={{ display:"flex", gap:6, flexWrap:"wrap", alignItems:"center" }}>
                    <input value={invEmail} onChange={e=>setInvEmail(e.target.value)} placeholder="email@example.com" style={{ ...S.input, flex:"1 1 160px", minWidth:0 }} />
                    <select value={invRole} onChange={e=>setInvRole(e.target.value)} style={{ ...S.select, flexShrink:0 }}>
                      {["viewer","editor","admin"].map(r=><option key={r}>{r}</option>)}
                    </select>
                    <button onClick={invite} disabled={loading} style={S.btn}>{loading?"Sending…":"📧 Invite"}</button>
                  </div>
                </div>
                <div style={{ fontSize:12, fontWeight:600, color:"#52525b", marginBottom:8 }}>Pending Invitations</div>
                {invitations.map && invitations.map(inv => (
                  <div key={inv.id} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13 }}>{inv.email}</div>
                      <div style={{ fontSize:11, color:"#52525b" }}>{inv.role} · {inv.status}</div>
                    </div>
                    <button onClick={()=>resendInv(inv.id)} style={{ ...S.btn, padding:"4px 8px" }}>↺</button>
                    <button onClick={()=>revokeInv(inv.id)} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                  </div>
                ))}
              </div>
            )}

            {/* Shared Datasets tab */}
            {tab === 12 && (
              <div>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
                  <div style={{ fontSize:13, color:"#71717a" }}>Datasets shared with this workspace</div>
                  {detail.role !== "viewer" && (
                    <button onClick={shareDataset} style={S.btnGreen}>📤 Share My Dataset</button>
                  )}
                </div>
                {sharedDs.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No shared datasets yet.</p>}
                {sharedDs.map(ds => (
                  <div key={ds.name} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{ds.name}</div>
                      <div style={{ fontSize:11, color:"#52525b" }}>by {ds.uploader} · {ds.rows} rows · {ds.cols} cols</div>
                      <div style={{ fontSize:10, color:"#3f3f46", marginTop:2 }}>{ds.columns?.slice(0,5).join(", ")}{ds.columns?.length>5?"…":""}</div>
                    </div>
                    <button onClick={()=>loadSharedDs(ds.name)} style={S.btn}>⬇ Load</button>
                  </div>
                ))}
              </div>
            )}

            {/* Pins tab */}
            {tab === 13 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:16 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Pin a Chart</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                      <input value={pinTitle} onChange={e=>setPinTitle(e.target.value)} placeholder="Chart title" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <input value={pinType} onChange={e=>setPinType(e.target.value)} placeholder="bar / line / scatter…" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <input value={pinX} onChange={e=>setPinX(e.target.value)} placeholder="X column" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <input value={pinY} onChange={e=>setPinY(e.target.value)} placeholder="Y column" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <button onClick={pinChart} style={S.btn}>📌 Pin</button>
                    </div>
                  </div>
                )}
                {pins.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No pinned charts yet.</p>}
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))", gap:10 }}>
                  {pins.map(p => (
                    <div key={p.id} style={S.card}>
                      <div style={{ display:"flex", justifyContent:"space-between" }}>
                        <div style={{ fontSize:13, fontWeight:600 }}>{p.title}</div>
                        <button onClick={()=>deletePin(p.id)} style={{ background:"none", border:"none", color:"#52525b", cursor:"pointer", fontSize:14 }}>✕</button>
                      </div>
                      <div style={{ fontSize:11, color:"#52525b", marginTop:4 }}>
                        {p.chart_type} · {p.x_col||"—"} vs {p.y_col||"—"}
                      </div>
                      <div style={{ fontSize:10, color:"#3f3f46", marginTop:4 }}>by {p.pinned_by?.split("@")[0]}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Chat tab */}
            {tab === 14 && (
              <div style={{ display:"flex", flexDirection:"column", height:420 }}>
                <div style={{ flex:1, overflowY:"auto", display:"flex", flexDirection:"column", gap:6, marginBottom:10 }}>
                  {chatMsgs.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No messages yet. Start the conversation.</p>}
                  {chatMsgs.map(m => (
                    <div key={m.id} style={{ display:"flex", gap:8, alignItems:"flex-start" }}>
                      <div style={{ width:28, height:28, borderRadius:"50%", background:"rgba(99,102,241,.2)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:12, flexShrink:0 }}>{m.user?.[0]?.toUpperCase()}</div>
                      <div style={{ flex:1 }}>
                        <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                          <span style={{ fontSize:12, fontWeight:600, color:"#818cf8" }}>{m.user?.split("@")[0]}</span>
                          <span style={{ fontSize:10, color:"#3f3f46" }}>{m.ts?.slice(11,16)}</span>
                          {m.edited && <span style={{ fontSize:10, color:"#52525b" }}>(edited)</span>}
                        </div>
                        <div style={{ fontSize:13, color:"#e4e4e7", marginTop:2 }}>{m.message}</div>
                      </div>
                      <button onClick={()=>deleteChat(m.id)} style={{ background:"none", border:"none", color:"#3f3f46", cursor:"pointer", fontSize:12, opacity:0.5 }}>✕</button>
                    </div>
                  ))}
                </div>
                <div style={{ display:"flex", gap:8 }}>
                  <input value={chatInput} onChange={e=>setChatInput(e.target.value)}
                    onKeyDown={e=>e.key==="Enter"&&sendChat()}
                    placeholder="Type a message… (Enter to send)"
                    style={{ ...S.input, flex:1 }} />
                  <button onClick={sendChat} style={S.btn}>Send</button>
                </div>
              </div>
            )}

            {/* Queries tab */}
            {tab === 15 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Save a Query</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:8 }}>
                      <input value={qTitle} onChange={e=>setQTitle(e.target.value)} placeholder="Query title" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <select value={qType} onChange={e=>setQType(e.target.value)} style={S.select}>
                        <option value="natural_language">Natural Language</option>
                        <option value="sql">SQL</option>
                        <option value="python">Python</option>
                      </select>
                    </div>
                    <textarea value={qText} onChange={e=>setQText(e.target.value)} rows={3} placeholder="Enter your query…" style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none", marginBottom:8 }} />
                    <button onClick={saveQuery} style={S.btn}>💾 Save Query</button>
                  </div>
                )}
                {queries.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No saved queries yet.</p>}
                {queries.map(q => (
                  <div key={q.id} style={S.card}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
                      <div>
                        <div style={{ fontSize:13, fontWeight:600 }}>{q.title}</div>
                        <div style={{ fontSize:10, color:"#52525b", marginTop:2 }}>{q.query_type} · by {q.created_by?.split("@")[0]} · {q.runs} runs</div>
                      </div>
                      <div style={{ display:"flex", gap:6 }}>
                        <button onClick={()=>runQuery(q.id)} style={{ ...S.btnGreen, padding:"4px 8px" }}>▶ Run</button>
                        <button onClick={()=>deleteQuery(q.id)} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                      </div>
                    </div>
                    <div style={{ marginTop:8, padding:"8px 10px", borderRadius:6, background:"rgba(0,0,0,.3)", fontSize:12, color:"#a1a1aa", fontFamily:"monospace", whiteSpace:"pre-wrap", wordBreak:"break-all" }}>{q.query}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Announcements tab */}
            {tab === 16 && (
              <div>
                {(detail.role === "owner" || detail.role === "admin") && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Post Announcement</div>
                    <input value={annTitle} onChange={e=>setAnnTitle(e.target.value)} placeholder="Title" style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
                    <textarea value={annBody} onChange={e=>setAnnBody(e.target.value)} rows={3} placeholder="Announcement body…" style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none", marginBottom:8 }} />
                    <button onClick={postAnnouncement} style={S.btn}>📢 Post</button>
                  </div>
                )}
                {announcements.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No announcements yet.</p>}
                {announcements.map(a => (
                  <div key={a.id} style={{ ...S.card, borderColor: a.pinned ? "rgba(245,158,11,.3)" : "rgba(255,255,255,.07)" }}>
                    <div style={{ display:"flex", justifyContent:"space-between" }}>
                      <div style={{ fontSize:14, fontWeight:600 }}>{a.pinned && "📌 "}{a.title}</div>
                      {(detail.role === "owner" || detail.role === "admin") && (
                        <button onClick={()=>deleteAnn(a.id)} style={{ background:"none", border:"none", color:"#52525b", cursor:"pointer" }}>✕</button>
                      )}
                    </div>
                    <div style={{ fontSize:13, color:"#a1a1aa", marginTop:6 }}>{a.body}</div>
                    <div style={{ fontSize:10, color:"#3f3f46", marginTop:6 }}>by {a.created_by?.split("@")[0]} · {a.ts?.slice(0,16)}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Presence tab */}
            {tab === 17 && (
              <div>
                <div style={{ fontSize:12, color:"#52525b", marginBottom:10 }}>Member online status (updates every 5 min)</div>
                {presence.map(p => (
                  <div key={p.email} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                    <div style={{ width:8, height:8, borderRadius:"50%", background: p.status==="online"?"#22c55e":p.status==="away"?"#f59e0b":"#3f3f46", flexShrink:0 }} />
                    <div style={{ flex:1, fontSize:13 }}>{p.email}</div>
                    <span style={{ fontSize:11, color: p.status==="online"?"#22c55e":p.status==="away"?"#f59e0b":"#52525b" }}>{p.status}</span>
                    <span style={{ fontSize:10, color:"#3f3f46" }}>{p.last_seen ? p.last_seen.slice(11,16) : "never"}</span>
                  </div>
                ))}
                {presence.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No presence data yet.</p>}
              </div>
            )}

            {/* Reports tab */}
            {tab === 18 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Schedule Team Report</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                      <input value={rptName} onChange={e=>setRptName(e.target.value)} placeholder="Report name" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <select value={rptFreq} onChange={e=>setRptFreq(e.target.value)} style={S.select}>
                        {["Daily","Weekly","Monthly"].map(f=><option key={f}>{f}</option>)}
                      </select>
                      <select value={rptType} onChange={e=>setRptType(e.target.value)} style={S.select}>
                        {["pdf","csv","excel"].map(t=><option key={t}>{t}</option>)}
                      </select>
                      <button onClick={createWsReport} style={S.btn}>+ Schedule</button>
                    </div>
                  </div>
                )}
                {wsReports.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No team reports scheduled.</p>}
                {wsReports.map(r => (
                  <div key={r.id} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{r.name}</div>
                      <div style={{ fontSize:11, color:"#52525b" }}>{r.frequency} · {r.report_type} · by {r.created_by?.split("@")[0]}</div>
                    </div>
                    <span style={S.badge(r.active?"#22c55e":"#52525b")}>{r.active?"Active":"Paused"}</span>
                    <button onClick={()=>api.delete(`/workspaces/${selected.id}/reports/${r.id}`).then(()=>setWsReports(prev=>prev.filter(x=>x.id!==r.id)))} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                  </div>
                ))}
              </div>
            )}

            {/* Notebooks tab */}
            {tab === 19 && (
              <div>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
                  <div style={{ fontSize:13, color:"#71717a" }}>Collaborative notes & documentation</div>
                  {detail.role !== "viewer" && (
                    <button onClick={async()=>{if(!nbTitle.trim())return;const{data}=await api.post(`/workspaces/${selected.id}/notebooks`,{title:nbTitle,content:nbContent});setNotebooks(p=>[...p,data]);setNbTitle("");setNbContent("");}} style={S.btn}>+ New Notebook</button>
                  )}
                </div>
                {detail.role !== "viewer" && !activeNb && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <input value={nbTitle} onChange={e=>setNbTitle(e.target.value)} placeholder="Notebook title" style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
                    <textarea value={nbContent} onChange={e=>setNbContent(e.target.value)} rows={3} placeholder="Content (markdown supported)…" style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none" }} />
                  </div>
                )}
                {activeNb ? (
                  <div style={S.card}>
                    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8 }}>
                      <input value={activeNb.title} onChange={e=>setActiveNb({...activeNb,title:e.target.value})} style={{ ...S.input, flex:1, marginRight:8 }} />
                      <button onClick={async()=>{await api.patch(`/workspaces/${selected.id}/notebooks/${activeNb.id}`,{title:activeNb.title,content:activeNb.content});setActiveNb(null);const{data}=await api.get(`/workspaces/${selected.id}/notebooks`);setNotebooks(data.notebooks||[]);flash(true,"Saved");}} style={S.btnGreen}>💾 Save</button>
                      <button onClick={()=>setActiveNb(null)} style={{ ...S.btn, marginLeft:6 }}>✕</button>
                    </div>
                    <textarea value={activeNb.content} onChange={e=>setActiveNb({...activeNb,content:e.target.value})} rows={12} style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"vertical", fontFamily:"monospace" }} />
                  </div>
                ) : (
                  <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))", gap:10 }}>
                    {notebooks.map(nb => (
                      <div key={nb.id} style={{ ...S.card, cursor:"pointer" }} onClick={()=>setActiveNb({...nb})}>
                        <div style={{ fontSize:13, fontWeight:600 }}>{nb.title}</div>
                        <div style={{ fontSize:11, color:"#52525b", marginTop:4 }}>{nb.content?.slice(0,60)}…</div>
                        <div style={{ fontSize:10, color:"#3f3f46", marginTop:6 }}>by {nb.author?.split("@")[0]} · {nb.updated?.slice(0,10)}</div>
                      </div>
                    ))}
                    {notebooks.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No notebooks yet.</p>}
                  </div>
                )}
              </div>
            )}

            {/* Tasks tab */}
            {tab === 20 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                      <input value={taskTitle} onChange={e=>setTaskTitle(e.target.value)} placeholder="Task title" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <select value={taskPriority} onChange={e=>setTaskPriority(e.target.value)} style={S.select}>
                        {["low","medium","high","critical"].map(p=><option key={p}>{p}</option>)}
                      </select>
                      <input value={taskAssignee} onChange={e=>setTaskAssignee(e.target.value)} placeholder="Assignee email" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <button onClick={async()=>{if(!taskTitle.trim())return;const{data}=await api.post(`/workspaces/${selected.id}/tasks`,{title:taskTitle,priority:taskPriority,assignee:taskAssignee});setTasks(p=>({...p,board:{...p.board,todo:[...(p.board?.todo||[]),data]}}));setTaskTitle("");flash(true,"Task created");}} style={S.btn}>+ Add Task</button>
                    </div>
                  </div>
                )}
                <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10 }}>
                  {["todo","in_progress","review","done"].map(col => (
                    <div key={col}>
                      <div style={{ fontSize:11, fontWeight:600, color:"#52525b", textTransform:"uppercase", marginBottom:8, letterSpacing:".05em" }}>{col.replace("_"," ")} ({(tasks.board?.[col]||[]).length})</div>
                      {(tasks.board?.[col]||[]).map(t => (
                        <div key={t.id} style={{ ...S.card, marginBottom:8 }}>
                          <div style={{ fontSize:12, fontWeight:600 }}>{t.title}</div>
                          <div style={{ display:"flex", gap:4, marginTop:4, flexWrap:"wrap" }}>
                            <span style={S.badge(t.priority==="critical"?"#ef4444":t.priority==="high"?"#f59e0b":t.priority==="medium"?"#6366f1":"#52525b")}>{t.priority}</span>
                            {t.assignee && <span style={{ fontSize:10, color:"#52525b" }}>@{t.assignee.split("@")[0]}</span>}
                          </div>
                          <div style={{ display:"flex", gap:4, marginTop:6 }}>
                            {col !== "done" && <button onClick={async()=>{const next={todo:"in_progress",in_progress:"review",review:"done"}[col];await api.patch(`/workspaces/${selected.id}/tasks/${t.id}`,{status:next});const{data}=await api.get(`/workspaces/${selected.id}/tasks`);setTasks(data);}} style={{ ...S.btnGreen, padding:"3px 6px", fontSize:10 }}>→</button>}
                            <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/tasks/${t.id}`);const{data}=await api.get(`/workspaces/${selected.id}/tasks`);setTasks(data);}} style={{ ...S.btnRed, padding:"3px 6px", fontSize:10 }}>✕</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Goals tab */}
            {tab === 21 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Add KPI Goal</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                      <input value={goalMetric} onChange={e=>setGoalMetric(e.target.value)} placeholder="Metric name" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <input value={goalTarget} onChange={e=>setGoalTarget(e.target.value)} placeholder="Target value" type="number" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <input value={goalUnit} onChange={e=>setGoalUnit(e.target.value)} placeholder="Unit (%, $, …)" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <button onClick={async()=>{if(!goalMetric||!goalTarget)return;const{data}=await api.post(`/workspaces/${selected.id}/goals`,{metric:goalMetric,target:parseFloat(goalTarget),unit:goalUnit});setGoals(p=>[...p,{...data,progress:0,status:"at_risk"}]);setGoalMetric("");setGoalTarget("");flash(true,"Goal added");}} style={S.btn}>+ Add Goal</button>
                    </div>
                  </div>
                )}
                {goals.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No goals set yet.</p>}
                {goals.map(g => (
                  <div key={g.id} style={S.card}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                      <div style={{ fontSize:14, fontWeight:600 }}>{g.metric}</div>
                      <span style={S.badge(g.status==="achieved"?"#22c55e":g.status==="on_track"?"#6366f1":"#ef4444")}>{g.status?.replace("_"," ")}</span>
                    </div>
                    <div style={{ margin:"8px 0 4px", height:6, borderRadius:3, background:"rgba(255,255,255,.06)" }}>
                      <div style={{ height:"100%", borderRadius:3, width:`${g.progress}%`, background:g.status==="achieved"?"#22c55e":g.status==="on_track"?"#6366f1":"#ef4444", transition:"width .3s" }} />
                    </div>
                    <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:"#52525b" }}>
                      <span>{g.current}{g.unit} / {g.target}{g.unit}</span>
                      <span>{g.progress}%</span>
                    </div>
                    {detail.role !== "viewer" && (
                      <div style={{ display:"flex", gap:6, marginTop:8 }}>
                        <input type="number" placeholder="Update current" style={{ ...S.input, flex:1 }} id={`goal-${g.id}`} />
                        <button onClick={async()=>{const v=document.getElementById(`goal-${g.id}`).value;if(!v)return;await api.patch(`/workspaces/${selected.id}/goals/${g.id}`,{current:parseFloat(v)});const{data}=await api.get(`/workspaces/${selected.id}/goals`);setGoals(data.goals||[]);}} style={S.btn}>Update</button>
                        <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/goals/${g.id}`);setGoals(p=>p.filter(x=>x.id!==g.id));}} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Webhooks tab */}
            {tab === 22 && (
              <div>
                {(detail.role === "owner" || detail.role === "admin") ? (
                  <>
                    <div style={{ ...S.card, marginBottom:12 }}>
                      <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Add Webhook</div>
                      <input value={hookUrl} onChange={e=>setHookUrl(e.target.value)} placeholder="https://your-endpoint.com/hook" style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
                      <button onClick={async()=>{if(!hookUrl.trim())return;const{data}=await api.post(`/workspaces/${selected.id}/webhooks`,{url:hookUrl});setWebhooks(p=>[...p,data]);setHookUrl("");flash(true,"Webhook added");}} style={S.btn}>+ Add Webhook</button>
                    </div>
                    {webhooks.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No webhooks configured.</p>}
                    {webhooks.map(h => (
                      <div key={h.id} style={S.card}>
                        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                          <div style={{ fontSize:12, fontFamily:"monospace", color:"#818cf8" }}>{h.url}</div>
                          <div style={{ display:"flex", gap:6 }}>
                            <button onClick={async()=>{const{data}=await api.post(`/workspaces/${selected.id}/webhooks/${h.id}/test`);flash(data.status<400,"Test: "+data.message);}} style={S.btn}>Test</button>
                            <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/webhooks/${h.id}`);setWebhooks(p=>p.filter(x=>x.id!==h.id));}} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                          </div>
                        </div>
                        <div style={{ fontSize:11, color:"#52525b", marginTop:4 }}>Events: {h.events?.join(", ")} · Deliveries: {h.deliveries||0}</div>
                      </div>
                    ))}
                  </>
                ) : <p style={{ color:"#52525b", fontSize:13 }}>Only owner or admin can manage webhooks.</p>}
              </div>
            )}

            {/* Versions tab */}
            {tab === 23 && (
              <div>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
                  <div style={{ fontSize:13, color:"#71717a" }}>Dataset version history</div>
                  {detail.role !== "viewer" && (
                    <button onClick={async()=>{const{data}=await api.post(`/workspaces/${selected.id}/versions/snapshot`);setVersions(p=>[data,...p]);flash(true,`Snapshot ${data.version} saved`);}} style={S.btnGreen}>📸 Snapshot</button>
                  )}
                </div>
                {versions.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No snapshots yet. Click Snapshot to save the current dataset.</p>}
                {versions.map(v => (
                  <div key={v.version} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                    <div style={{ width:36, height:36, borderRadius:8, background:"rgba(99,102,241,.15)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:12, fontWeight:700, color:"#818cf8" }}>{v.version}</div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{v.version} — {v.rows} rows × {v.cols} cols</div>
                      <div style={{ fontSize:11, color:"#52525b" }}>by {v.uploaded_by?.split("@")[0]} · {v.ts?.slice(0,16)} · {v.size_mb}MB</div>
                    </div>
                    <button onClick={async()=>{await api.post(`/workspaces/${selected.id}/datasets/${v.version}/load`);flash(true,`Loaded ${v.version}`);}} style={S.btn}>⬇ Load</button>
                  </div>
                ))}
              </div>
            )}

            {/* Leaderboard tab */}
            {tab === 24 && (
              <div>
                <div style={{ fontSize:13, color:"#71717a", marginBottom:12 }}>Contribution scores based on workspace activity</div>
                {leaderboard.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No activity yet.</p>}
                {leaderboard.map(entry => (
                  <div key={entry.email} style={{ ...S.card, display:"flex", alignItems:"center", gap:12 }}>
                    <div style={{ fontSize:24 }}>{entry.badge}</div>
                    <div style={{ width:28, height:28, borderRadius:"50%", background:"rgba(99,102,241,.2)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:13, fontWeight:700 }}>#{entry.rank}</div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:13, fontWeight:600 }}>{entry.email?.split("@")[0]}</div>
                      <div style={{ fontSize:11, color:"#52525b" }}>{Object.entries(entry.events||{}).slice(0,3).map(([k,v])=>`${k.replace(/_/g," ")}×${v}`).join(" · ")}</div>
                    </div>
                    <div style={{ fontSize:20, fontWeight:700, color:"#818cf8" }}>{entry.score}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Summary tab */}
            {tab === 25 && wsSummary && (
              <div>
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))", gap:10, marginBottom:16 }}>
                  {[["Members",wsSummary.members,"#6366f1"],["Activity 7d",wsSummary.activity_7d,"#10b981"],["Notebooks",wsSummary.notebooks,"#f59e0b"],["Tasks",wsSummary.tasks?.total,"#8b5cf6"],["Goals",wsSummary.goals?.length,"#0ea5e9"],["Versions",wsSummary.versions,"#ec4899"],["Webhooks",wsSummary.webhooks,"#ef4444"],["Queries",wsSummary.saved_queries,"#22c55e"]].map(([l,v,c])=>(
                    <div key={l} style={{ ...S.card, textAlign:"center", marginBottom:0 }}>
                      <div style={{ fontSize:22, fontWeight:700, color:c }}>{v??0}</div>
                      <div style={{ fontSize:11, color:"#52525b", marginTop:2 }}>{l}</div>
                    </div>
                  ))}
                </div>
                {wsSummary.goals?.length > 0 && (
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Goal Progress</div>
                    {wsSummary.goals.map((g,i) => (
                      <div key={i} style={{ marginBottom:8 }}>
                        <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:3 }}>
                          <span>{g.metric}</span>
                          <span style={{ color:g.status==="achieved"?"#22c55e":g.status==="on_track"?"#6366f1":"#ef4444" }}>{g.progress}%</span>
                        </div>
                        <div style={{ height:4, borderRadius:2, background:"rgba(255,255,255,.06)" }}>
                          <div style={{ height:"100%", borderRadius:2, width:`${g.progress}%`, background:g.status==="achieved"?"#22c55e":g.status==="on_track"?"#6366f1":"#ef4444" }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                {wsSummary.top_contributors?.length > 0 && (
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Top Contributors</div>
                    {wsSummary.top_contributors.map((c,i) => (
                      <div key={i} style={{ display:"flex", justifyContent:"space-between", padding:"4px 0", fontSize:12 }}>
                        <span>{["🥇","🥈","🥉"][i]} {c.email?.split("@")[0]}</span>
                        <span style={{ color:"#818cf8" }}>{c.events} events</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Polls tab */}
            {tab === 26 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Create Poll</div>
                    <input value={pollQ} onChange={e=>setPollQ(e.target.value)} placeholder="Question" style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
                    <textarea value={pollOpts} onChange={e=>setPollOpts(e.target.value)} rows={3} placeholder="One option per line" style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none", marginBottom:8 }} />
                    <button onClick={async()=>{if(!pollQ.trim())return;const opts=pollOpts.split("\n").map(o=>o.trim()).filter(Boolean);const{data}=await api.post(`/workspaces/${selected.id}/polls`,{question:pollQ,options:opts});setPolls(p=>[...p,{...data,total_votes:0,user_voted:false}]);setPollQ("");flash(true,"Poll created");}} style={S.btn}>+ Create Poll</button>
                  </div>
                )}
                {polls.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No polls yet.</p>}
                {polls.map(p => (
                  <div key={p.id} style={S.card}>
                    <div style={{ display:"flex", justifyContent:"space-between" }}>
                      <div style={{ fontSize:14, fontWeight:600 }}>{p.question}</div>
                      <div style={{ display:"flex", gap:6 }}>
                        {!p.closed && (detail.role==="owner"||detail.role==="admin") && <button onClick={async()=>{await api.post(`/workspaces/${selected.id}/polls/${p.id}/close`);const{data}=await api.get(`/workspaces/${selected.id}/polls`);setPolls(data.polls||[]);}} style={{ ...S.btnRed, padding:"3px 8px", fontSize:11 }}>Close</button>}
                        {p.closed && <span style={S.badge("#52525b")}>Closed</span>}
                      </div>
                    </div>
                    <div style={{ marginTop:10 }}>
                      {p.options?.map(opt => {
                        const votes = p.votes?.[opt]?.length || 0;
                        const total = p.total_votes || 1;
                        const pct = Math.round(votes/total*100);
                        return (
                          <div key={opt} style={{ marginBottom:8 }}>
                            <div style={{ display:"flex", justifyContent:"space-between", fontSize:12, marginBottom:3 }}>
                              <button onClick={async()=>{if(p.closed)return;await api.post(`/workspaces/${selected.id}/polls/${p.id}/vote`,{option:opt});const{data}=await api.get(`/workspaces/${selected.id}/polls`);setPolls(data.polls||[]);}} style={{ background:"none", border:"none", color:"#e4e4e7", cursor:p.closed?"default":"pointer", fontSize:12, textAlign:"left" }}>{opt}</button>
                              <span style={{ color:"#818cf8" }}>{votes} ({pct}%)</span>
                            </div>
                            <div style={{ height:4, borderRadius:2, background:"rgba(255,255,255,.06)" }}>
                              <div style={{ height:"100%", borderRadius:2, width:`${pct}%`, background:"#6366f1", transition:"width .3s" }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    <div style={{ fontSize:10, color:"#3f3f46", marginTop:6 }}>{p.total_votes} votes · by {p.created_by?.split("@")[0]}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Contracts tab */}
            {tab === 27 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>New Data Contract</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                      <input value={contractName} onChange={e=>setContractName(e.target.value)} placeholder="Contract name" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <input value={contractSla} onChange={e=>setContractSla(e.target.value)} placeholder="SLA (e.g. Updated daily)" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <button onClick={async()=>{if(!contractName.trim())return;const{data}=await api.post(`/workspaces/${selected.id}/contracts`,{name:contractName,sla:contractSla});setContracts(p=>[...p,data]);setContractName("");setContractSla("");flash(true,"Contract created");}} style={S.btn}>+ Create</button>
                    </div>
                  </div>
                )}
                {contracts.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No data contracts yet.</p>}
                {contracts.map(c => (
                  <div key={c.id} style={S.card}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                      <div>
                        <div style={{ fontSize:13, fontWeight:600 }}>{c.name}</div>
                        {c.sla && <div style={{ fontSize:11, color:"#52525b" }}>SLA: {c.sla}</div>}
                      </div>
                      <div style={{ display:"flex", gap:6 }}>
                        <span style={S.badge(c.status==="valid"?"#22c55e":c.status==="violated"?"#ef4444":"#6366f1")}>{c.status}</span>
                        <button onClick={async()=>{const{data}=await api.post(`/workspaces/${selected.id}/contracts/${c.id}/validate`);flash(data.valid,"Contract: "+(data.valid?"Valid":""+data.violations?.length+" violations"));const r=await api.get(`/workspaces/${selected.id}/contracts`);setContracts(r.data.contracts||[]);}} style={S.btn}>Validate</button>
                        <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/contracts/${c.id}`);setContracts(p=>p.filter(x=>x.id!==c.id));}} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                      </div>
                    </div>
                    {c.violations?.length > 0 && (
                      <div style={{ marginTop:8 }}>
                        {c.violations.map((v,i)=><div key={i} style={{ fontSize:11, color:"#f87171" }}>⚠ {v}</div>)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Integrations tab */}
            {tab === 28 && (
              <div>
                {(detail.role==="owner"||detail.role==="admin") ? (
                  <>
                    <div style={{ ...S.card, marginBottom:12 }}>
                      <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Add Integration</div>
                      <div style={{ display:"flex", gap:6, flexWrap:"wrap", alignItems:"center" }}>
                        <select value={intgType} onChange={e=>setIntgType(e.target.value)} style={{ ...S.select, width:90 }}>
                          {["slack","teams","discord","email","custom"].map(t=><option key={t}>{t}</option>)}
                        </select>
                        <input value={intgName} onChange={e=>setIntgName(e.target.value)} placeholder="Name" style={{ ...S.input, width:100 }} />
                        <input value={intgUrl} onChange={e=>setIntgUrl(e.target.value)} placeholder="Webhook URL" style={{ ...S.input, flex:1, minWidth:0 }} />
                        <button onClick={async()=>{if(!intgUrl.trim())return;const{data}=await api.post(`/workspaces/${selected.id}/integrations`,{type:intgType,name:intgName,webhook_url:intgUrl});setIntegrations(p=>[...p,data]);setIntgUrl("");setIntgName("");flash(true,"Integration added");}} style={S.btn}>+ Add</button>
                      </div>
                    </div>
                    {integrations.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No integrations configured.</p>}
                    {integrations.map(i => (
                      <div key={i.id} style={{ ...S.card, display:"flex", alignItems:"center", gap:10 }}>
                        <div style={{ fontSize:20 }}>{i.type==="slack"?"💬":i.type==="teams"?"🟦":i.type==="discord"?"🎮":i.type==="email"?"📧":"🔗"}</div>
                        <div style={{ flex:1 }}>
                          <div style={{ fontSize:13, fontWeight:600 }}>{i.name}</div>
                          <div style={{ fontSize:11, color:"#52525b" }}>{i.webhook_url} · {i.deliveries||0} deliveries</div>
                        </div>
                        <button onClick={async()=>{const{data}=await api.post(`/workspaces/${selected.id}/integrations/${i.id}/test`);flash(data.status<400||data.status===0,"Test: "+data.message);}} style={S.btn}>Test</button>
                        <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/integrations/${i.id}`);setIntegrations(p=>p.filter(x=>x.id!==i.id));}} style={{ ...S.btnRed, padding:"4px 8px" }}>✕</button>
                      </div>
                    ))}
                  </>
                ) : <p style={{ color:"#52525b", fontSize:13 }}>Only owner or admin can manage integrations.</p>}
              </div>
            )}

            {/* Permissions tab */}
            {tab === 29 && (
              <div>
                {(detail.role==="owner"||detail.role==="admin") ? (
                  <div>
                    <div style={{ fontSize:12, color:"#52525b", marginBottom:12 }}>Fine-grained per-member feature access</div>
                    <div style={{ overflowX:"auto" }}>
                      <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11 }}>
                        <thead>
                          <tr>
                            <th style={{ padding:"6px 10px", textAlign:"left", color:"#52525b", borderBottom:"1px solid rgba(255,255,255,.06)" }}>Member</th>
                            {permMatrix.features?.map(f=><th key={f} style={{ padding:"6px 8px", color:"#52525b", borderBottom:"1px solid rgba(255,255,255,.06)", textTransform:"capitalize" }}>{f}</th>)}
                          </tr>
                        </thead>
                        <tbody>
                          {permMatrix.matrix?.map(m=>(
                            <tr key={m.email}>
                              <td style={{ padding:"6px 10px", color:"#e4e4e7", borderBottom:"1px solid rgba(255,255,255,.04)" }}>{m.email?.split("@")[0]} <span style={S.badge(ROLE_COLOR[m.role]||"#52525b")}>{m.role}</span></td>
                              {permMatrix.features?.map(f=>(
                                <td key={f} style={{ padding:"6px 8px", textAlign:"center", borderBottom:"1px solid rgba(255,255,255,.04)" }}>
                                  <input type="checkbox" checked={m.permissions?.[f]||false} onChange={async(e)=>{await api.patch(`/workspaces/${selected.id}/permissions`,{user_email:m.email,permissions:{[f]:e.target.checked}});const{data}=await api.get(`/workspaces/${selected.id}/permissions`);setPermMatrix(data);}} style={{ accentColor:"#6366f1" }} />
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : <p style={{ color:"#52525b", fontSize:13 }}>Only owner or admin can manage permissions.</p>}
              </div>
            )}

            {/* Changelog tab */}
            {tab === 30 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Add Changelog Entry</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap", marginBottom:8 }}>
                      <input value={clVersion} onChange={e=>setClVersion(e.target.value)} placeholder="v1.2.0" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <input value={clTitle} onChange={e=>setClTitle(e.target.value)} placeholder="Title" style={{ ...S.input, flex:3, minWidth:0 }} />
                    </div>
                    <textarea value={clBody} onChange={e=>setClBody(e.target.value)} rows={3} placeholder="What changed?" style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none", marginBottom:8 }} />
                    <button onClick={async()=>{if(!clVersion||!clTitle)return;const{data}=await api.post(`/workspaces/${selected.id}/changelog`,{version:clVersion,title:clTitle,body:clBody});setChangelog(p=>[data,...p]);setClVersion("");setClTitle("");setClBody("");flash(true,"Entry added");}} style={S.btn}>+ Add Entry</button>
                  </div>
                )}
                {changelog.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No changelog entries yet.</p>}
                {changelog.map(e => (
                  <div key={e.id} style={S.card}>
                    <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                      <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                        <span style={S.badge("#6366f1")}>{e.version}</span>
                        <span style={{ fontSize:13, fontWeight:600 }}>{e.title}</span>
                        {e.breaking && <span style={S.badge("#ef4444")}>BREAKING</span>}
                      </div>
                      {(detail.role==="owner"||detail.role==="admin") && <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/changelog/${e.id}`);setChangelog(p=>p.filter(x=>x.id!==e.id));}} style={{ background:"none", border:"none", color:"#52525b", cursor:"pointer" }}>✕</button>}
                    </div>
                    <div style={{ fontSize:12, color:"#a1a1aa", marginTop:6 }}>{e.body}</div>
                    <div style={{ fontSize:10, color:"#3f3f46", marginTop:4 }}>by {e.author?.split("@")[0]} · {e.ts?.slice(0,10)}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Metrics tab */}
            {tab === 31 && (
              <div>
                {detail.role !== "viewer" && (
                  <div style={{ ...S.card, marginBottom:12 }}>
                    <div style={{ fontSize:13, fontWeight:600, marginBottom:10 }}>Add Metric</div>
                    <div style={{ display:"flex", gap:6, flexWrap:"wrap" }}>
                      <input value={metricName} onChange={e=>setMetricName(e.target.value)} placeholder="Metric name" style={{ ...S.input, flex:2, minWidth:0 }} />
                      <input value={metricVal} onChange={e=>setMetricVal(e.target.value)} placeholder="Value" type="number" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <input value={metricUnit} onChange={e=>setMetricUnit(e.target.value)} placeholder="Unit" style={{ ...S.input, flex:1, minWidth:0 }} />
                      <button onClick={async()=>{if(!metricName||!metricVal)return;const{data}=await api.post(`/workspaces/${selected.id}/metrics`,{name:metricName,value:parseFloat(metricVal),unit:metricUnit});setMetrics(p=>[...p,data]);setMetricName("");setMetricVal("");flash(true,"Metric added");}} style={S.btn}>+ Add</button>
                    </div>
                  </div>
                )}
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))", gap:10 }}>
                  {metrics.map(m => (
                    <div key={m.id} style={S.card}>
                      <div style={{ display:"flex", justifyContent:"space-between" }}>
                        <div style={{ fontSize:11, color:"#52525b" }}>{m.name}</div>
                        <span style={{ fontSize:14 }}>{m.trend==="up"?"📈":m.trend==="down"?"📉":"➡"}</span>
                      </div>
                      <div style={{ fontSize:26, fontWeight:700, color:"#818cf8", margin:"6px 0" }}>{m.value}{m.unit}</div>
                      <div style={{ fontSize:10, color:"#3f3f46" }}>Updated {m.ts?.slice(11,16)}</div>
                      {detail.role !== "viewer" && (
                        <div style={{ display:"flex", gap:4, marginTop:8 }}>
                          <input type="number" placeholder="New value" style={{ ...S.input, flex:1, fontSize:11 }} id={`metric-${m.id}`} />
                          <button onClick={async()=>{const v=document.getElementById(`metric-${m.id}`).value;if(!v)return;const{data}=await api.patch(`/workspaces/${selected.id}/metrics/${m.id}`,{name:m.name,value:parseFloat(v),unit:m.unit});setMetrics(p=>p.map(x=>x.id===m.id?data:x));}} style={{ ...S.btn, padding:"4px 6px", fontSize:10 }}>↑</button>
                          <button onClick={async()=>{await api.delete(`/workspaces/${selected.id}/metrics/${m.id}`);setMetrics(p=>p.filter(x=>x.id!==m.id));}} style={{ ...S.btnRed, padding:"4px 6px", fontSize:10 }}>✕</button>
                        </div>
                      )}
                    </div>
                  ))}
                  {metrics.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No metrics tracked yet.</p>}
                </div>
              </div>
            )}

            {/* Digest tab */}
            {tab === 32 && digest && (
              <div>
                <div style={{ ...S.card, marginBottom:12 }}>
                  <div style={{ fontSize:14, fontWeight:700, marginBottom:4 }}>Weekly Digest — {digest.workspace}</div>
                  <div style={{ fontSize:11, color:"#52525b" }}>{digest.period}</div>
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))", gap:10, marginBottom:16 }}>
                  {[["Events",digest.highlights?.total_events,"#6366f1"],["Tasks Done",digest.highlights?.tasks_completed,"#22c55e"],["Active Tasks",digest.highlights?.tasks_active,"#f59e0b"],["Goals Achieved",digest.highlights?.goals_achieved,"#10b981"],["Datasets Shared",digest.highlights?.new_datasets,"#8b5cf6"],["Notebooks",digest.highlights?.new_notebooks,"#0ea5e9"],["Chat Messages",digest.highlights?.chat_messages,"#ec4899"]].map(([l,v,c])=>(
                    <div key={l} style={{ ...S.card, textAlign:"center", marginBottom:0 }}>
                      <div style={{ fontSize:22, fontWeight:700, color:c }}>{v??0}</div>
                      <div style={{ fontSize:11, color:"#52525b", marginTop:2 }}>{l}</div>
                    </div>
                  ))}
                </div>
                {digest.top_contributors?.length > 0 && (
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Top Contributors This Week</div>
                    {digest.top_contributors.map((c,i)=>(
                      <div key={i} style={{ display:"flex", justifyContent:"space-between", padding:"4px 0", fontSize:12 }}>
                        <span>{["🥇","🥈","🥉"][i]} {c.email?.split("@")[0]}</span>
                        <span style={{ color:"#818cf8" }}>{c.events} events</span>
                      </div>
                    ))}
                  </div>
                )}
                {digest.completed_tasks?.length > 0 && (
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Completed Tasks</div>
                    {digest.completed_tasks.map((t,i)=><div key={i} style={{ fontSize:12, color:"#a1a1aa", padding:"3px 0" }}>✅ {t.title}</div>)}
                  </div>
                )}
                {digest.recent_announcements?.length > 0 && (
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Recent Announcements</div>
                    {digest.recent_announcements.map((a,i)=><div key={i} style={{ fontSize:12, color:"#a1a1aa", padding:"3px 0" }}>📢 {a.title}</div>)}
                  </div>
                )}
              </div>
            )}

            {/* Activity tab */}
            {tab === 33 && (
              <div>
                <div style={{ fontSize:12, color:"#52525b", marginBottom:10 }}>{activity.length} events logged</div>
                {activity.length === 0 && <p style={{ color:"#52525b", fontSize:13 }}>No activity yet.</p>}
                {activity.map((e,i) => (
                  <div key={i} style={{ display:"flex", gap:10, padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,.04)" }}>
                    <div style={{ fontSize:10, color:"#3f3f46", minWidth:0 }}>{e.ts?.slice(11,16)}</div>
                    <div style={{ flex:1 }}>
                      <span style={{ fontSize:12, color:"#818cf8" }}>{e.user?.split("@")[0]}</span>
                      <span style={{ fontSize:12, color:"#52525b" }}> · {e.event?.replace(/_/g," ")}</span>
                      {e.detail && <div style={{ fontSize:11, color:"#3f3f46", marginTop:2 }}>{e.detail}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Analytics tab */}
            {tab === 34 && wsAnalytics && (
              <div>
                <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(140px,1fr))", gap:10, marginBottom:16 }}>
                  {[["Total Members", wsAnalytics.total_members,"#6366f1"],["Active (7d)", wsAnalytics.active_members_7d,"#10b981"],["Total Events", wsAnalytics.total_events,"#f59e0b"],["Shared Datasets", wsAnalytics.shared_datasets,"#8b5cf6"],["Pinned Charts", wsAnalytics.pinned_charts,"#0ea5e9"]].map(([l,v,c])=>(
                    <div key={l} style={{ ...S.card, textAlign:"center", marginBottom:0 }}>
                      <div style={{ fontSize:22, fontWeight:700, color:c }}>{v}</div>
                      <div style={{ fontSize:11, color:"#52525b", marginTop:2 }}>{l}</div>
                    </div>
                  ))}
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Role Distribution</div>
                    {Object.entries(wsAnalytics.role_distribution||{}).map(([r,c])=>(
                      <div key={r} style={{ display:"flex", justifyContent:"space-between", padding:"4px 0", fontSize:12 }}>
                        <span style={{ color:ROLE_COLOR[r]||"#52525b" }}>{r}</span>
                        <span style={{ color:"#f4f4f5" }}>{c}</span>
                      </div>
                    ))}
                  </div>
                  <div style={S.card}>
                    <div style={{ fontSize:12, fontWeight:600, marginBottom:8 }}>Event Breakdown</div>
                    {Object.entries(wsAnalytics.event_breakdown||{}).slice(0,6).map(([e,c])=>(
                      <div key={e} style={{ display:"flex", justifyContent:"space-between", padding:"4px 0", fontSize:12 }}>
                        <span style={{ color:"#71717a" }}>{e.replace(/_/g," ")}</span>
                        <span style={{ color:"#f4f4f5" }}>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Settings tab */}
            {tab === 35 && (
              <div>
                {detail.role === "owner" && (
                  <>
                    <div style={S.card}>
                      <div style={{ fontSize:13, fontWeight:600, marginBottom:12 }}>Workspace Settings</div>
                      <label style={S.label}>Name</label>
                      <input value={editName} onChange={e=>setEditName(e.target.value)} style={{ ...S.input, width:"100%", boxSizing:"border-box", marginBottom:8, minWidth:0 }} />
                      <label style={S.label}>Description</label>
                      <textarea value={editDesc} onChange={e=>setEditDesc(e.target.value)} rows={2} style={{ ...S.input, width:"100%", boxSizing:"border-box", resize:"none", marginBottom:12 }} />
                      <button onClick={updateSettings} style={S.btn}>💾 Save Changes</button>
                    </div>
                    <div style={S.card}>
                      <div style={{ fontSize:13, fontWeight:600, marginBottom:12, color:"#f59e0b" }}>⚠ Transfer Ownership</div>
                      <div style={{ fontSize:12, color:"#52525b", marginBottom:8 }}>Transfer to an existing member. You'll become an admin.</div>
                      <div style={{ display:"flex", gap:8 }}>
                        <input value={transferEmail} onChange={e=>setTransferEmail(e.target.value)} placeholder="member@email.com" style={{ ...S.input, flex:1 }} />
                        <button onClick={transferOwnership} style={{ ...S.btnRed }}>Transfer</button>
                      </div>
                    </div>
                    <div style={S.card}>
                      <div style={{ fontSize:13, fontWeight:600, marginBottom:8, color:"#ef4444" }}>🗑 Danger Zone</div>
                      <button onClick={()=>deleteWs(selected.id)} style={S.btnRed}>Delete Workspace</button>
                    </div>
                  </>
                )}
                {detail.role !== "owner" && <p style={{ color:"#52525b", fontSize:13 }}>Only the workspace owner can change settings.</p>}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
