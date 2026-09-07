import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { Component, lazy, Suspense } from "react";
import useAuth from "./store/auth";
import Sidebar from "./components/Sidebar";

// ── Lazy load all pages — only downloaded when first visited ──────────────────
const Login              = lazy(() => import("./pages/Login"));
const LandingPage        = lazy(() => import("./pages/LandingPage"));
const Chat               = lazy(() => import("./pages/Chat"));
const Dashboard          = lazy(() => import("./pages/Dashboard"));
const Upload             = lazy(() => import("./pages/Upload"));
const AutoML             = lazy(() => import("./pages/AutoML"));
const Admin              = lazy(() => import("./pages/Admin"));
const GeoIntelligence    = lazy(() => import("./pages/GeoIntelligence"));
const Reports            = lazy(() => import("./pages/Reports"));
const AIAnalyst          = lazy(() => import("./pages/AIAnalyst"));
const LiveVisualization  = lazy(() => import("./pages/LiveVisualization"));
const Roadmap            = lazy(() => import("./pages/Roadmap"));
const Settings           = lazy(() => import("./pages/Settings"));
const Profile            = lazy(() => import("./pages/Profile"));
const Workspaces         = lazy(() => import("./pages/Workspaces"));
const DebugAgent         = lazy(() => import("./pages/DebugAgent"));
const AdvancedAnalytics  = lazy(() => import("./pages/AdvancedAnalytics"));
const Maps               = lazy(() => import("./pages/Maps"));
const Alerts             = lazy(() => import("./pages/Alerts"));
const FederatedQuery     = lazy(() => import("./pages/FederatedQuery"));
const SemanticLayer      = lazy(() => import("./pages/SemanticLayer"));
const PipelineBuilder    = lazy(() => import("./pages/PipelineBuilder"));
const DataCatalog        = lazy(() => import("./pages/DataCatalog"));
const ESG                = lazy(() => import("./pages/ESG"));
const GaussianSplatting  = lazy(() => import("./pages/GaussianSplatting"));
const OAuthCallback      = lazy(() => import("./pages/OAuthCallback"));
const ActionLayer        = lazy(() => import("./pages/ActionLayer"));
const LiveIngest         = lazy(() => import("./pages/LiveIngest"));
const DeepAnalyst        = lazy(() => import("./pages/DeepAnalyst"));
const DeveloperHub       = lazy(() => import("./pages/DeveloperHub"));
const RealTimeDashboard  = lazy(() => import("./pages/RealTimeDashboard"));
const Globe3D            = lazy(() => import("./pages/Globe3D"));
const HelpGuide          = lazy(() => import("./pages/HelpGuide"));
const ResetPassword      = lazy(() => import("./pages/ResetPassword"));

function Protected() {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return (
    <div style={{ display:"flex" }}>
      <Sidebar />
      <main style={{ flex:1, overflow:"hidden" }}>
        <PageErrorBoundary>
          <Suspense fallback={<PageLoader />}>
            <Outlet />
          </Suspense>
        </PageErrorBoundary>
      </main>
    </div>
  );
}

function PageLoader() {
  return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:"100vh", background:"#09090b" }}>
      <div style={{ textAlign:"center" }}>
        <div style={{ width:32, height:32, border:"3px solid rgba(99,102,241,.3)", borderTopColor:"#6366f1", borderRadius:"50%", animation:"spin 0.7s linear infinite", margin:"0 auto 12px" }} />
        <div style={{ fontSize:13, color:"#52525b" }}>Loading…</div>
      </div>
    </div>
  );
}

// ── Global Error Boundary — prevents blank screen on any page crash ───────────
class PageErrorBoundary extends Component {
  state = { error: null, info: null };
  static getDerivedStateFromError(e) { return { error: e }; }
  componentDidCatch(e, info) { this.setState({ info }); }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 40, background: "#09090b", minHeight: "100vh", color: "#e4e4e7", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ maxWidth: 560, textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#f4f4f5", marginBottom: 8 }}>Page Error</div>
            <div style={{ fontSize: 14, color: "#71717a", marginBottom: 20 }}>
              This page crashed. The error has been caught so the rest of the app still works.
            </div>
            <div style={{ background: "#18181b", border: "1px solid rgba(239,68,68,.3)", borderRadius: 10, padding: "12px 16px", fontSize: 12, color: "#f87171", fontFamily: "monospace", textAlign: "left", marginBottom: 20, wordBreak: "break-all" }}>
              {this.state.error?.message || String(this.state.error)}
            </div>
            <button onClick={() => { this.setState({ error: null, info: null }); window.location.reload(); }}
              style={{ padding: "10px 24px", borderRadius: 10, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 14, fontWeight: 600, cursor: "pointer" }}>
              🔄 Reload Page
            </button>
            <button onClick={() => { this.setState({ error: null, info: null }); window.history.back(); }}
              style={{ marginLeft: 10, padding: "10px 24px", borderRadius: 10, border: "1px solid rgba(255,255,255,.1)", background: "transparent", color: "#71717a", fontSize: 14, cursor: "pointer" }}>
              ← Go Back
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function AdminOnly({ children }) {
  const { getPayload } = useAuth();  const p = getPayload();
  if (p?.role !== "admin") return <Navigate to="/chat" replace />;
  return children;
}
export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login"          element={<Login />} />
          <Route path="/"               element={<LandingPage />} />
          <Route path="/oauth/callback" element={<OAuthCallback />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route element={<Protected />}>
            <Route path="/chat"        element={<Chat />} />
            <Route path="/upload"      element={<Upload />} />
            <Route path="/dashboard"   element={<Dashboard />} />
            <Route path="/analyst"     element={<AIAnalyst />} />
            <Route path="/automl"      element={<AutoML />} />
            <Route path="/geo"         element={<GeoIntelligence />} />
            <Route path="/viz"         element={<LiveVisualization />} />
            <Route path="/reports"     element={<Reports />} />
            <Route path="/roadmap"     element={<Roadmap />} />
            <Route path="/workspaces"  element={<Workspaces />} />
            <Route path="/analytics"   element={<AdvancedAnalytics />} />
            <Route path="/maps"        element={<Maps />} />
            <Route path="/alerts"      element={<Alerts />} />
            <Route path="/federated"   element={<FederatedQuery />} />
            <Route path="/semantic"    element={<SemanticLayer />} />
            <Route path="/pipeline"    element={<PipelineBuilder />} />
            <Route path="/catalog"     element={<DataCatalog />} />
            <Route path="/esg"         element={<ESG />} />
            <Route path="/splat"       element={<GaussianSplatting />} />
            <Route path="/debug"       element={<DebugAgent />} />
            <Route path="/profile"     element={<Profile />} />
            <Route path="/settings"    element={<Settings />} />
            <Route path="/admin"       element={<Admin />} />
            <Route path="/actions"     element={<ActionLayer />} />
            <Route path="/ingest"      element={<LiveIngest />} />
            <Route path="/deep-analyst" element={<DeepAnalyst />} />
            <Route path="/devhub"      element={<AdminOnly><DeveloperHub /></AdminOnly>} />
            <Route path="/globe"       element={<Globe3D />} />
            <Route path="/help"        element={<HelpGuide />} />
            <Route path="/realtime"    element={<RealTimeDashboard />} />
            <Route path="*"            element={<Navigate to="/chat" replace />} />
          </Route>
          <Route path="/" element={<LandingPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
