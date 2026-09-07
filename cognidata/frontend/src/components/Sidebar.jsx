import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useEffect, useState, useRef } from "react";
import { api } from "../api/client";
import useAuth from "../store/auth";

const NAV = [
  { to:"/chat",       icon:"💬", label:"AI Chat",            sub:"Ask your data" },
  { to:"/upload",     icon:"📤", label:"Upload Dataset",     sub:"CSV · Excel · JSON" },
  { to:"/dashboard",  icon:"📊", label:"Dashboard",          sub:"7 tabs · KPIs · Charts" },
  { to:"/analyst",    icon:"🧠", label:"AI Analyst",         sub:"SQL · RAG · Analysis" },
  { to:"/analytics",  icon:"🔬", label:"Advanced Analytics", sub:"Stats · Cluster · TS" },
  { to:"/maps",       icon:"🗺️", label:"Advanced Maps",       sub:"Choropleth · H3 · Flow" },
  { to:"/alerts",     icon:"🚨", label:"KPI Alerts",           sub:"Threshold rules · history" },
  { to:"/actions",    icon:"⚡", label:"Action Layer",          sub:"Webhooks · Slack · Auto-fire" },
  { to:"/ingest",     icon:"📡", label:"Live Ingest",           sub:"Stream data · webhooks" },
  { to:"/realtime",   icon:"📊", label:"Real-Time Dashboard",    sub:"SSE · Live charts · KPIs" },
  { to:"/deep-analyst", icon:"🧠", label:"Deep Analyst",        sub:"Reasoning · Insights · Decide" },
  { to:"/globe",      icon:"🌍", label:"3D Globe",              sub:"WebGL · Geo · Data spikes" },
  { to:"/federated",  icon:"🔌", label:"Federated Query",       sub:"Postgres · MySQL · BigQuery" },
  { to:"/semantic",   icon:"🧮", label:"Semantic Metrics",      sub:"Define · compute · lineage" },
  { to:"/pipeline",   icon:"⚙️", label:"Pipeline Builder",      sub:"AI-generated ETL steps" },
  { to:"/catalog",    icon:"📚", label:"Data Catalog",          sub:"Auto-doc · quality · lineage" },
  { to:"/esg",        icon:"🌱", label:"ESG Dashboard",          sub:"Carbon · Diversity · CSRD" },
  { to:"/splat",      icon:"✨", label:"Gaussian Splatting",      sub:"WebGL · Three.js · 3D geo" },
  { to:"/automl",     icon:"🤖", label:"AutoML Studio",      sub:"Train · SHAP · Predict" },
  { to:"/geo",        icon:"🌍", label:"Geo Intelligence",   sub:"15 cities · live" },
  { to:"/viz",        icon:"📡", label:"Live Viz",           sub:"11 modes · 3D" },
  { to:"/reports",    icon:"📈", label:"Reports",            sub:"PDF · Export · Schedule" },
  { to:"/roadmap",    icon:"🗺️", label:"Roadmap",            sub:"AI planning" },
  { to:"/workspaces", icon:"🏢", label:"Workspaces",         sub:"Team · Roles · Invite" },
  { to:"/profile",    icon:"👤", label:"My Profile",         sub:"2FA · Keys · Activity" },
  { to:"/settings",   icon:"⚙️", label:"Settings",           sub:"API · SMTP · Prefs" },
  { to:"/help",       icon:"📖", label:"Feature Guide",       sub:"How to use everything" },
];

const TICKER_ITEMS = [
  "🧠 6 AI Agents","⚡ Real-time Analytics","📊 150+ Chart Types","🤖 AutoML Studio",
  "🛡️ Enterprise Security","🔮 GPT-4 Powered","📈 Live Dashboards","🔍 Anomaly Detection",
  "🌍 Geo Intelligence","📄 PDF Reports","🔐 2FA Auth","🏢 Team Workspaces",
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { clearToken, getPayload } = useAuth();
  const p = getPayload();
  const isAdmin = p?.role === "admin";
  const email   = p?.sub || "";
  const links   = isAdmin
    ? [...NAV, { to:"/debug", icon:"🛠️", label:"Debug Agent", sub:"System · Traces" },
               { to:"/devhub", icon:"💻", label:"Developer Hub", sub:"API · SDK · Webhooks" },
               { to:"/admin", icon:"🛡️", label:"Admin", sub:"System" }]
    : NAV;

  const [unread, setUnread]     = useState(0);
  const [provider, setProvider] = useState(null);
  const [dsInfo, setDsInfo]     = useState(null);
  const [activeDataset, setActiveDataset] = useState(null);
  const tickerRef = useRef(null);

  // Poll unread notifications count — only when tab is visible, every 60s
  useEffect(() => {
    const poll = () => {
      if (!document.hidden)
        api.get("/profile/notifications").then(({ data }) => setUnread(data.unread || 0)).catch(() => {});
    };
    poll();
    const t = setInterval(poll, 60000);
    return () => clearInterval(t);
  }, []);

  // Admin notification sound (admin only)
  const lastAlertCount = useRef(0);
  useEffect(() => {
    if (!isAdmin) return;
    const playSound = () => {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain); gain.connect(ctx.destination);
        osc.frequency.value = 880;
        osc.type = "sine";
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
        osc.start(ctx.currentTime); osc.stop(ctx.currentTime + 0.3);
      } catch {}
    };
    const poll = () => {
      api.get("/admin/alerts").then(({ data }) => {
        const count = Array.isArray(data) ? data.length : 0;
        if (count > lastAlertCount.current && lastAlertCount.current > 0) playSound();
        lastAlertCount.current = count;
      }).catch(() => {});
    };
    poll();
    const t = setInterval(poll, 60000);
    return () => clearInterval(t);
  }, [isAdmin]);

  // Detect active LLM provider from localStorage
  useEffect(() => {
    const gemini = localStorage.getItem("gemini_key");
    const aiml = localStorage.getItem("aiml_key");
    const oai  = localStorage.getItem("openai_key");
    if (gemini) setProvider({ label:"Gemini Flash", color:"#8b5cf6", dot:"🟣" });
    else if (aiml) setProvider({ label:"AIML API", color:"#0ea5e9", dot:"🔵" });
    else if (oai) setProvider({ label:"OpenAI", color:"#22c55e", dot:"🟢" });
    else setProvider(null);
  }, []);

  // Dataset status - poll every 10 seconds to catch uploads
  useEffect(() => {
    const fetchDatasetInfo = () => {
      // Get dataset info (rows/columns)
      api.get("/data/info").then(({ data }) => setDsInfo(data)).catch(() => setDsInfo(null));
      // Get active dataset name
      api.get("/data/datasets").then(({ data }) => setActiveDataset(data.active || null)).catch(() => {});
    };
    fetchDatasetInfo(); // Initial fetch
    const interval = setInterval(fetchDatasetInfo, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch {}
    clearToken(); navigate("/login");
  };

  return (
    <aside style={S.aside}>
      {/* Brand */}
      <div style={S.brand}>
        <div style={S.brandIcon}>✦</div>
        <div>
          <div style={S.brandName}>CogniData</div>
          <div style={S.brandTag}>AI Analytics Platform</div>
        </div>
      </div>

      {/* Marquee banner */}
      <div style={S.marqueeWrap}>
        <div ref={tickerRef} style={S.marquee}>
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((t, i) => (
            <span key={i} style={S.marqueeItem}>{t}<span style={S.marqueeDot}>·</span></span>
          ))}
        </div>
      </div>

      {/* Nav */}
      <nav style={S.nav}>
        {links.map(({ to, icon, label, sub }) => (
          <NavLink key={to} to={to} style={({ isActive }) => ({
            display:"flex", alignItems:"center", gap:8,
            padding:"7px 10px", borderRadius:"0 8px 8px 0",
            textDecoration:"none", transition:"all .15s",
            marginLeft:-10, paddingLeft:10,
            background: isActive ? "rgba(99,102,241,.15)" : "transparent",
            borderLeft: isActive ? "2px solid #818cf8" : "2px solid transparent",
            color: isActive ? "#a5b4fc" : "#a1a1aa",
          })}>
            <span style={{ fontSize:13, width:18, textAlign:"center" }}>{icon}</span>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontSize:11, fontWeight:600 }}>{label}</div>
              <div style={{ fontSize:9, color:"#71717a", marginTop:1 }}>{sub}</div>
            </div>
            {to === "/profile" && unread > 0 && (
              <span style={{ fontSize:9, background:"#6366f1", color:"#fff", borderRadius:20, padding:"1px 5px", flexShrink:0 }}>{unread}</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Bottom status area */}
      <div style={S.statusArea}>
        {/* Dataset status with name */}
        {dsInfo && activeDataset ? (
          <div style={S.statusCard}>
            <div style={S.statusCardHeader}>
              <span style={S.statusLabel}>📊 ACTIVE DATASET</span>
            </div>
            <div style={S.statusCardContent}>
              <div style={S.datasetName}>{activeDataset}</div>
              <div style={S.datasetStats}>
                {dsInfo.rows?.toLocaleString()} rows × {dsInfo.columns} cols
              </div>
            </div>
          </div>
        ) : (
          <div style={S.statusCard}>
            <div style={S.statusCardHeader}>
              <span style={S.statusLabel}>📊 DATASET</span>
            </div>
            <div style={{ ...S.statusCardContent, ...S.noData }}>
              <div style={S.noDataText}>No dataset loaded</div>
            </div>
          </div>
        )}

        {/* LLM provider badge */}
        {provider && (
          <div style={S.statusCard}>
            <div style={S.statusCardHeader}>
              <span style={S.statusLabel}>🤖 AI MODEL</span>
            </div>
            <div style={S.statusCardContent}>
              <div style={{ ...S.providerBadge, color: provider.color }}>
                <span style={S.providerDot}>{provider.dot}</span>
                <span>{provider.label}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* User row */}
      <div style={S.user}>
        <div style={S.avatar}>{email.slice(0,2).toUpperCase()||"U"}</div>
        <div style={{ flex:1, minWidth:0 }}>
          <div style={{ fontSize:10, color:"#a1a1aa", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{email}</div>
          <div style={{ fontSize:9, color:"#71717a" }}>{isAdmin?"Admin":"Member"}</div>
        </div>
        <button onClick={logout} title="Sign out" style={{ background:"transparent", border:"none", color:"#71717a", cursor:"pointer", padding:4, fontSize:13 }}>⏻</button>
      </div>
    </aside>
  );
}

const S = {
  aside:       { width:200, height:"100vh", background:"#09090b", borderRight:"1px solid rgba(255,255,255,.05)", display:"flex", flexDirection:"column", position:"sticky", top:0, flexShrink:0, overflow:"hidden" },
  brand:       { display:"flex", alignItems:"center", gap:8, padding:"14px 12px 10px", borderBottom:"1px solid rgba(255,255,255,.04)", flexShrink:0 },
  brandIcon:   { width:26, height:26, borderRadius:7, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, color:"#fff", fontWeight:700 },
  brandName:   { fontSize:12, fontWeight:700, color:"#f4f4f5" },
  brandTag:    { fontSize:8, color:"#71717a" },
  marqueeWrap: { overflow:"hidden", borderBottom:"1px solid rgba(255,255,255,.03)", height:20, flexShrink:0, display:"flex", alignItems:"center" },
  marquee:     { display:"flex", whiteSpace:"nowrap", animation:"sidebarTicker 40s linear infinite", width:"max-content" },
  marqueeItem: { fontSize:8, color:"#71717a", padding:"0 6px", fontWeight:500 },
  marqueeDot:  { marginLeft:6, color:"#52525b" },
  nav:         { flex:1, padding:"6px 10px", display:"flex", flexDirection:"column", gap:1, overflowY:"auto" },
  statusArea:  { padding:"8px 10px", borderTop:"1px solid rgba(255,255,255,.03)", display:"flex", flexDirection:"column", gap:8, flexShrink:0 },
  statusCard:  { background:"rgba(255,255,255,.02)", borderRadius:6, padding:"6px 8px", border:"1px solid rgba(255,255,255,.04)" },
  statusCardHeader: { marginBottom:4 },
  statusLabel: { fontSize:8, color:"#71717a", fontWeight:600, letterSpacing:".5px" },
  statusCardContent: { display:"flex", flexDirection:"column", gap:2 },
  datasetName: { fontSize:10, color:"#22c55e", fontWeight:600, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" },
  datasetStats:{ fontSize:9, color:"#71717a" },
  noData:      { alignItems:"center" },
  noDataText:  { fontSize:9, color:"#f59e0b", fontStyle:"italic" },
  providerBadge: { display:"flex", alignItems:"center", gap:4, fontSize:10, fontWeight:600 },
  providerDot: { fontSize:10 },
  user:        { display:"flex", alignItems:"center", gap:7, padding:"8px 10px", borderTop:"1px solid rgba(255,255,255,.04)", flexShrink:0 },
  avatar:      { width:24, height:24, borderRadius:"50%", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:8, fontWeight:700, color:"#fff", flexShrink:0 },
};