import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { authApi, api } from "../api/client";
import useAuth from "../store/auth";

const TICKER = ["🧠 6 AI Agents","⚡ Real-time","📊 150+ Charts","🤖 AutoML","🛡️ Secure","🔮 GPT-4","📈 Live Dashboards","🔍 Anomaly Detection"];

export default function Login() {
  const [mode, setMode]         = useState("login");
  const [email, setEmail]       = useState("");
  const [pass, setPass]         = useState("");
  const [fullName, setFullName] = useState("");
  const [confirmPass, setConfirmPass] = useState("");
  const [rememberMe, setRememberMe]   = useState(false);
  const [tosAccepted, setTosAccepted] = useState(false);
  const [show, setShow]         = useState(false);
  const [err, setErr]           = useState(null);
  const [loading, setLoad]      = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");
  // 2FA state
  const [requires2fa, setReq2fa] = useState(false);
  const [tempToken, setTempToken] = useState("");
  const [totpCode, setTotpCode]  = useState("");
  // Forgot password state
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotMsg, setForgotMsg] = useState(null);
  const [forgotLoading, setForgotLoad] = useState(false);
  const { setToken }            = useAuth();
  const navigate                = useNavigate();

  // Check backend connection on mount
  useEffect(() => {
    api.get("/debug/ping").then(() => {
      setBackendStatus("connected");
    }).catch(() => {
      setBackendStatus("offline");
      setErr({ ok: false, msg: "Backend server is offline. Please start the backend server." });
    });
  }, []);

  const submit = async (e) => {
    e.preventDefault(); setErr(null); setLoad(true);
    try {
      if (mode === "register") {
        if (pass.length < 6) { setErr({ ok: false, msg: "Password must be at least 6 characters." }); setLoad(false); return; }
        if (pass !== confirmPass) { setErr({ ok: false, msg: "Passwords do not match." }); setLoad(false); return; }
        if (!tosAccepted) { setErr({ ok: false, msg: "Please accept the Terms of Service." }); setLoad(false); return; }
        await authApi.register(email, pass);
        setMode("login"); setErr({ ok: true, msg: "Account created — sign in below." });
      } else {
        const { data } = await authApi.login(email, pass);
        if (data.requires_2fa) {
          setTempToken(data.temp_token);
          setReq2fa(true);
        } else {
          if (rememberMe) localStorage.setItem("remember_email", email);
          setToken(data.access_token); navigate("/chat");
        }
      }
    } catch (e) {
      setErr({ ok: false, msg: e.response?.data?.detail || e.message || "Request failed" });
    } finally { setLoad(false); }
  };

  const verify2fa = async (e) => {
    e.preventDefault(); setErr(null); setLoad(true);
    try {
      const { data } = await authApi.verify2fa(tempToken, totpCode);
      setToken(data.access_token); navigate("/chat");
    } catch (e) {
      setErr({ ok: false, msg: e.response?.data?.detail || "Invalid code" });
    } finally { setLoad(false); }
  };

  const oauth = async (provider) => {
    try {
      const { data } = await (provider === "google" ? authApi.googleUrl() : authApi.githubUrl());
      sessionStorage.setItem("oauth_provider", provider);
      window.location.href = data.url;
    } catch (e) { setErr({ ok: false, msg: `${provider} sign-in failed` }); }
  };

  const submitForgot = async (e) => {
    e.preventDefault(); setForgotMsg(null); setForgotLoad(true);
    try {
      await api.post("/auth/forgot-password", { email: forgotEmail });
      setForgotMsg({ ok: true, msg: "If that email exists, a reset link has been sent. Check your inbox." });
    } catch (e) {
      setForgotMsg({ ok: false, msg: e.response?.data?.detail || "Request failed" });
    } finally { setForgotLoad(false); }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden dot-grid scanline" style={{ background: "#09090b", paddingTop: 40 }}>
      {/* Orbs */}
      <div className="fixed rounded-full pointer-events-none" style={{ width:600,height:600,top:"-10%",left:"-5%",background:"radial-gradient(circle,rgba(99,102,241,.1) 0%,transparent 65%)",animation:"orbFloat 14s ease-in-out infinite" }} />
      <div className="fixed rounded-full pointer-events-none" style={{ width:500,height:500,bottom:"-8%",right:"-5%",background:"radial-gradient(circle,rgba(139,92,246,.08) 0%,transparent 65%)",animation:"orbFloat 18s ease-in-out 2s infinite" }} />

      {/* Ticker */}
      <div className="fixed top-0 left-0 right-0 z-20 overflow-hidden flex items-center" style={{ height:34,background:"rgba(9,9,11,.9)",borderBottom:"1px solid rgba(255,255,255,.06)" }}>
        <div style={{ display:"flex",whiteSpace:"nowrap",width:"max-content",animation:"ticker 28s linear infinite" }}>
          {[...TICKER,...TICKER].map((t,i) => <span key={i} style={{ fontSize:11,color:"#52525b",padding:"0 24px",fontWeight:500 }}>{t}<span style={{ marginLeft:24,color:"#27272a" }}>·</span></span>)}
        </div>
      </div>

      {/* Card */}
      <div className="fade-up relative z-10 w-full" style={{ maxWidth:440,background:"rgba(14,14,16,.92)",border:"1px solid rgba(255,255,255,.08)",borderRadius:20,padding:"32px 36px 26px",boxShadow:"0 0 60px rgba(99,102,241,.08),0 40px 80px rgba(0,0,0,.7)" }}>
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-1">
          <div style={{ width:42,height:42,borderRadius:12,background:"linear-gradient(135deg,#7c3aed,#6366f1)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:20,boxShadow:"0 4px 20px rgba(124,58,237,.5)" }}>🧠</div>
          <span style={{ fontSize:24,fontWeight:800,color:"#f4f4f5",letterSpacing:"0.06em" }}>COGNIDATA</span>
        </div>
        <p className="text-center mb-4" style={{ fontSize:12,color:"#52525b" }}>LLM Powered Data Analyst Platform</p>
        
        {/* Demo Credentials */}
        <div style={{ marginBottom:16,padding:"10px 12px",borderRadius:8,background:"rgba(99,102,241,.08)",border:"1px solid rgba(99,102,241,.2)" }}>
          <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center" }}>
            <div>
              <p style={{ fontSize:10,fontWeight:700,color:"#818cf8",letterSpacing:"0.08em",marginBottom:6 }}>🔑 DEMO CREDENTIALS</p>
              <p style={{ fontSize:11,color:"#a5b4fc",margin:"2px 0" }}>📧 rudraadmin@gmail.com</p>
              <p style={{ fontSize:11,color:"#a5b4fc",margin:"2px 0" }}>🔒 adminrudra@1234</p>
            </div>
            <div style={{ textAlign:"right" }}>
              <p style={{ fontSize:9,color:"#71717a",marginBottom:4 }}>Backend</p>
              <div style={{ display:"flex",alignItems:"center",gap:4 }}>
                <div style={{ width:6,height:6,borderRadius:"50%",background: backendStatus === "connected" ? "#10b981" : backendStatus === "offline" ? "#ef4444" : "#f59e0b" }} />
                <span style={{ fontSize:10,color: backendStatus === "connected" ? "#10b981" : backendStatus === "offline" ? "#ef4444" : "#f59e0b" }}>
                  {backendStatus === "connected" ? "Online" : backendStatus === "offline" ? "Offline" : "Checking..."}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Inner ticker */}
        <div style={{ overflow:"hidden",marginBottom:18,maskImage:"linear-gradient(to right,transparent,black 10%,black 90%,transparent)",WebkitMaskImage:"linear-gradient(to right,transparent,black 10%,black 90%,transparent)" }}>
          <div style={{ display:"flex",gap:8,width:"max-content",animation:"ticker 14s linear infinite" }}>
            {[...TICKER,...TICKER].map((t,i) => <span key={i} style={{ fontSize:10,fontWeight:600,color:"#6366f1",background:"rgba(99,102,241,.08)",border:"1px solid rgba(99,102,241,.18)",borderRadius:20,padding:"3px 10px",whiteSpace:"nowrap" }}>{t}</span>)}
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display:"flex",background:"rgba(0,0,0,.4)",border:"1px solid rgba(255,255,255,.07)",borderRadius:12,padding:4,marginBottom:18,gap:4 }}>
          {["login","register"].map(m => (
            <button key={m} type="button" onClick={() => { setMode(m); setErr(null); }}
              style={{ flex:1,padding:"9px",borderRadius:9,border:"none",fontSize:13,fontWeight:600,cursor:"pointer",transition:"all .2s",
                background: mode===m ? "linear-gradient(135deg,#7c3aed,#6366f1)" : "transparent",
                color: mode===m ? "#fff" : "#52525b",
                boxShadow: mode===m ? "0 2px 16px rgba(124,58,237,.4)" : "none" }}>
              {m === "login" ? "▲ Sign In" : "+ Create Account"}
            </button>
          ))}
        </div>

        {/* Social */}
        <p style={{ textAlign:"center",fontSize:10,color:"#27272a",letterSpacing:"0.12em",fontWeight:700,marginBottom:10 }}>CONTINUE WITH</p>
        <div style={{ display:"flex",gap:10,marginBottom:14 }}>
          {[["google","🌐","Google"],["github","🐙","GitHub"]].map(([p,icon,label]) => (
            <button key={p} type="button" onClick={() => oauth(p)}
              style={{ flex:1,padding:"10px",borderRadius:10,border:"1px solid rgba(255,255,255,.09)",background:"rgba(255,255,255,.04)",color:"#a1a1aa",fontSize:13,fontWeight:500,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",gap:8 }}>
              <span>{icon}</span>{label}
            </button>
          ))}
        </div>

        <div style={{ display:"flex",alignItems:"center",gap:10,marginBottom:14 }}>
          <div style={{ flex:1,height:1,background:"rgba(255,255,255,.06)" }} />
          <span style={{ fontSize:10,color:"#27272a",fontWeight:700,letterSpacing:"0.1em" }}>{mode==="login"?"OR SIGN IN WITH EMAIL":"OR CREATE WITH EMAIL"}</span>
          <div style={{ flex:1,height:1,background:"rgba(255,255,255,.06)" }} />
        </div>

        {err && <div style={{ padding:"9px 13px",borderRadius:8,border:"1px solid",fontSize:13,marginBottom:10,background:err.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:err.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:err.ok?"#34d399":"#f87171" }}>{err.ok?"✓":"✗"} {err.msg}</div>}

        <form onSubmit={submit} style={{ display:"flex",flexDirection:"column",gap:10 }}>
          <label style={{ fontSize:12,fontWeight:500,color:"#71717a" }}>✉ Email</label>
          <input type="email" placeholder="you@company.com" value={email} onChange={e=>setEmail(e.target.value)} required
            style={{ padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:14,outline:"none",fontFamily:"inherit" }} />

          {mode === "register" && (
            <>
              <label style={{ fontSize:12,fontWeight:500,color:"#71717a" }}>👤 Full Name</label>
              <input type="text" placeholder="Your full name" value={fullName} onChange={e=>setFullName(e.target.value)}
                style={{ padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:14,outline:"none",fontFamily:"inherit" }} />
            </>
          )}

          <label style={{ fontSize:12,fontWeight:500,color:"#71717a" }}>🔒 Password</label>
          <div style={{ position:"relative" }}>
            <input type={show?"text":"password"} placeholder="Enter your password" value={pass} onChange={e=>setPass(e.target.value)} required
              style={{ width:"100%",padding:"11px 42px 11px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:14,outline:"none",fontFamily:"inherit",boxSizing:"border-box" }} />
            <button type="button" onClick={()=>setShow(!show)} style={{ position:"absolute",right:12,top:"50%",transform:"translateY(-50%)",background:"transparent",border:"none",cursor:"pointer",fontSize:15,color:"#52525b" }}>{show?"🙈":"👁"}</button>
          </div>
          {mode === "register" && (
            <div style={{ fontSize:11,color:"#52525b",padding:"4px 8px",borderRadius:6,background:"rgba(255,255,255,.03)",border:"1px solid rgba(255,255,255,.06)" }}>
              🔑 Minimum 6 characters
            </div>
          )}

          {mode === "register" && (
            <>
              <label style={{ fontSize:12,fontWeight:500,color:"#71717a" }}>🔒 Confirm Password</label>
              <input type={show?"text":"password"} placeholder="Confirm your password" value={confirmPass} onChange={e=>setConfirmPass(e.target.value)} required
                style={{ padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:`1px solid ${confirmPass && confirmPass !== pass ? "rgba(239,68,68,.4)" : "rgba(255,255,255,.09)"}`,color:"#f4f4f5",fontSize:14,outline:"none",fontFamily:"inherit" }} />
              {confirmPass && confirmPass !== pass && <span style={{ fontSize:11,color:"#f87171" }}>Passwords do not match</span>}
            </>
          )}

          {mode === "login" && (
            <label style={{ display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13,color:"#71717a" }}>
              <input type="checkbox" checked={rememberMe} onChange={e=>setRememberMe(e.target.checked)} style={{ accentColor:"#6366f1" }} />
              Remember me
            </label>
          )}

          {mode === "login" && (
            <button type="button" onClick={() => { setShowForgot(true); setForgotMsg(null); setForgotEmail(email); }}
              style={{ background:"transparent",border:"none",cursor:"pointer",color:"#818cf8",fontSize:12,textAlign:"left",padding:0,textDecoration:"underline" }}>
              Forgot password?
            </button>
          )}

          {mode === "register" && (
            <label style={{ display:"flex",alignItems:"flex-start",gap:8,cursor:"pointer",fontSize:12,color:"#71717a" }}>
              <input type="checkbox" checked={tosAccepted} onChange={e=>setTosAccepted(e.target.checked)} style={{ accentColor:"#6366f1",marginTop:2,flexShrink:0 }} />
              I agree to the <span style={{ color:"#818cf8",textDecoration:"underline",cursor:"pointer" }}>Terms of Service</span> and <span style={{ color:"#818cf8",textDecoration:"underline",cursor:"pointer" }}>Privacy Policy</span>
            </label>
          )}

          <button type="submit" disabled={loading}
            style={{ padding:"13px",borderRadius:11,border:"none",background:"linear-gradient(90deg,#f97316,#ef4444 50%,#ec4899)",color:"#fff",fontSize:15,fontWeight:700,cursor:"pointer",marginTop:4,display:"flex",alignItems:"center",justifyContent:"center",gap:8,boxShadow:"0 4px 24px rgba(249,115,22,.4)",letterSpacing:"0.02em" }}>
            {loading ? <span className="spinner" style={{ borderTopColor:"#fff" }} /> : mode==="login"?"✦ Sign In":"+ Create Account"}
          </button>
        </form>

        <p style={{ textAlign:"center",fontSize:11,color:"#27272a",marginTop:18 }}>🔒 256-bit encrypted · SOC 2 compliant · GDPR ready</p>
      </div>

      {/* 2FA Modal */}
      {requires2fa && (
        <div style={{ position:"fixed",inset:0,background:"rgba(0,0,0,.7)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:100 }}>
          <div style={{ background:"rgba(14,14,16,.95)",border:"1px solid rgba(99,102,241,.3)",borderRadius:16,padding:"32px 36px",width:340 }}>
            <h3 style={{ fontSize:16,fontWeight:700,color:"#f4f4f5",marginBottom:8 }}>🔐 Two-Factor Authentication</h3>
            <p style={{ fontSize:13,color:"#71717a",marginBottom:16 }}>Enter the 6-digit code from your authenticator app.</p>
            {err && <div style={{ padding:"8px 12px",borderRadius:8,background:"rgba(239,68,68,.1)",border:"1px solid rgba(239,68,68,.3)",color:"#f87171",fontSize:13,marginBottom:12 }}>{err.msg}</div>}
            <form onSubmit={verify2fa} style={{ display:"flex",flexDirection:"column",gap:10 }}>
              <input type="text" inputMode="numeric" maxLength={6} placeholder="000000"
                value={totpCode} onChange={e=>setTotpCode(e.target.value.replace(/\D/g,""))}
                style={{ padding:"12px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:20,outline:"none",textAlign:"center",letterSpacing:"0.3em",fontFamily:"monospace" }} />
              <button type="submit" disabled={loading||totpCode.length!==6}
                style={{ padding:"12px",borderRadius:10,border:"none",background:"linear-gradient(90deg,#f97316,#ef4444)",color:"#fff",fontSize:14,fontWeight:700,cursor:"pointer" }}>
                {loading ? <span className="spinner" style={{ borderTopColor:"#fff" }} /> : "✓ Verify"}
              </button>
              <button type="button" onClick={() => { setReq2fa(false); setTotpCode(""); setErr(null); }}
                style={{ padding:"10px",borderRadius:10,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:13,cursor:"pointer" }}>
                Cancel
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Forgot Password Modal */}
      {showForgot && (
        <div style={{ position:"fixed",inset:0,background:"rgba(0,0,0,.7)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:100 }}>
          <div style={{ background:"rgba(14,14,16,.95)",border:"1px solid rgba(99,102,241,.3)",borderRadius:16,padding:"32px 36px",width:360 }}>
            <h3 style={{ fontSize:16,fontWeight:700,color:"#f4f4f5",marginBottom:8 }}>🔑 Forgot Password</h3>
            <p style={{ fontSize:13,color:"#71717a",marginBottom:16 }}>Enter your email and we'll send you a reset link.</p>
            {forgotMsg && (
              <div style={{ padding:"9px 13px",borderRadius:8,border:"1px solid",fontSize:13,marginBottom:12,
                background:forgotMsg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",
                borderColor:forgotMsg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",
                color:forgotMsg.ok?"#34d399":"#f87171" }}>
                {forgotMsg.ok?"✓":"✗"} {forgotMsg.msg}
              </div>
            )}
            {!forgotMsg?.ok && (
              <form onSubmit={submitForgot} style={{ display:"flex",flexDirection:"column",gap:10 }}>
                <input type="email" placeholder="you@company.com" value={forgotEmail}
                  onChange={e=>setForgotEmail(e.target.value)} required
                  style={{ padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:14,outline:"none",fontFamily:"inherit" }} />
                <button type="submit" disabled={forgotLoading}
                  style={{ padding:"12px",borderRadius:10,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:14,fontWeight:700,cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",gap:8 }}>
                  {forgotLoading ? <span className="spinner" style={{ borderTopColor:"#fff" }} /> : "Send Reset Link"}
                </button>
              </form>
            )}
            <button type="button" onClick={() => { setShowForgot(false); setForgotMsg(null); }}
              style={{ marginTop:12,padding:"10px",borderRadius:10,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:13,cursor:"pointer",width:"100%" }}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}