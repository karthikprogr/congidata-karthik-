import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "../api/client";
import useAuth from "../store/auth";

export default function OAuthCallback() {
  const [error, setError] = useState(null);
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { setToken } = useAuth();

  useEffect(() => {
    const code = params.get("code");
    const state = params.get("state") || "";
    const provider = sessionStorage.getItem("oauth_provider");
    if (!code || !provider) { setError("Invalid callback."); return; }
    const fn = provider === "google" ? authApi.googleCallback : authApi.githubCallback;
    fn(code, state).then(({ data }) => {
      setToken(data.access_token);
      sessionStorage.removeItem("oauth_provider");
      navigate("/chat", { replace: true });
    }).catch(e => setError(e.response?.data?.detail || "Sign-in failed."));
  }, []);

  return (
    <div style={{ minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:"#09090b" }}>
      <div style={{ display:"flex",flexDirection:"column",alignItems:"center",gap:16,background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.07)",borderRadius:16,padding:"40px 48px" }}>
        {error ? <>
          <p style={{ color:"#f87171",fontSize:14 }}>{error}</p>
          <button onClick={() => navigate("/login")} style={{ padding:"10px 24px",borderRadius:8,border:"none",background:"#6366f1",color:"#fff",cursor:"pointer" }}>Back to Login</button>
        </> : <>
          <span className="spinner" style={{ width:28,height:28 }} />
          <p style={{ color:"#71717a",fontSize:14 }}>Completing sign-in…</p>
        </>}
      </div>
    </div>
  );
}
