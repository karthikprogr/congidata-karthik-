/**
 * Help & Feature Guide — Complete documentation for all COGNIDATA features
 */
import { useState } from "react";

const FEATURES = [
  {
    id: "auth", icon: "🔐", title: "Login / Register",
    desc: "Authentication with email, Google, GitHub, 2FA, and password reset",
    steps: [
      "Go to the login page",
      "Click '+ Create Account' to register with email + password",
      "Or click 'Sign In' with existing credentials",
      "Or use Google / GitHub buttons for OAuth login",
      "Click 'Forgot password?' to get a reset link emailed to you",
      "Click the link in the email → enter new password on the reset page",
      "Enable 2FA in Settings → Security for extra protection",
    ],
    tips: ["Admin gets email on every login/register/logout", "Reset links expire after 1 hour", "Use App Password for Gmail SMTP in Settings"],
  },
  {
    id: "upload", icon: "📤", title: "Upload Dataset",
    desc: "Upload CSV, Excel, or JSON files up to 200MB",
    steps: [
      "Click 'Upload Dataset' in the sidebar",
      "Drag & drop or click to select a file (CSV, Excel, JSON)",
      "Preview the data in the table below",
      "Click 'Clean Data' to auto-remove duplicates and fill nulls",
      "Click 'RAG Index' to enable document-based AI queries",
    ],
    tips: ["Max file size: 200MB", "Multiple files: upload one at a time, switch between them in the dataset panel"],
  },
  {
    id: "dashboard", icon: "📊", title: "Dashboard",
    desc: "Overview, data explorer, chart builder, and data doctor",
    steps: [
      "Upload a dataset first",
      "Overview tab: auto-generated charts + KPI cards",
      "Pick a color palette (Indigo/Emerald/Sunset/Ocean)",
      "Data Explorer tab: search and paginate through rows",
      "Charts tab: pick chart type, X/Y columns, click Build Chart",
      "Data Doctor tab: health score, missing values, column analysis",
    ],
    tips: ["Pie charts: X = category column, Y = numeric column", "Click 'Clean' or 'Export CSV' from the header"],
  },
  {
    id: "chat", icon: "💬", title: "AI Chat",
    desc: "Natural language queries on your dataset with streaming responses",
    steps: [
      "Upload a dataset first",
      "Add your OpenAI or AIML API key in Settings → API & Models",
      "Type any question: 'What is the average revenue by region?'",
      "Responses stream token by token",
      "Attach an image for vision analysis (GPT-4o)",
      "Click the memory icon to view or clear conversation history",
    ],
    tips: ["Requires OpenAI or AIML API key", "Use voice-to-text by clicking the mic icon"],
  },
  {
    id: "analyst", icon: "🧠", title: "AI Analyst",
    desc: "SQL, RAG, ML, anomaly detection — all in one place",
    steps: [
      "Upload a dataset first",
      "Type a natural language question",
      "AI routes it to the right agent automatically",
      "Click 'Clean' for smart data cleaning",
      "Click 'Classify' or 'Regress' for guided ML",
      "Click 'Cluster' for unsupervised grouping",
    ],
    tips: ["Results include charts, SHAP explanations, and metrics", "Works best with structured tabular data"],
  },
  {
    id: "deep-analyst", icon: "🧠", title: "Deep Analyst",
    desc: "Multi-step reasoning, auto insights, decision engine, narrative",
    steps: [
      "Upload a dataset first",
      "🧠 Deep Reason: type a complex question → get multi-step reasoning with confidence score",
      "💡 Auto Insights: click to auto-scan data and surface top insights (no question needed)",
      "🎯 Decision Engine: enter a business goal → get ranked action recommendations",
      "📝 Narrate: generates a full executive report automatically",
    ],
    tips: ["Confidence score 0-100 shows how reliable the answer is", "Follow-up questions are auto-suggested"],
  },
  {
    id: "analytics", icon: "🔬", title: "Advanced Analytics",
    desc: "Statistical tests, clustering, anomaly detection, timeseries, embeddings",
    steps: [
      "Upload a dataset first",
      "Stats tab: Shapiro-Wilk normality + Pearson correlations",
      "Cluster tab: pick K-Means/DBSCAN/GMM, click Cluster",
      "Anomaly tab: Isolation Forest detects outliers",
      "Timeseries tab: pick a numeric column, see trend decomposition",
      "Embedding tab: pick UMAP/t-SNE/PCA for 3D scatter visualization",
    ],
    tips: ["Silhouette score shows clustering quality", "UMAP requires more memory than PCA"],
  },
  {
    id: "automl", icon: "🤖", title: "AutoML Studio",
    desc: "Train ML models, get SHAP explanations, run predictions",
    steps: [
      "Upload a dataset first",
      "Pick a target column (what you want to predict)",
      "Click 'Train' for classification or regression",
      "View ROC curve, confusion matrix, or residual plots",
      "Click 'Explain' for SHAP feature importance chart",
      "Click 'Predict' to run predictions on new data",
    ],
    tips: ["Classification: target should be categorical", "Regression: target should be numeric"],
  },
  {
    id: "maps", icon: "🗺️", title: "Advanced Maps",
    desc: "Choropleth, H3 hex, flow maps, satellite, geo cluster, polygon filter",
    steps: [
      "Upload a dataset with geographic columns",
      "Choropleth: pick country column + value column → Generate",
      "H3 Hex: pick lat/lon columns → hexagonal density map",
      "Flow Map: pick origin/destination columns → arc connections",
      "Satellite: toggle dark/street/satellite tile styles",
      "Geo Cluster: group nearby points, adjust cluster radius",
      "Polygon Filter: paste lat,lon pairs to filter points inside a polygon",
    ],
    tips: ["All maps use OpenStreetMap — no API key needed", "Click any point for a tooltip with row data"],
  },
  {
    id: "globe", icon: "🌍", title: "3D Globe",
    desc: "Real-world NASA Earth texture with data spikes",
    steps: [
      "Upload a dataset with lat/lon columns",
      "Click '🔄 Cols' to load column names",
      "Select Latitude, Longitude, and Value columns",
      "Click '🌍 Plot Data' — spikes appear on the real Earth",
      "Drag to rotate, scroll to zoom",
      "Toggle '🌙 Night' for NASA city lights view",
      "Click any spike for a tooltip with full row data",
    ],
    tips: ["Earth texture loads from NASA CDN — needs internet", "Value column controls spike height"],
  },
  {
    id: "splat", icon: "✨", title: "Gaussian Splatting",
    desc: "16 WebGL 3D render types for your data",
    steps: [
      "Upload a dataset with numeric columns",
      "Select X, Y, Z, Size, Color columns",
      "Pick a render type from the 16 options",
      "Click 'Render' to visualize",
      "Drag to orbit, scroll to zoom",
      "Adjust Splat Size and Opacity sliders",
    ],
    tips: [
      "✨ Gaussian Splats: soft glowing spheres",
      "🧊 Voxel: 3D cubes",
      "🧬 DNA: double helix spiral",
      "🌀 Galaxy: spiral galaxy distribution",
      "🏔️ Terrain: heightmap surface from data density",
    ],
  },
  {
    id: "geo", icon: "🌍", title: "Geo Intelligence",
    desc: "Live city data simulation with forecasting and playback",
    steps: [
      "View live simulated data for 15 global cities",
      "Switch between Live Map, Forecast, Segments, Rankings, Trend, Playback tabs",
      "Click 'Sync Real Data' to load your own dataset's geo data",
      "Use Playback to replay historical data",
    ],
    tips: ["Data refreshes every few seconds in Live mode", "Rankings show top cities by metric"],
  },
  {
    id: "viz", icon: "📡", title: "Live Visualization",
    desc: "Real-time streaming charts with 11 visualization modes",
    steps: [
      "Pick a visualization mode from the left panel",
      "Adjust Speed and Window sliders",
      "Click '▶ Live' to start real-time streaming",
      "Click '⏹ Stop' to pause",
      "Switch modes without stopping",
    ],
    tips: ["Traffic Monitor, Neural Network, 3D modes available", "Data is simulated random walk"],
  },
  {
    id: "alerts", icon: "🚨", title: "KPI Alerts",
    desc: "Threshold rules that fire when metrics breach limits",
    steps: [
      "Click '+ Create Rule'",
      "Set: Metric name (column name), Condition (gt/lt/eq/gte/lte), Threshold value",
      "Enable 'Email notification' to get emailed when triggered",
      "Click 'Check Metrics' and pass JSON like {\"revenue\": 500} to test",
      "View alert history with warning/critical severity",
    ],
    tips: ["Alerts also fire automatically when Live Ingest receives data", "Connect to Action Layer for webhooks"],
  },
  {
    id: "actions", icon: "⚡", title: "Action Layer",
    desc: "Automate responses — webhooks, Slack, email on alert fire",
    steps: [
      "Click '+ Create Action'",
      "Set Type: Webhook (POST to URL), Slack (Slack webhook URL), or Email",
      "Set Trigger: 'On Alert Fire' (auto) or 'Manual'",
      "Optionally bind to a specific alert rule via Rule ID",
      "Click '▶ Run' to test manually",
      "When an alert fires, matching actions trigger automatically",
    ],
    tips: [
      "Slack: create Incoming Webhook at api.slack.com/apps",
      "Webhook payload includes: metric, value, threshold, timestamp",
    ],
  },
  {
    id: "ingest", icon: "📡", title: "Live Ingest",
    desc: "Stream real-time data via webhooks without uploading files",
    steps: [
      "Click '+ Create Stream' — give it a name",
      "Copy the stream ID and API key shown",
      "Send data from anywhere using curl or Python",
      "Watch rows appear in the live table (refreshes every 2s)",
      "Click '📊 Load as Dataset' to analyze in AI Chat",
    ],
    code: `curl -X POST http://localhost:8000/api/ingest/STREAM_ID \\
  -H "X-Stream-Key: YOUR_KEY" \\
  -d '{"revenue": 1200, "region": "APAC"}'`,
    tips: ["Supports single row or batch (array) ingestion", "Alert rules check every incoming row automatically"],
  },
  {
    id: "reports", icon: "📈", title: "Reports",
    desc: "PDF generation, CSV/Excel export, data profiling, scheduled delivery",
    steps: [
      "Upload a dataset first",
      "Overview tab: auto-generated visual report",
      "Export tab: download as CSV, JSON, or Excel",
      "Profile tab: per-column data profiling",
      "Schedule tab: set daily/weekly email delivery with recipient email",
    ],
    tips: ["PDF includes AI-generated insights", "Scheduled reports are sent via SMTP email"],
  },
  {
    id: "workspaces", icon: "🏢", title: "Workspaces",
    desc: "Team collaboration with roles and email invitations",
    steps: [
      "My Workspaces tab: click '+ Create' to make a new workspace",
      "Invite Members tab: select workspace, enter email + role, click 'Send Invitation'",
      "Invited user gets an email with an Accept button and join link",
      "Join via Invite tab: paste the token from the email, click 'Join Workspace'",
      "Click '👥 Members' on a workspace card to see/remove members",
    ],
    tips: ["Roles: owner / editor / viewer", "Invitation tokens expire after 72 hours"],
  },
  {
    id: "federated", icon: "🔌", title: "Federated Query",
    desc: "Query external databases without uploading data",
    steps: [
      "Fill in: Name, Type (postgres/mysql/sqlite/bigquery/snowflake)",
      "Enter: Host, Port, Database, Username, Password",
      "Click '+ Add Connection'",
      "Click 'Test' to verify connectivity",
      "Click 'Schema' to browse tables and columns",
      "Click 'Query' → write SQL or natural language → Run",
    ],
    tips: ["Host must be the server IP/hostname, not an email address", "Natural language converts to SQL automatically"],
  },
  {
    id: "semantic", icon: "🧮", title: "Semantic Metrics",
    desc: "Define named business metrics with expressions",
    steps: [
      "Click '+ Define Metric'",
      "Give it a name (e.g. 'profit_margin') and a pandas expression (e.g. 'revenue - cost')",
      "Click 'Compute' to calculate it on your dataset",
      "Click 'Compute All' to run all metrics at once",
      "View 'Lineage' to see metric dependencies",
    ],
    tips: ["Expressions use pandas syntax", "Metrics are saved per session"],
  },
  {
    id: "pipeline", icon: "⚙️", title: "Pipeline Builder",
    desc: "AI-generated ETL pipelines for data transformation",
    steps: [
      "Describe what ETL pipeline you need in plain English",
      "Example: 'clean nulls, normalize revenue, encode categories'",
      "Click 'Generate Pipeline' — AI creates the steps",
      "Click 'Run Step' to execute each step on your dataset",
      "Download the generated pipeline code",
    ],
    tips: ["Each step is executed independently", "Generated code is Python/pandas"],
  },
  {
    id: "catalog", icon: "📚", title: "Data Catalog",
    desc: "Column metadata, auto-documentation, lineage tracking",
    steps: [
      "Upload a dataset first",
      "View all columns with type, nulls, unique count",
      "Click 'Annotate' on any column to add a description",
      "Click 'Auto-Document' — AI writes descriptions for all columns",
      "View 'Lineage' to track data transformations",
    ],
    tips: ["Auto-documentation requires an API key", "Annotations are saved per session"],
  },
  {
    id: "profile", icon: "👤", title: "My Profile",
    desc: "API keys, notifications, feedback, activity, 2FA",
    steps: [
      "API Keys tab: click '+ Create Key', give it a name, copy the key",
      "Notifications tab: view and mark notifications as read",
      "Feedback tab: submit feedback with a 1-5 star rating",
      "Activity tab: view your recent actions",
      "Change Password: enter current + new password",
    ],
    tips: ["API keys can be used instead of JWT tokens", "Keys are shown only once — copy immediately"],
  },
  {
    id: "settings", icon: "⚙️", title: "Settings",
    desc: "API keys, appearance, data preferences, SMTP, security",
    steps: [
      "API & Models tab: paste OpenAI or AIML key → Test → Save",
      "Appearance tab: toggle Light/Dark mode",
      "Data Preferences tab: set default chart type, table rows, decimals",
      "Notifications tab (admin): configure SMTP → Save SMTP → Test Email",
      "Security tab: change password, enable 2FA with QR code",
      "Danger Zone: clear local data, reset preferences, delete account",
    ],
    tips: ["2FA: scan QR with Google Authenticator or Authy", "SMTP: use Gmail App Password (16 chars, no spaces)"],
  },
  {
    id: "admin", icon: "🛡️", title: "Admin Panel",
    desc: "User management, logs, metrics, broadcast (admin only)",
    steps: [
      "Users tab: view all users, change roles, activate/deactivate, delete",
      "Logs tab: view all API request logs",
      "Metrics tab: system performance metrics",
      "System tab: CPU, memory, DB size",
      "AI Usage tab: which AI endpoints are used most",
      "Broadcast tab: send a message to all users",
    ],
    tips: ["Only accessible to admin role users", "Broadcast sends in-app notifications to everyone"],
  },
  {
    id: "devhub", icon: "💻", title: "Developer Hub",
    desc: "API reference, SDK examples, webhook guide (admin only)",
    steps: [
      "Quickstart tab: 7-step guide to integrate via API",
      "API Reference tab: full endpoint list with methods and parameters",
      "SDK tab: copy Python, JavaScript, or curl code examples",
      "Webhooks tab: guide for setting up webhook actions",
      "Rate Limits tab: view API limits per endpoint",
    ],
    tips: ["Only accessible to admin role users", "Python SDK example covers all major features"],
  },
  {
    id: "debug", icon: "🛠️", title: "Debug Agent",
    desc: "System diagnostics, performance, traces (admin only)",
    steps: [
      "System tab: Python version, memory, CPU usage",
      "Health tab: API health check",
      "Packages tab: check installed packages, install new ones",
      "Performance tab: response times, maintenance actions",
      "Traces tab: AI agent execution traces",
      "Watcher tab: file system change events",
    ],
    tips: ["Only accessible to admin role users", "Use Performance tab to clear caches"],
  },
  {
    id: "oauth", icon: "🔗", title: "OAuth Callback",
    desc: "Handles Google and GitHub OAuth redirects automatically",
    steps: [
      "Click Google or GitHub on the login page",
      "You are redirected to the OAuth provider",
      "After approval, you are redirected back to /oauth/callback",
      "The callback page extracts the code and exchanges it for a JWT token",
      "You are automatically logged in and redirected to /chat",
    ],
    tips: ["OAuth credentials are configured in Settings → Config (admin)", "Google and GitHub OAuth both supported"],
  },
];

const S = {
  page:    { padding: "24px", background: "#09090b", minHeight: "100vh", color: "#e4e4e7" },
  header:  { marginBottom: 24 },
  title:   { fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 4 },
  sub:     { fontSize: 13, color: "#71717a" },
  search:  { width: "100%", maxWidth: 400, background: "#18181b", border: "1px solid rgba(255,255,255,.1)", borderRadius: 10, padding: "10px 14px", color: "#e4e4e7", fontSize: 14, outline: "none", marginBottom: 20, boxSizing: "border-box" },
  grid:    { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 },
  card:    { background: "#18181b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 12, overflow: "hidden", cursor: "pointer", transition: "border-color .15s" },
  cardHdr: { padding: "14px 16px", display: "flex", alignItems: "center", gap: 10 },
  icon:    { fontSize: 20 },
  cardTitle: { fontSize: 14, fontWeight: 600, color: "#f4f4f5" },
  cardDesc:  { fontSize: 12, color: "#71717a", marginTop: 2 },
  body:    { padding: "0 16px 16px" },
  step:    { display: "flex", gap: 10, marginBottom: 8, alignItems: "flex-start" },
  num:     { width: 20, height: 20, borderRadius: "50%", background: "rgba(99,102,241,.2)", color: "#818cf8", fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1 },
  stepTxt: { fontSize: 13, color: "#a1a1aa", lineHeight: 1.5 },
  tip:     { fontSize: 11, color: "#52525b", padding: "4px 0", borderTop: "1px solid rgba(255,255,255,.04)", marginTop: 4 },
  code:    { background: "#09090b", border: "1px solid rgba(255,255,255,.08)", borderRadius: 8, padding: "10px 12px", fontFamily: "monospace", fontSize: 11, color: "#a1a1aa", marginTop: 8, whiteSpace: "pre-wrap", wordBreak: "break-all" },
  badge:   { padding: "2px 8px", borderRadius: 20, fontSize: 10, fontWeight: 600, background: "rgba(99,102,241,.1)", color: "#818cf8", marginLeft: 6 },
};

export default function HelpGuide() {
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(null);

  const filtered = FEATURES.filter(f =>
    !search || f.title.toLowerCase().includes(search.toLowerCase()) ||
    f.desc.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.title}>📖 Feature Guide</div>
        <div style={S.sub}>Complete guide to every feature in COGNIDATA — {FEATURES.length} features</div>
      </div>

      <input
        style={S.search}
        placeholder="Search features…"
        value={search}
        onChange={e => setSearch(e.target.value)}
      />

      <div style={S.grid}>
        {filtered.map(f => (
          <div key={f.id} style={{ ...S.card, borderColor: expanded === f.id ? "rgba(99,102,241,.4)" : "rgba(255,255,255,.08)" }}
            onClick={() => setExpanded(expanded === f.id ? null : f.id)}>
            <div style={S.cardHdr}>
              <span style={S.icon}>{f.icon}</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <span style={S.cardTitle}>{f.title}</span>
                  {(f.id === "admin" || f.id === "devhub" || f.id === "debug") &&
                    <span style={S.badge}>Admin only</span>}
                </div>
                <div style={S.cardDesc}>{f.desc}</div>
              </div>
              <span style={{ color: "#52525b", fontSize: 12 }}>{expanded === f.id ? "▲" : "▼"}</span>
            </div>

            {expanded === f.id && (
              <div style={S.body} onClick={e => e.stopPropagation()}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#6366f1", marginBottom: 8, textTransform: "uppercase", letterSpacing: 1 }}>How to use</div>
                {f.steps.map((step, i) => (
                  <div key={i} style={S.step}>
                    <div style={S.num}>{i + 1}</div>
                    <div style={S.stepTxt}>{step}</div>
                  </div>
                ))}
                {f.code && <div style={S.code}>{f.code}</div>}
                {f.tips?.length > 0 && (
                  <div style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#f59e0b", marginBottom: 6, textTransform: "uppercase", letterSpacing: 1 }}>Tips</div>
                    {f.tips.map((tip, i) => (
                      <div key={i} style={S.tip}>💡 {tip}</div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
