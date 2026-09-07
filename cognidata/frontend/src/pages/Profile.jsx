import { useEffect, useState, Component } from "react";
import { api } from "../api/client";
import useAuth from "../store/auth";
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

const TABS = ["👤 Profile","🔒 Security / 2FA","🔔 Notifications","🔑 API Keys","📋 Activity","💬 Feedback"];

export default function Profile() {
  const [tab, setTab] = useState(0);
  const { getPayload } = useAuth();
  const p = getPayload();
  const [activity, setActivity] = useState([]);
  const [profileData, setProfileData] = useState(null);

  useEffect(() => {
    api.get("/profile/activity").then(({ data }) => setActivity(data || [])).catch(() => {});
    api.get("/profile/me").then(({ data }) => setProfileData(data)).catch(() => {});
  }, []);

  const totalActions = activity.length;
  const datasetsUploaded = activity.filter(a => String(a.action||"").toLowerCase().includes("upload")).length;
  const aiQueries = activity.filter(a => String(a.action||"").toLowerCase().includes("ai_query")).length;
  const reportsGenerated = activity.filter(a => String(a.action||"").toLowerCase().includes("report")).length;

  const displayName = profileData?.name || localStorage.getItem("display_name") || p.sub || "User";

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.avatar}>{displayName.slice(0,2).toUpperCase()}</div>
        <div>
          <div style={S.name}>{displayName}</div>
          <div style={{fontSize:12,color:"#52525b",marginTop:1}}>{p.sub}</div>
          <div style={S.role}>{p.role==="admin"?"Administrator":"Member"}</div>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display:"flex",gap:12,marginBottom:16,flexWrap:"wrap" }}>
        {[
          ["Total Actions", totalActions, "#6366f1"],
          ["Datasets Uploaded", datasetsUploaded, "#22c55e"],
          ["AI Queries", aiQueries, "#f59e0b"],
          ["Reports Generated", reportsGenerated, "#ec4899"],
        ].map(([label, value, color]) => (
          <div key={label} style={{ flex:"1 1 120px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"14px 18px" }}>
            <div style={{ fontSize:22,fontWeight:700,color }}>{value}</div>
            <div style={{ fontSize:11,color:"#52525b",marginTop:3 }}>{label}</div>
          </div>
        ))}
      </div>

      <div style={S.tabs}>
        {TABS.map((t,i) => (
          <button key={t} onClick={() => setTab(i)} style={{...S.tab, borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent", color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>

      {tab === 0 && <ProfileTab payload={p} />}
      {tab === 1 && <SecurityTab />}
      {tab === 2 && <NotificationsTab />}
      {tab === 3 && <APIKeysTab />}
      {tab === 4 && <ActivityTab />}
      {tab === 5 && <FeedbackTab />}
    </div>
    </ErrorBoundary>
  );
}

function ProfileTab({ payload }) {
  const [displayName, setDisplayName] = useState("");
  const [saved, setSaved] = useState(false);
  const [loading, setLoad] = useState(false);

  useEffect(() => {
    api.get("/profile/me").then(({data}) => setDisplayName(data.name || "")).catch(() => {
      setDisplayName(localStorage.getItem("display_name") || "");
    });
  }, []);

  const save = async () => {
    setLoad(true);
    try {
      await api.post("/profile/name", { name: displayName });
      localStorage.setItem("display_name", displayName);
      setSaved(true); setTimeout(() => setSaved(false), 2000);
    } catch {
      localStorage.setItem("display_name", displayName);
      setSaved(true); setTimeout(() => setSaved(false), 2000);
    } finally { setLoad(false); }
  };

  return (
    <div style={S.card}>
      <div style={S.field}><span style={S.fieldLabel}>Email</span><span style={S.fieldVal}>{payload.sub}</span></div>
      <div style={S.field}><span style={S.fieldLabel}>Role</span><span style={S.fieldVal}>
        <span style={{padding:"2px 10px",borderRadius:20,background:payload.role==="admin"?"rgba(99,102,241,.15)":"rgba(255,255,255,.05)",color:payload.role==="admin"?"#818cf8":"#71717a",fontSize:12}}>{payload.role}</span>
      </span></div>
      <div style={S.field}><span style={S.fieldLabel}>Member since</span><span style={S.fieldVal}>2024</span></div>
      <div style={{marginTop:8}}>
        <h3 style={{...S.sectionTitle,marginBottom:8}}>Display Name</h3>
        {saved && <div style={{...S.alert,background:"rgba(16,185,129,.1)",borderColor:"rgba(16,185,129,.3)",color:"#34d399",marginBottom:8}}>✓ Display name saved</div>}
        <div style={{display:"flex",gap:10}}>
          <input value={displayName} onChange={e=>setDisplayName(e.target.value)} placeholder="Enter display name…"
            style={{...S.input,flex:1}} />
          <button onClick={save} disabled={loading} style={S.btn}>
            {loading?<span className="spinner" style={{width:14,height:14}}/>:"💾 Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

function SecurityTab() {
  const [old, setOld] = useState(""); const [nw, setNw] = useState(""); const [msg, setMsg] = useState(null);
  const [twofa, setTwofa] = useState(null); // {enabled, secret, qr_uri}
  const [code, setCode]   = useState("");
  const [disCode, setDisCode] = useState("");
  const { getPayload } = useAuth();

  useEffect(() => {
    // Check 2FA status from token
    const p = getPayload();
    setTwofa({ enabled: false }); // default; will be updated from profile endpoint
    api.get("/profile/2fa-status").then(({ data }) => setTwofa(data)).catch(() => {});
  }, []);

  const change = async () => {
    try { await api.post("/profile/change-password", { old_password:old, new_password:nw }); setMsg({ok:true,t:"Password changed"}); setOld(""); setNw(""); }
    catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Failed"}); }
  };

  const setup2fa = async () => {
    try {
      const { data } = await api.post("/auth/2fa/setup");
      setTwofa({ enabled:false, secret:data.secret, qr_uri:data.qr_uri });
    } catch(e) { setMsg({ok:false,t:"Failed to setup 2FA"}); }
  };

  const confirm2fa = async () => {
    try {
      await api.post("/auth/2fa/confirm", { code });
      setTwofa(t => ({...t, enabled:true, secret:null, qr_uri:null}));
      setCode(""); setMsg({ok:true,t:"2FA enabled successfully"});
    } catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Invalid code"}); }
  };

  const disable2fa = async () => {
    try {
      await api.post("/auth/2fa/disable", { code: disCode });
      setTwofa({ enabled:false }); setDisCode(""); setMsg({ok:true,t:"2FA disabled"});
    } catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Invalid code"}); }
  };

  return (
    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      <div style={S.card}>
        <h3 style={S.sectionTitle}>Change Password</h3>
        {msg && <div style={{...S.alert,background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:msg.ok?"#34d399":"#f87171",marginBottom:12}}>{msg.t}</div>}
        <input type="password" placeholder="Current password" value={old} onChange={e=>setOld(e.target.value)} style={S.input} />
        <input type="password" placeholder="New password (min 6 chars)" value={nw} onChange={e=>setNw(e.target.value)} style={S.input} />
        <button onClick={change} style={S.btn}>🔒 Change Password</button>
      </div>

      <div style={S.card}>
        <h3 style={S.sectionTitle}>Two-Factor Authentication (2FA)</h3>
        {twofa?.enabled ? (
          <div>
            <div style={{padding:"10px 14px",borderRadius:10,background:"rgba(16,185,129,.08)",border:"1px solid rgba(16,185,129,.2)",color:"#34d399",fontSize:13,marginBottom:12}}>
              ✅ 2FA is enabled — your account is protected
            </div>
            <p style={{fontSize:12,color:"#52525b",marginBottom:10}}>Enter your current TOTP code to disable 2FA:</p>
            <div style={{display:"flex",gap:10}}>
              <input type="text" inputMode="numeric" maxLength={6} placeholder="000000" value={disCode} onChange={e=>setDisCode(e.target.value.replace(/\D/g,""))}
                style={{...S.input,letterSpacing:"0.3em",textAlign:"center",fontFamily:"monospace",width:140}} />
              <button onClick={disable2fa} disabled={disCode.length!==6}
                style={{...S.btn,background:"rgba(239,68,68,.15)",border:"1px solid rgba(239,68,68,.3)",color:"#f87171"}}>Disable 2FA</button>
            </div>
          </div>
        ) : twofa?.qr_uri ? (
          <div>
            <div style={{padding:"10px 14px",borderRadius:10,background:"rgba(245,158,11,.08)",border:"1px solid rgba(245,158,11,.2)",color:"#f59e0b",fontSize:13,marginBottom:12}}>
              ⚠️ Scan the QR code with your authenticator app, then verify
            </div>
            <div style={{background:"#fff",padding:12,borderRadius:10,display:"inline-block",marginBottom:12}}>
              <img src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(twofa.qr_uri)}`} alt="QR Code" width={160} height={160} />
            </div>
            <p style={{fontSize:12,color:"#52525b",marginBottom:4}}>Manual key:</p>
            <code style={{fontSize:11,color:"#a5f3fc",background:"#0f172a",padding:"4px 10px",borderRadius:6,display:"block",marginBottom:12,wordBreak:"break-all"}}>{twofa.secret}</code>
            <div style={{display:"flex",gap:10}}>
              <input type="text" inputMode="numeric" maxLength={6} placeholder="000000" value={code} onChange={e=>setCode(e.target.value.replace(/\D/g,""))}
                style={{...S.input,letterSpacing:"0.3em",textAlign:"center",fontFamily:"monospace",width:140}} />
              <button onClick={confirm2fa} disabled={code.length!==6} style={S.btn}>✓ Verify & Enable</button>
            </div>
          </div>
        ) : (
          <div>
            <div style={{padding:"10px 14px",borderRadius:10,background:"rgba(245,158,11,.08)",border:"1px solid rgba(245,158,11,.2)",color:"#f59e0b",fontSize:13,marginBottom:12}}>
              ⚠️ 2FA is disabled — enable it for extra security
            </div>
            <button onClick={setup2fa} style={S.btn}>🔐 Setup 2FA</button>
          </div>
        )}
      </div>
    </div>
  );
}

function NotificationsTab() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/profile/notifications").then(({data})=>setData(data)).catch(()=>{}); }, []);
  const markRead = async () => { await api.post("/profile/notifications/read"); setData(d=>({...d,unread:0,notifications:d.notifications.map(n=>({...n,read:true}))})); };
  return (
    <div style={S.card}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
        <h3 style={S.sectionTitle}>Notifications {data?.unread>0 && <span style={{fontSize:11,background:"#6366f1",color:"#fff",borderRadius:20,padding:"2px 8px",marginLeft:8}}>{data.unread}</span>}</h3>
        {data?.unread>0 && <button onClick={markRead} style={{...S.btn,padding:"5px 12px",fontSize:11}}>Mark all read</button>}
      </div>
      {data?.notifications?.length ? data.notifications.map(n=>(
        <div key={n.id} style={{...S.notif,opacity:n.read?0.5:1}}>
          <div style={{fontSize:13,fontWeight:500,color:"#f4f4f5"}}>{n.title}</div>
          <div style={{fontSize:12,color:"#71717a",marginTop:2}}>{n.message}</div>
          <div style={{fontSize:10,color:"#3f3f46",marginTop:4}}>{new Date(n.ts).toLocaleString()}</div>
        </div>
      )) : <p style={{color:"#52525b",fontSize:13}}>No notifications.</p>}
    </div>
  );
}

function APIKeysTab() {
  const [keys, setKeys] = useState([]); const [name, setName] = useState(""); const [newKey, setNewKey] = useState(null);
  useEffect(() => { api.get("/profile/keys").then(({data})=>setKeys(data)).catch(()=>{}); }, []);
  const create = async () => {
    const {data} = await api.post("/profile/keys", { name: name||"default" });
    setNewKey(data.key); setName("");
    api.get("/profile/keys").then(({data})=>setKeys(data));
  };
  return (
    <div style={S.card}>
      <h3 style={S.sectionTitle}>API Keys <span style={{fontSize:11,color:"#52525b"}}>(aida_ prefix)</span></h3>
      {newKey && <div style={{...S.alert,background:"rgba(16,185,129,.1)",borderColor:"rgba(16,185,129,.3)",color:"#34d399",marginBottom:12,wordBreak:"break-all"}}>✓ New key: {newKey}<br/><span style={{fontSize:11}}>Copy it now — it won't be shown again.</span></div>}
      <div style={{display:"flex",gap:10,marginBottom:16}}>
        <input placeholder="Key name" value={name} onChange={e=>setName(e.target.value)} style={{...S.input,flex:1}} />
        <button onClick={create} style={S.btn}>+ Generate</button>
      </div>
      {keys.length ? <Table data={keys} /> : <p style={{color:"#52525b",fontSize:13}}>No API keys yet.</p>}
    </div>
  );
}

function ActivityTab() {
  const [logs, setLogs] = useState([]);
  useEffect(() => { api.get("/profile/activity").then(({data})=>setLogs(data)).catch(()=>{}); }, []);
  return (
    <div style={S.card}>
      <h3 style={S.sectionTitle}>Recent Activity</h3>
      {logs.length ? <Table data={logs.map(l=>({time:new Date(l.ts).toLocaleString(),action:l.action,detail:String(l.detail||"").slice(0,60)}))} /> : <p style={{color:"#52525b",fontSize:13}}>No activity yet.</p>}
    </div>
  );
}

function FeedbackTab() {
  const [msg, setMsg] = useState(""); const [rating, setRating] = useState(5); const [sent, setSent] = useState(false);
  const submit = async () => {
    if (!msg.trim()) return;
    await api.post("/profile/feedback", { message:msg, rating, category:"general" });
    setSent(true); setMsg("");
  };
  return (
    <div style={S.card}>
      <h3 style={S.sectionTitle}>Send Feedback</h3>
      {sent && <div style={{...S.alert,background:"rgba(16,185,129,.1)",borderColor:"rgba(16,185,129,.3)",color:"#34d399",marginBottom:12}}>✓ Thank you for your feedback!</div>}
      <div style={{display:"flex",gap:6,marginBottom:12}}>
        {[1,2,3,4,5].map(s=>(
          <button key={s} onClick={()=>setRating(s)} style={{fontSize:20,background:"transparent",border:"none",cursor:"pointer",opacity:s<=rating?1:0.3}}>⭐</button>
        ))}
        <span style={{fontSize:13,color:"#71717a",alignSelf:"center",marginLeft:4}}>{rating}/5</span>
      </div>
      <textarea value={msg} onChange={e=>setMsg(e.target.value)} rows={4} placeholder="Share your thoughts…"
        style={{...S.input,resize:"none",width:"100%",boxSizing:"border-box",marginBottom:10}} />
      <button onClick={submit} disabled={!msg.trim()} style={S.btn}>📤 Submit Feedback</button>
    </div>
  );
}

const S = {
  page:        { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  header:      { display:"flex", alignItems:"center", gap:14, marginBottom:20 },
  avatar:      { width:52, height:52, borderRadius:"50%", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, fontWeight:700, color:"#fff" },
  name:        { fontSize:16, fontWeight:600, color:"#f4f4f5" },
  role:        { fontSize:12, color:"#52525b", marginTop:2 },
  tabs:        { display:"flex", gap:4, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:         { padding:"8px 14px", background:"transparent", border:"none", fontSize:13, fontWeight:500, cursor:"pointer" },
  card:        { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"20px 22px", display:"flex", flexDirection:"column", gap:10, maxWidth:600 },
  sectionTitle:{ fontSize:14, fontWeight:600, color:"#a1a1aa", margin:0 },
  field:       { display:"flex", justifyContent:"space-between", padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,.04)" },
  fieldLabel:  { fontSize:13, color:"#52525b" },
  fieldVal:    { fontSize:13, color:"#f4f4f5" },
  input:       { padding:"10px 14px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  btn:         { padding:"10px 18px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", alignSelf:"flex-start", display:"flex", alignItems:"center", gap:8 },
  alert:       { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
  notif:       { padding:"10px 12px", background:"rgba(255,255,255,.03)", borderRadius:8, border:"1px solid rgba(255,255,255,.05)" },
};
