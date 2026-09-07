/**
 * LandingPage.jsx
 * 
 * Renders the full Lovable landing page inside the React dashboard app.
 * This way everything runs on ONE port (5173) — no proxy needed.
 * Login button navigates within the same tab using react-router-dom.
 */
import { useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Brain, ArrowRight, PlayCircle, Sparkles, TrendingUp, LineChart,
  Cpu, Database, X, CalendarCheck, LogIn, Check, ChevronDown,
  Zap, Shield, BarChart3, Globe, Users, Bot, FileText,
  Upload, ShieldCheck, Lightbulb, Layers, Code2,
} from "lucide-react";

/* ── Styles injected once ─────────────────────────────────────────── */
const CSS = `
  .landing-root {
    min-height: 100vh;
    background: #000;
    color: #fff;
    font-family: 'Inter', system-ui, sans-serif;
    overflow-x: clip;
  }
  .text-gold { color: #facc15; }
  .glass {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
  }
  .glass-strong {
    background: rgba(10,10,10,0.85);
    border: 1px solid rgba(250,204,21,0.15);
    backdrop-filter: blur(20px);
  }
  .gold-btn {
    background: linear-gradient(90deg,#facc15,#f59e0b);
    color: #000;
    font-weight: 700;
    border: none;
    cursor: pointer;
    transition: transform .2s, box-shadow .2s;
  }
  .gold-btn:hover { transform: scale(1.03); box-shadow: 0 0 30px -6px rgba(250,204,21,.7); }
  .ghost-btn {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.12);
    color: #fff;
    cursor: pointer;
    transition: background .2s;
  }
  .ghost-btn:hover { background: rgba(255,255,255,0.1); }
  .section { padding: 96px 24px; max-width: 1200px; margin: 0 auto; }
  .section-eyebrow {
    display: inline-block;
    background: rgba(250,204,21,0.1);
    border: 1px solid rgba(250,204,21,0.25);
    color: #facc15;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    padding: 4px 14px;
    border-radius: 20px;
    margin-bottom: 20px;
  }
  .section-title { font-size: clamp(1.8rem,4vw,3rem); font-weight: 700; line-height: 1.1; margin-bottom: 16px; }
  .section-sub { color: #a1a1aa; font-size: 1rem; max-width: 600px; line-height: 1.7; }
  .card {
    background: rgba(20,20,20,0.7);
    border: 1px solid rgba(250,204,21,0.1);
    border-radius: 16px;
    padding: 28px;
    transition: border-color .2s, transform .2s;
  }
  .card:hover { border-color: rgba(250,204,21,0.3); transform: translateY(-2px); }
  .faq-item { border-bottom: 1px solid rgba(255,255,255,0.06); }
  @media (max-width:768px) { .hide-mobile { display:none!important; } }
`;

/* ── Demo Modal ───────────────────────────────────────────────────── */
function DemoModal({ onClose }) {
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    await new Promise(r => setTimeout(r, 1200));
    setLoading(false);
    setSent(true);
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, zIndex: 200,
        background: "rgba(0,0,0,0.8)", backdropFilter: "blur(8px)",
        display: "flex", alignItems: "center", justifyContent: "center", padding: 16,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        className="glass-strong"
        style={{ width: "100%", maxWidth: 420, borderRadius: 20, padding: 32, position: "relative" }}
      >
        <button onClick={onClose} style={{ position: "absolute", right: 16, top: 16, background: "transparent", border: "none", color: "#71717a", cursor: "pointer", fontSize: 18 }}>
          <X size={18} />
        </button>

        {sent ? (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <div style={{ width: 56, height: 56, borderRadius: "50%", background: "rgba(250,204,21,.15)", border: "1px solid rgba(250,204,21,.3)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
              <CalendarCheck size={26} color="#facc15" />
            </div>
            <h3 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>You're on the list!</h3>
            <p style={{ color: "#a1a1aa", fontSize: 14, marginBottom: 24 }}>We'll reach out within 24 hours to schedule your personalised demo.</p>
            <button onClick={onClose} className="gold-btn" style={{ padding: "10px 28px", borderRadius: 10, fontSize: 14 }}>Close</button>
          </div>
        ) : (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
              <div style={{ width: 40, height: 40, borderRadius: 12, background: "linear-gradient(135deg,#facc15,#f59e0b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Brain size={20} color="#000" />
              </div>
              <div>
                <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>Request a Demo</h2>
                <p style={{ fontSize: 12, color: "#71717a", margin: 0 }}>See CogniData in action</p>
              </div>
            </div>
            <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {[
                { name: "name", label: "Full Name", type: "text", ph: "Jane Smith" },
                { name: "email", label: "Work Email", type: "email", ph: "jane@company.com" },
                { name: "company", label: "Company", type: "text", ph: "Acme Corp" },
              ].map(({ name, label, type, ph }) => (
                <div key={name}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#71717a", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 6 }}>{label}</label>
                  <input name={name} type={type} required placeholder={ph}
                    style={{ width: "100%", padding: "10px 14px", borderRadius: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: 14, outline: "none", boxSizing: "border-box" }} />
                </div>
              ))}
              <button type="submit" disabled={loading} className="gold-btn"
                style={{ padding: "12px", borderRadius: 11, fontSize: 14, marginTop: 4, opacity: loading ? .7 : 1 }}>
                {loading ? "Sending…" : "Request Demo →"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

/* ── Navbar ───────────────────────────────────────────────────────── */
function Navbar({ onDemo }) {
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    fn();
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  const NAV = [
    { href: "#features", label: "Features" },
    { href: "#how", label: "How It Works" },
    { href: "#agents", label: "AI Agents" },
    { href: "#faq", label: "FAQ" },
  ];

  return (
    <header style={{ position: "fixed", inset: "0 0 auto 0", zIndex: 100, padding: scrolled ? "8px 16px" : "16px 16px", transition: "padding .3s" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <div className={scrolled ? "glass-strong" : ""} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, borderRadius: 50, padding: "10px 20px" }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            <div style={{ width: 32, height: 32, borderRadius: 9, background: "linear-gradient(135deg,#facc15,#f59e0b)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 20px -4px rgba(250,204,21,.6)" }}>
              <Brain size={16} color="#000" strokeWidth={2.5} />
            </div>
            <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-.01em" }}>
              Cogni<span className="text-gold">Data</span>
            </span>
          </div>

          {/* Nav links */}
          <nav className="hide-mobile" style={{ display: "flex", gap: 4 }}>
            {NAV.map(n => (
              <a key={n.href} href={n.href} style={{ padding: "6px 14px", borderRadius: 20, fontSize: 13, color: "#a1a1aa", textDecoration: "none", transition: "color .15s" }}
                onMouseEnter={e => e.target.style.color = "#fff"} onMouseLeave={e => e.target.style.color = "#a1a1aa"}>
                {n.label}
              </a>
            ))}
          </nav>

          {/* CTAs */}
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
            <button onClick={onDemo} className="hide-mobile ghost-btn"
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 16px", borderRadius: 20, fontSize: 13, fontWeight: 500 }}>
              <CalendarCheck size={14} color="#facc15" />
              <span style={{ color: "#facc15" }}>Request a Demo</span>
            </button>
            <button onClick={() => navigate("/login")} className="gold-btn"
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 18px", borderRadius: 20, fontSize: 13 }}>
              <LogIn size={13} />
              Login
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

/* ── Hero ─────────────────────────────────────────────────────────── */
function Hero({ onDemo }) {
  const navigate = useNavigate();
  const points = [12, 22, 18, 30, 26, 40, 36, 52, 48, 60, 58, 74, 70, 88];
  const max = Math.max(...points);
  const w = 800, h = 160, step = w / (points.length - 1);
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${i * step} ${h - (p / max) * (h - 20) - 10}`).join(" ");
  const area = `${path} L ${w} ${h} L 0 ${h} Z`;

  return (
    <section style={{ padding: "160px 24px 96px", maxWidth: 1200, margin: "0 auto" }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} style={{ textAlign: "center", maxWidth: 800, margin: "0 auto" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "rgba(250,204,21,0.08)", border: "1px solid rgba(250,204,21,0.2)", borderRadius: 20, padding: "6px 16px", fontSize: 12, color: "#facc15", marginBottom: 24 }}>
          <Sparkles size={13} />
          Multi-Agent AI · Business Intelligence · Predictive Analytics
        </div>

        <h1 style={{ fontSize: "clamp(2.4rem,6vw,4.5rem)", fontWeight: 800, lineHeight: 1.05, marginBottom: 20, letterSpacing: "-.02em" }}>
          <span className="text-gold">Transform Business Data</span>
          <br />into Intelligent Decisions.
        </h1>

        <p style={{ color: "#a1a1aa", fontSize: "clamp(.95rem,2vw,1.15rem)", lineHeight: 1.7, marginBottom: 36, maxWidth: 620, margin: "0 auto 36px" }}>
          CogniData is an AI-powered Business Analytics Platform combining Multi-Agent AI, Machine Learning, Predictive Analytics, and Natural Language Processing to help you make smarter decisions — faster.
        </p>

        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <button onClick={() => navigate("/login")} className="gold-btn"
            style={{ display: "flex", alignItems: "center", gap: 8, padding: "14px 28px", borderRadius: 50, fontSize: 15 }}>
            Get Started Free <ArrowRight size={16} />
          </button>
          <button onClick={onDemo} className="ghost-btn"
            style={{ display: "flex", alignItems: "center", gap: 8, padding: "14px 28px", borderRadius: 50, fontSize: 15 }}>
            <PlayCircle size={16} color="#facc15" /> Watch Demo
          </button>
        </div>
      </motion.div>

      {/* Dashboard mock */}
      <motion.div initial={{ opacity: 0, y: 60, scale: .96 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: 1, delay: .25 }}
        style={{ maxWidth: 900, margin: "56px auto 0", position: "relative" }}>
        <div style={{ position: "absolute", inset: -16, zIndex: -1, borderRadius: 32, background: "linear-gradient(135deg,rgba(250,204,21,.25),rgba(245,158,11,.1),rgba(250,204,21,.2))", filter: "blur(40px)" }} />
        <div className="glass-strong" style={{ borderRadius: 20, padding: 12, boxShadow: "0 40px 120px -20px rgba(0,0,0,.9)" }}>
          <div style={{ display: "flex", gap: 6, padding: "4px 8px 8px" }}>
            {["#ef4444","#f59e0b","#22c55e"].map(c => <span key={c} style={{ width: 10, height: 10, borderRadius: "50%", background: c, opacity: .7 }} />)}
            <span style={{ fontSize: 11, color: "#52525b", marginLeft: 8 }}>cognidata.ai — Executive Dashboard</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 10, padding: 12, background: "rgba(0,0,0,.4)", borderRadius: 12 }}>
            {[
              { icon: TrendingUp, label: "Revenue", value: "$2.48M", delta: "+18.4%" },
              { icon: LineChart, label: "Forecast Q4", value: "$3.10M", delta: "+24.9%" },
              { icon: Cpu, label: "AI Agents", value: "8 active", delta: "live" },
              { icon: Database, label: "Records", value: "1.2M rows", delta: "clean" },
            ].map(({ icon: Icon, label, value, delta }) => (
              <div key={label} className="glass" style={{ borderRadius: 10, padding: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "#71717a", marginBottom: 8 }}>
                  <Icon size={13} color="#facc15" /> {label}
                </div>
                <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>{value}</div>
                <div style={{ fontSize: 11, color: "#22c55e" }}>{delta}</div>
              </div>
            ))}
            <div className="glass" style={{ gridColumn: "1/-1", borderRadius: 10, padding: 14, height: 120 }}>
              <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height: "100%" }}>
                <defs>
                  <linearGradient id="g1" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="0%" stopColor="#facc15" stopOpacity=".4" />
                    <stop offset="100%" stopColor="#facc15" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path d={area} fill="url(#g1)" />
                <path d={path} fill="none" stroke="#facc15" strokeWidth="2.5" strokeLinecap="round" />
                {points.map((p, i) => (
                  <circle key={i} cx={i * step} cy={h - (p / max) * (h - 20) - 10} r="3" fill="#fff" />
                ))}
              </svg>
            </div>
          </div>
        </div>
      </motion.div>
    </section>
  );
}

/* ── Features ─────────────────────────────────────────────────────── */
const FEATURES = [
  { icon: Bot, title: "Multi-Agent AI", desc: "8 specialized AI agents — Data, SQL, Viz, RAG, Geo, AutoML, LLM, and Controller — working together." },
  { icon: BarChart3, title: "150+ Chart Types", desc: "Auto-generated Plotly charts including Sankey, Network Graph, Parallel Coordinates, 3D Surface and more." },
  { icon: Brain, title: "GPT-4 Powered", desc: "Natural language queries, NL-to-SQL, insight generation, and deep multi-step reasoning via OpenAI." },
  { icon: Shield, title: "Explainable AI (XAI)", desc: "SHAP TreeExplainer shows exactly which features drive every prediction — full model transparency." },
  { icon: Globe, title: "Geo Intelligence", desc: "H3 hexbins, Leaflet maps, isochrones, choropleth maps and a WebGL 3D globe with data spikes." },
  { icon: Zap, title: "Real-Time Streaming", desc: "SSE live dashboards, webhook data ingestion, KPI threshold alerts with email notifications." },
  { icon: Users, title: "Team Workspaces", desc: "Multi-user collaboration with role-based access (admin/member/viewer) and email invitations." },
  { icon: FileText, title: "PDF Reports", desc: "AI-generated multi-page branded reports with embedded charts, scheduled via APScheduler." },
];

function FeaturesSection() {
  return (
    <section id="features" style={{ padding: "96px 24px", background: "rgba(255,255,255,.015)" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", textAlign: "center" }}>
        <span className="section-eyebrow">Features</span>
        <h2 className="section-title">Everything your data team needs</h2>
        <p className="section-sub" style={{ margin: "0 auto 56px" }}>From raw CSV to boardroom-ready insights — all in one platform.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 16, textAlign: "left" }}>
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <motion.div key={title} className="card" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * .05 }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: "rgba(250,204,21,.1)", border: "1px solid rgba(250,204,21,.2)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14 }}>
                <Icon size={18} color="#facc15" />
              </div>
              <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }}>{title}</h3>
              <p style={{ fontSize: 13, color: "#a1a1aa", lineHeight: 1.6, margin: 0 }}>{desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── How it works ─────────────────────────────────────────────────── */
const STEPS = [
  { icon: Upload, n: "01", title: "Upload your data", desc: "CSV, Excel or JSON — up to 200MB. Auto type detection and memory optimisation." },
  { icon: Brain, n: "02", title: "Ask in plain English", desc: "Type a question. The AI controller routes it to the right agent automatically." },
  { icon: Lightbulb, n: "03", title: "Get instant insights", desc: "Charts, tables, SQL, ML predictions or PDF reports — in seconds." },
];

function HowItWorks() {
  return (
    <section id="how" style={{ padding: "96px 24px" }}>
      <div style={{ maxWidth: 900, margin: "0 auto", textAlign: "center" }}>
        <span className="section-eyebrow">How It Works</span>
        <h2 className="section-title">Three steps to intelligent analytics</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))", gap: 24, marginTop: 48, textAlign: "left" }}>
          {STEPS.map(({ icon: Icon, n, title, desc }) => (
            <div key={n} className="card" style={{ position: "relative" }}>
              <div style={{ fontSize: 48, fontWeight: 900, color: "rgba(250,204,21,.08)", position: "absolute", top: 16, right: 20, lineHeight: 1 }}>{n}</div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: "linear-gradient(135deg,rgba(250,204,21,.2),rgba(245,158,11,.1))", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
                <Icon size={20} color="#facc15" />
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>{title}</h3>
              <p style={{ fontSize: 13, color: "#a1a1aa", lineHeight: 1.6, margin: 0 }}>{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── AI Agents ────────────────────────────────────────────────────── */
const AGENTS = [
  { e: "🧠", name: "Controller Agent", role: "Intent classifier — routes every query to the right specialist agent" },
  { e: "📊", name: "Data Agent", role: "Rule-based + LLM-assisted pandas operations on your dataset" },
  { e: "💬", name: "LLM Agent", role: "GPT-4 insight generation, chart type selection, code generation" },
  { e: "📈", name: "Viz Agent", role: "Auto-generates 150+ Plotly chart types from dataset shape" },
  { e: "🔍", name: "SQL Agent", role: "Converts natural language to SQL and executes it on your data" },
  { e: "📚", name: "RAG Agent", role: "Document indexing, vector search, context-aware question answering" },
  { e: "🌍", name: "Geo Agent", role: "City-level geospatial data, H3 hexbins, anomaly detection on maps" },
  { e: "🤖", name: "AutoML Agent", role: "End-to-end model training, SHAP explanations, predictions API" },
];

function AgentsSection() {
  return (
    <section id="agents" style={{ padding: "96px 24px", background: "rgba(255,255,255,.015)" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", textAlign: "center" }}>
        <span className="section-eyebrow">Multi-Agent AI</span>
        <h2 className="section-title">8 Specialised AI Agents</h2>
        <p className="section-sub" style={{ margin: "0 auto 48px" }}>Each agent is an expert. The controller decides which one to call.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 14, textAlign: "left" }}>
          {AGENTS.map(({ e, name, role }, i) => (
            <motion.div key={name} className="card" initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * .04 }}
              style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
              <span style={{ fontSize: 28, flexShrink: 0, marginTop: 2 }}>{e}</span>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{name}</div>
                <div style={{ fontSize: 12, color: "#a1a1aa", lineHeight: 1.5 }}>{role}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Stats ────────────────────────────────────────────────────────── */
function StatsSection() {
  const stats = [
    { value: "150+", label: "Chart Types" },
    { value: "8", label: "AI Agents" },
    { value: "34", label: "App Pages" },
    { value: "30+", label: "API Routes" },
  ];
  return (
    <section style={{ padding: "64px 24px" }}>
      <div style={{ maxWidth: 800, margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 24, textAlign: "center" }}>
        {stats.map(({ value, label }) => (
          <div key={label}>
            <div style={{ fontSize: "clamp(2rem,4vw,3rem)", fontWeight: 900, color: "#facc15", lineHeight: 1 }}>{value}</div>
            <div style={{ fontSize: 13, color: "#71717a", marginTop: 6 }}>{label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── FAQ ──────────────────────────────────────────────────────────── */
const FAQS = [
  { q: "What file formats are supported?", a: "CSV, Excel (.xlsx and .xls), and JSON — up to 200MB per file. Multiple datasets per user are supported with easy switching." },
  { q: "Which AI model does it use?", a: "OpenAI GPT-4 for reasoning, insights, NL-to-SQL and code generation. Sentence Transformers for RAG embeddings." },
  { q: "Do I need to know Python or SQL?", a: "No. Ask questions in plain English. The AI agents handle all SQL, pandas code, and ML model selection automatically." },
  { q: "What ML algorithms are included?", a: "Random Forest, Gradient Boosting, Logistic Regression, Ridge, Naïve Bayes, K-Means, DBSCAN, GMM, Isolation Forest, UMAP, t-SNE, PCA, and SHAP." },
  { q: "Is there email support?", a: "Yes. Gmail SMTP is configured for login alerts, workspace invitations, password resets, and scheduled PDF report delivery." },
];

function FaqSection() {
  const [open, setOpen] = useState(null);
  return (
    <section id="faq" style={{ padding: "96px 24px" }}>
      <div style={{ maxWidth: 700, margin: "0 auto", textAlign: "center" }}>
        <span className="section-eyebrow">FAQ</span>
        <h2 className="section-title">Common questions</h2>
        <div style={{ marginTop: 40, textAlign: "left" }}>
          {FAQS.map(({ q, a }, i) => (
            <div key={i} className="faq-item">
              <button onClick={() => setOpen(open === i ? null : i)}
                style={{ width: "100%", background: "transparent", border: "none", color: "#fff", padding: "18px 0", display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer", fontSize: 15, fontWeight: 600, gap: 12 }}>
                {q}
                <ChevronDown size={16} color="#facc15" style={{ flexShrink: 0, transition: "transform .2s", transform: open === i ? "rotate(180deg)" : "none" }} />
              </button>
              {open === i && <p style={{ color: "#a1a1aa", fontSize: 14, lineHeight: 1.7, padding: "0 0 18px", margin: 0 }}>{a}</p>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── CTA ──────────────────────────────────────────────────────────── */
function CtaSection({ onDemo }) {
  const navigate = useNavigate();
  return (
    <section style={{ padding: "96px 24px", textAlign: "center" }}>
      <div style={{ maxWidth: 600, margin: "0 auto" }}>
        <div style={{ width: 64, height: 64, borderRadius: 18, background: "linear-gradient(135deg,#facc15,#f59e0b)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 24px", boxShadow: "0 0 40px -8px rgba(250,204,21,.6)" }}>
          <Brain size={30} color="#000" />
        </div>
        <h2 style={{ fontSize: "clamp(1.8rem,4vw,2.8rem)", fontWeight: 800, marginBottom: 16 }}>
          Ready to transform your data?
        </h2>
        <p style={{ color: "#a1a1aa", marginBottom: 32, lineHeight: 1.7 }}>
          Join the platform and start turning raw data into intelligent business decisions today.
        </p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <button onClick={() => navigate("/login")} className="gold-btn"
            style={{ padding: "14px 32px", borderRadius: 50, fontSize: 15, display: "flex", alignItems: "center", gap: 8 }}>
            Start for Free <ArrowRight size={16} />
          </button>
          <button onClick={onDemo} className="ghost-btn"
            style={{ padding: "14px 32px", borderRadius: 50, fontSize: 15 }}>
            Request a Demo
          </button>
        </div>
      </div>
    </section>
  );
}

/* ── Footer ───────────────────────────────────────────────────────── */
function Footer() {
  return (
    <footer style={{ borderTop: "1px solid rgba(255,255,255,.06)", padding: "40px 24px", textAlign: "center" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 12 }}>
        <div style={{ width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg,#facc15,#f59e0b)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Brain size={14} color="#000" />
        </div>
        <span style={{ fontWeight: 700 }}>Cogni<span className="text-gold">Data</span></span>
      </div>
      <p style={{ color: "#52525b", fontSize: 12 }}>
        © {new Date().getFullYear()} CogniData. Multi-Agent AI Business Analytics Platform.
      </p>
    </footer>
  );
}

/* ── Main Landing Page ────────────────────────────────────────────── */
export default function LandingPage() {
  const [showDemo, setShowDemo] = useState(false);

  return (
    <>
      <style>{CSS}</style>
      <div className="landing-root">
        <Navbar onDemo={() => setShowDemo(true)} />
        <main>
          <Hero onDemo={() => setShowDemo(true)} />
          <StatsSection />
          <FeaturesSection />
          <HowItWorks />
          <AgentsSection />
          <FaqSection />
          <CtaSection onDemo={() => setShowDemo(true)} />
        </main>
        <Footer />
        {showDemo && <DemoModal onClose={() => setShowDemo(false)} />}
      </div>
    </>
  );
}
