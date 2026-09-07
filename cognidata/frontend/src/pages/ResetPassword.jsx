import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [newPass, setNewPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoad] = useState(false);
  const [msg, setMsg] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) setMsg({ ok: false, text: "Invalid reset link — no token found." });
  }, [token]);

  const submit = async (e) => {
    e.preventDefault();
    if (newPass.length < 6) { setMsg({ ok: false, text: "Password must be at least 6 characters." }); return; }
    if (newPass !== confirm) { setMsg({ ok: false, text: "Passwords do not match." }); return; }
    setLoad(true); setMsg(null);
    try {
      await api.post("/auth/reset-password", { token, new_password: newPass });
      setMsg({ ok: true, text: "Password reset successfully! Redirecting to login…" });
      setTimeout(() => navigate("/login"), 2500);
    } catch(e) {
      setMsg({ ok: false, text: e.response?.data?.detail || "Reset failed — link may have expired." });
    } finally { setLoad(false); }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#09090b", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
      <div style={{ width: "100%", maxWidth: 400, background: "rgba(14,14,16,.95)", border: "1px solid rgba(255,255,255,.08)", borderRadius: 20, padding: "32px 36px", boxShadow: "0 40px 80px rgba(0,0,0,.7)" }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>🔑</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#f4f4f5" }}>Reset Password</div>
          <div style={{ fontSize: 13, color: "#52525b", marginTop: 4 }}>Enter your new password below</div>
        </div>

        {msg && (
          <div style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid", fontSize: 13, marginBottom: 16,
            background: msg.ok ? "rgba(16,185,129,.1)" : "rgba(239,68,68,.1)",
            borderColor: msg.ok ? "rgba(16,185,129,.3)" : "rgba(239,68,68,.3)",
            color: msg.ok ? "#34d399" : "#f87171" }}>
            {msg.ok ? "✓" : "✗"} {msg.text}
          </div>
        )}

        {!msg?.ok && token && (
          <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div>
              <label style={{ fontSize: 12, color: "#71717a", display: "block", marginBottom: 4 }}>New Password</label>
              <div style={{ position: "relative" }}>
                <input type={show ? "text" : "password"} value={newPass} onChange={e => setNewPass(e.target.value)}
                  placeholder="At least 6 characters" required
                  style={{ width: "100%", padding: "11px 42px 11px 14px", borderRadius: 10, background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.09)", color: "#f4f4f5", fontSize: 14, outline: "none", boxSizing: "border-box" }} />
                <button type="button" onClick={() => setShow(!show)}
                  style={{ position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)", background: "transparent", border: "none", cursor: "pointer", fontSize: 15, color: "#52525b" }}>
                  {show ? "🙈" : "👁"}
                </button>
              </div>
            </div>

            <div>
              <label style={{ fontSize: 12, color: "#71717a", display: "block", marginBottom: 4 }}>Confirm Password</label>
              <input type={show ? "text" : "password"} value={confirm} onChange={e => setConfirm(e.target.value)}
                placeholder="Repeat new password" required
                style={{ width: "100%", padding: "11px 14px", borderRadius: 10, background: "rgba(255,255,255,.05)", border: `1px solid ${confirm && confirm !== newPass ? "rgba(239,68,68,.4)" : "rgba(255,255,255,.09)"}`, color: "#f4f4f5", fontSize: 14, outline: "none", boxSizing: "border-box" }} />
              {confirm && confirm !== newPass && <span style={{ fontSize: 11, color: "#f87171" }}>Passwords do not match</span>}
            </div>

            <button type="submit" disabled={loading || !newPass || !confirm}
              style={{ padding: "13px", borderRadius: 11, border: "none", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontSize: 15, fontWeight: 700, cursor: "pointer", marginTop: 4, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
              {loading ? <span className="spinner" style={{ borderTopColor: "#fff" }} /> : "🔑 Reset Password"}
            </button>
          </form>
        )}

        <button onClick={() => navigate("/login")}
          style={{ marginTop: 16, width: "100%", padding: "10px", borderRadius: 10, border: "1px solid rgba(255,255,255,.09)", background: "transparent", color: "#71717a", fontSize: 13, cursor: "pointer" }}>
          ← Back to Login
        </button>
      </div>
    </div>
  );
}
