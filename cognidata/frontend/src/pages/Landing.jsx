import { useNavigate } from "react-router-dom";
import { useState, useEffect, useRef } from "react";

/* ── tiny hook: animate number counting up ─────────────────────────── */
function useCount(target, duration = 1800) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const id = setInterval(() => {
      start += step;
      if (start >= target) { setVal(target); clearInterval(id); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(id);
  }, [target, duration]);
  return val;
}

const FEATURES = [
  { icon:"💬", title:"AI Chat Analyst",      desc:"Ask questions in plain English. GPT-4 powered insights on any dataset." },
  { icon:"📊", title:"150+ Chart Types",      desc:"Plotly, 3D, Geo, Sankey, Sunburst, Waterfall and more — auto-generated." },
  { icon:"🤖", title:"AutoML Studio",         desc:"Train, evaluate and deploy ML models with SHAP explainability." },
  { icon:"🌍", title:"Geo Intelligence",       desc:"H3 hexbins, choropleth, isochrones, OSM maps with live data overlays." },
  { icon:"⚡", title:"Real-Time Streaming",    desc:"SSE-powered live dashboards, webhook ingestion and KPI alerts." },
  { icon:"🔌", title:"Federated Query",        desc:"Query Postgres, MySQL and BigQuery from a single SQL interface." },
  { icon:"🏢", title:"Team Workspaces",        desc:"Invite team members, manage roles, share datasets and dashboards." },
  { icon:"🛡️", title:"Enterprise Security",   desc:"JWT auth, 2FA TOTP, OAuth (Google + GitHub), rate limiting, RBAC." },
];

const STATS = [
  { value:150, suffix:"+", label:"Chart Types" },
  { value:6,   suffix:" AI", label:"Agents" },
  { value:99,  suffix:"%",  label:"Uptime" },
  { value:50,  suffix:"ms", label:"Avg Response" },
];

const STEPS = [
  { n:"01", title:"Connect your data",  desc:"Upload CSV, Excel, JSON or connect to a live database in seconds." },
  { n:"02", title:"Ask anything",        desc:"Chat with your data using natural language — no SQL required." },
  { n:"03", title:"Visualize & share",   desc:"Auto-generate dashboards, export PDFs and invite your team." },
];

const TICKER = [
  "🧠 GPT-4 Powered","⚡ Real-time Analytics","📊 150+ Chart Types","🤖 AutoML Studio",
  "🛡️ Enterprise Security","🌍 Geo Intelligence","📈 Live Dashboards","🔍 Anomaly Detection",
  "🔌 Federated Query","🏢 Team Workspaces","📄 PDF Reports","🔐 2FA Auth",
];
