import { useEffect, useState } from "react";
import { api } from "../api/client";
import useAuth from "../store/auth";

// ── Theme engine ──────────────────────────────────────────────────────────────
export function applyTheme(theme) {
  const root = document.documentElement;
  if (theme === "light") {
    root.style.setProperty("--bg-primary",   "#f8fafc");
    root.style.setProperty("--bg-secondary", "#f1f5f9");
    root.style.setProperty("--bg-card",      "#ffffff");
    root.style.setProperty("--text-primary",  "#0f172a");
    root.style.setProperty("--text-secondary","#475569");
    root.style.setProperty("--border",        "rgba(0,0,0,.1)");
    document.body.style.background = "#f8fafc";
    document.body.style.color      = "#0f172a";
    root.setAttribute("data-theme", "light");
  } else {
    root.style.setProperty("--bg-primary",   "#09090b");
    root.style.setProperty("--bg-secondary", "#18181b");
    root.style.setProperty("--bg-card",      "#18181b");
    root.style.setProperty("--text-primary",  "#e4e4e7");
    root.style.setProperty("--text-secondary","#71717a");
    root.style.setProperty("--border",        "rgba(255,255,255,.08)");
    document.body.style.background = "#09090b";
    document.body.style.color      = "#e4e4e7";
    root.setAttribute("data-theme", "dark");
  }
}

const TABS = ["🔑 API & Models","🎨 Appearance","📊 Data Preferences","🔔 Notifications","🔒 Security","⚠️ Danger Zone"];
const AIML_MODELS = ["google/gemma-3-4b-it","google/gemma-3-12b-it","google/gemma-3-27b-it","meta-llama/Llama-3.2-3B-Instruct-Turbo","meta-llama/Llama-3.3-70B-Instruct-Turbo","mistralai/Mistral-7B-Instruct-v0.2","mistralai/Mixtral-8x7B-Instruct-v0.1","microsoft/Phi-3-mini-4k-instruct","Qwen/Qwen2.5-7B-Instruct-Turbo","Qwen/Qwen2.5-72B-Instruct-Turbo","deepseek-ai/DeepSeek-R1","deepseek-ai/DeepSeek-V3"];

export default function Settings() {
  const [tab, setTab] = useState(0);
  const { getPayload } = useAuth();
  const payload = getPayload();
  const isAdmin = payload?.role === "admin";

  return (
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={S.icon}>⚙️</div>
          <div>
            <div style={S.title}>Settings</div>
            <div style={S.sub}>Manage your preferences and account</div>
          </div>
        </div>
      </div>
      <div style={S.tabs}>
        {TABS.map((t,i)=>(
          <button key={t} onClick={()=>setTab(i)} style={{...S.tab,borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent",color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>
      {tab===0 && <APIModelsTab />}
      {tab===1 && <AppearanceTab />}
      {tab===2 && <DataPrefsTab />}
      {tab===3 && <NotificationsTab isAdmin={isAdmin} />}
      {tab===4 && <SecurityTab />}
      {tab===5 && <DangerZoneTab />}
    </div>
  );
}

function APIModelsTab() {
  const [openaiKey, setOpenaiKey] = useState(()=>localStorage.getItem("openai_key")||"");
  const [aimlKey, setAimlKey]     = useState(()=>localStorage.getItem("aiml_key")||"");
  const [aimlModel, setAimlModel] = useState(()=>localStorage.getItem("aiml_model")||AIML_MODELS[0]);
  const [msg, setMsg]             = useState({});
  const [testing, setTesting]     = useState({});

  const testKey = async (provider) => {
    setTesting(t=>({...t,[provider]:true}));
    try {
      const { data } = await api.post("/ai/test-key", { provider, key: provider==="openai"?openaiKey:aimlKey, model: provider==="aiml"?aimlModel:undefined });
      setMsg(m=>({...m,[provider]:{ok:data.success,t:data.message||"Connected"}}));
    } catch(e) {
      setMsg(m=>({...m,[provider]:{ok:false,t:e.response?.data?.detail||"Test failed"}}));
    } finally { setTesting(t=>({...t,[provider]:false})); }
  };

  const save = () => {
    localStorage.setItem("openai_key", openaiKey);
    localStorage.setItem("aiml_key", aimlKey);
    localStorage.setItem("aiml_model", aimlModel);
    api.post("/config/keys", { openai_key: openaiKey, aiml_key: aimlKey, aiml_model: aimlModel }).catch(()=>{});
    setMsg(m=>({...m,save:{ok:true,t:"Keys saved"}}));
    setTimeout(()=>setMsg(m=>({...m,save:null})),2500);
  };

  const activeProvider = openaiKey ? "openai" : aimlKey ? "aiml" : null;

  return (
    <div style={{maxWidth:680}}>
      {msg.save && <Alert ok={msg.save.ok} t={msg.save.t} />}
      <Section title="OpenAI Configuration">
        <Label>API Key</Label>
        <div style={{display:"flex",gap:8,marginBottom:8}}>
          <input type="password" value={openaiKey} onChange={e=>setOpenaiKey(e.target.value)} placeholder="sk-…" style={{...S.input,flex:1}} />
          <button onClick={()=>testKey("openai")} disabled={!openaiKey||testing.openai} style={S.outlineBtn}>
            {testing.openai?"Testing…":"Test"}
          </button>
        </div>
        {msg.openai && <Alert ok={msg.openai.ok} t={msg.openai.t} />}
      </Section>

      <Section title="AIML API Configuration">
        <Label>API Key</Label>
        <div style={{display:"flex",gap:8,marginBottom:10}}>
          <input type="password" value={aimlKey} onChange={e=>setAimlKey(e.target.value)} placeholder="aiml-…" style={{...S.input,flex:1}} />
          <button onClick={()=>testKey("aiml")} disabled={!aimlKey||testing.aiml} style={S.outlineBtn}>
            {testing.aiml?"Testing…":"Test"}
          </button>
        </div>
        <Label>Model</Label>
        <select value={aimlModel} onChange={e=>setAimlModel(e.target.value)} style={{...S.select,width:"100%",marginBottom:8}}>
          {AIML_MODELS.map(m=><option key={m} value={m}>{m}</option>)}
        </select>
        {msg.aiml && <Alert ok={msg.aiml.ok} t={msg.aiml.t} />}
      </Section>

      <Section title="Active Provider">
        <div style={{display:"flex",gap:12,flexWrap:"wrap"}}>
          {[["openai","OpenAI GPT","🤖"],["aiml","AIML API","⚡"]].map(([id,name,icon])=>(
            <div key={id} style={{flex:"1 1 200px",padding:"14px 18px",borderRadius:12,border:`1px solid ${activeProvider===id?"#6366f1":"rgba(255,255,255,.06)"}`,background:activeProvider===id?"rgba(99,102,241,.08)":"rgba(24,24,27,.8)",position:"relative"}}>
              <div style={{fontSize:22,marginBottom:6}}>{icon}</div>
              <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>{name}</div>
              <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{activeProvider===id?"Active provider":"Not configured"}</div>
              {activeProvider===id && <div style={{position:"absolute",top:10,right:10,width:8,height:8,borderRadius:"50%",background:"#22c55e",boxShadow:"0 0 6px #22c55e"}} />}
            </div>
          ))}
        </div>
      </Section>

      <button onClick={save} style={S.btn}>💾 Save Keys</button>
      <div style={{marginTop:24}}>
        <APIKeyManager />
      </div>
    </div>
  );
}

function AppearanceTab() {
  const [theme, setTheme] = useState(()=>localStorage.getItem("theme")||"dark");

  const pick = (t) => {
    setTheme(t);
    localStorage.setItem("theme", t);
    // Apply theme immediately
    applyTheme(t);
  };

  return (
    <div style={{maxWidth:500}}>
      <Section title="Color Theme">
        <div style={{display:"flex",gap:14}}>
          {[["dark","🌙 Dark Mode"],["light","☀️ Light Mode"]].map(([id,label])=>(
            <div key={id} onClick={()=>pick(id)} style={{flex:1,padding:"20px 16px",borderRadius:14,border:`2px solid ${theme===id?"#6366f1":"rgba(255,255,255,.1)"}`,background:theme===id?"rgba(99,102,241,.08)":"rgba(24,24,27,.5)",cursor:"pointer",textAlign:"center",position:"relative",transition:"all .2s"}}>
              <div style={{fontSize:36,marginBottom:10}}>{id==="dark"?"🌙":"☀️"}</div>
              <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5"}}>{label}</div>
              {theme===id && <div style={{position:"absolute",top:10,right:10,width:8,height:8,borderRadius:"50%",background:"#6366f1",boxShadow:"0 0 6px #6366f1"}} />}
            </div>
          ))}
        </div>
        <p style={{fontSize:12,color:"#52525b",marginTop:12}}>Theme is applied immediately and saved for future sessions.</p>
      </Section>
    </div>
  );
}

function DataPrefsTab() {
  const load = (k,d) => { const v=localStorage.getItem(k); return v!==null?Number(v):d; };
  const loadB = (k,d) => { const v=localStorage.getItem(k); return v!==null?v==="true":d; };
  const loadS = (k,d) => localStorage.getItem(k)||d;
  const [tableRows, setTableRows]   = useState(()=>load("pref_table_rows",50));
  const [maxCols, setMaxCols]       = useState(()=>load("pref_max_cols",20));
  const [decimals, setDecimals]     = useState(()=>load("pref_decimals",2));
  const [chartH, setChartH]         = useState(()=>load("pref_chart_height",400));
  const [autoClean, setAutoClean]   = useState(()=>loadB("pref_auto_clean",false));
  const [autoDetect, setAutoDetect] = useState(()=>loadB("pref_auto_detect",true));
  const [dateFormat, setDateFormat] = useState(()=>loadS("pref_date_format","MM/DD/YYYY"));
  const [chartType, setChartType]   = useState(()=>loadS("pref_chart_type","Bar"));
  const [chartTheme, setChartTheme] = useState(()=>loadS("pref_chart_theme","plotly_dark"));
  const [sampleSize, setSampleSize] = useState(()=>load("pref_sample_size",10000));
  const [largeThreshold, setLargeThreshold] = useState(()=>load("pref_large_threshold",100000));
  const [saved, setSaved]           = useState(false);

  const save = () => {
    const prefs = { pref_table_rows:tableRows, pref_max_cols:maxCols, pref_decimals:decimals,
      pref_chart_height:chartH, pref_auto_clean:autoClean, pref_auto_detect:autoDetect,
      pref_date_format:dateFormat, pref_chart_type:chartType, pref_chart_theme:chartTheme,
      pref_sample_size:sampleSize, pref_large_threshold:largeThreshold };
    Object.entries(prefs).forEach(([k,v])=>localStorage.setItem(k,v));
    setSaved(true); setTimeout(()=>setSaved(false),2000);
  };

  const Slider = ({label,val,set,min,max,unit=""}) => (
    <div style={{marginBottom:16}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
        <Label>{label}</Label>
        <span style={{fontSize:12,color:"#6366f1",fontWeight:600}}>{val.toLocaleString()}{unit}</span>
      </div>
      <input type="range" min={min} max={max} value={val} onChange={e=>set(Number(e.target.value))}
        style={{width:"100%",accentColor:"#6366f1"}} />
      <div style={{display:"flex",justifyContent:"space-between",fontSize:10,color:"#3f3f46",marginTop:2}}>
        <span>{min.toLocaleString()}{unit}</span><span>{max.toLocaleString()}{unit}</span>
      </div>
    </div>
  );

  const Sel = ({label,val,set,opts}) => (
    <div style={{marginBottom:14}}>
      <Label>{label}</Label>
      <select value={val} onChange={e=>set(e.target.value)} style={{...S.select,width:"100%"}}>
        {opts.map(o=><option key={o}>{o}</option>)}
      </select>
    </div>
  );

  return (
    <div style={{maxWidth:560}}>
      {saved && <Alert ok={true} t="Preferences saved" />}
      <Section title="Table & Display">
        <Slider label="Table Rows per Page" val={tableRows} set={setTableRows} min={10} max={500} />
        <Slider label="Max Columns Shown" val={maxCols} set={setMaxCols} min={5} max={50} />
        <Slider label="Decimal Places" val={decimals} set={setDecimals} min={0} max={8} />
        <Sel label="Date Format" val={dateFormat} set={setDateFormat} opts={["MM/DD/YYYY","DD/MM/YYYY","YYYY-MM-DD","MMM DD, YYYY"]} />
      </Section>
      <Section title="Charts">
        <Slider label="Default Chart Height" val={chartH} set={setChartH} min={250} max={800} unit="px" />
        <Sel label="Default Chart Type" val={chartType} set={setChartType} opts={["Bar","Line","Scatter","Histogram","Pie"]} />
        <Sel label="Default Chart Theme" val={chartTheme} set={setChartTheme} opts={["plotly_dark","plotly","ggplot2","seaborn","simple_white"]} />
      </Section>
      <Section title="Performance">
        <Slider label="Sample Size (large datasets)" val={sampleSize} set={setSampleSize} min={1000} max={100000} />
        <Slider label="Large Dataset Threshold" val={largeThreshold} set={setLargeThreshold} min={10000} max={1000000} />
      </Section>
      <Section title="Automation">
        <CheckRow label="Auto-clean data on upload" checked={autoClean} onChange={setAutoClean} desc="Automatically remove duplicates and fill missing values" />
        <CheckRow label="Auto-detect column types" checked={autoDetect} onChange={setAutoDetect} desc="Infer numeric, categorical, and date columns automatically" />
      </Section>
      <button onClick={save} style={S.btn}>💾 Save Preferences</button>
    </div>
  );
}

function NotificationsTab({ isAdmin }) {
  const loadB = (k,d) => { const v=localStorage.getItem(k); return v!==null?v==="true":d; };
  const [notifs, setNotifs] = useState({
    upload:  loadB("notif_upload",true),
    ai:      loadB("notif_ai",true),
    export:  loadB("notif_export",true),
    error:   loadB("notif_error",true),
    automl:  loadB("notif_automl",false),
    schedule:loadB("notif_schedule",false),
  });
  const [sound, setSound]   = useState(()=>localStorage.getItem("notif_sound")||"none");
  const [smtp, setSmtp]     = useState({ smtp_host:"smtp.gmail.com", smtp_port:587, smtp_user:"", smtp_password:"", admin_email:"", alert_enabled:false });
  const [msg, setMsg]       = useState(null);
  const [testing, setTest]  = useState(false);

  useEffect(()=>{
    if(isAdmin) api.get("/config/smtp").then(({data})=>setSmtp(data)).catch(()=>{});
  },[isAdmin]);

  const saveNotifs = () => {
    Object.entries(notifs).forEach(([k,v])=>localStorage.setItem(`notif_${k}`,v));
    localStorage.setItem("notif_sound", sound);
    setMsg({ok:true,t:"Notification preferences saved"});
    setTimeout(()=>setMsg(null),2500);
  };

  const previewSound = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      if (sound === "chime") {
        osc.frequency.value = 880; osc.type = "sine";
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
        osc.start(); osc.stop(ctx.currentTime + 0.5);
      } else if (sound === "pop") {
        osc.frequency.value = 440; osc.type = "square";
        gain.gain.setValueAtTime(0.1, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
        osc.start(); osc.stop(ctx.currentTime + 0.1);
      } else if (sound === "bell") {
        osc.frequency.value = 1047; osc.type = "sine";
        gain.gain.setValueAtTime(0.2, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
        osc.start(); osc.stop(ctx.currentTime + 0.8);
      }
    } catch {}
  };

  const saveSmtp = async () => {
    try { await api.post("/config/smtp", smtp); setMsg({ok:true,t:"SMTP configuration saved"}); }
    catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Failed to save SMTP"}); }
  };

  const testEmail = async () => {
    setTest(true);
    try {
      const {data} = await api.post("/config/smtp/test", smtp);
      setMsg({ok:data.success,t:data.message||"Test email sent"});
    } catch(e) { setMsg({ok:false,t:e.response?.data?.detail||"Test failed"}); }
    finally { setTest(false); }
  };

  const notifItems = [
    ["upload","📤 Upload Notifications","Alert when dataset upload completes"],
    ["ai","🤖 AI Analysis Alerts","Notify when AI analysis finishes"],
    ["export","📥 Export Notifications","Alert when report export is ready"],
    ["error","❌ Error Alerts","Notify on system errors"],
    ["automl","🧠 AutoML Completion","Alert when ML training completes"],
    ["schedule","⏰ Scheduled Tasks","Notify on scheduled job results"],
  ];

  return (
    <div style={{maxWidth:640}}>
      {msg && <Alert ok={msg.ok} t={msg.t} />}
      <Section title="In-App Notifications">
        {notifItems.map(([k,label,desc])=>(
          <CheckRow key={k} label={label} checked={notifs[k]} onChange={v=>setNotifs(n=>({...n,[k]:v}))} desc={desc} />
        ))}
      </Section>

      <Section title="Notification Sound">
        <div style={{display:"flex",gap:10,alignItems:"center",marginBottom:10}}>
          <select value={sound} onChange={e=>setSound(e.target.value)} style={{...S.select,flex:1}}>
            <option value="none">None</option>
            <option value="chime">Subtle Chime</option>
            <option value="pop">Pop</option>
            <option value="bell">Success Bell</option>
          </select>
          <button onClick={previewSound} disabled={sound==="none"} style={S.outlineBtn}>▶ Preview</button>
        </div>
      </Section>

      <button onClick={saveNotifs} style={{...S.btn,marginBottom:24}}>💾 Save Notification Settings</button>

      {isAdmin && (
        <Section title="📧 SMTP Email Configuration">
          <p style={{fontSize:12,color:"#52525b",marginBottom:14}}>Configure SMTP to send email alerts. Gmail: enable 2FA → App Passwords.</p>
          {[["SMTP Host","smtp_host","text"],["SMTP Port","smtp_port","number"],["SMTP User","smtp_user","email"],["App Password","smtp_password","password"],["Admin Email","admin_email","email"]].map(([label,key,type])=>(
            <div key={key} style={{marginBottom:10}}>
              <Label>{label}</Label>
              <input type={type} value={smtp[key]||""} onChange={e=>setSmtp(s=>({...s,[key]:e.target.value}))} style={{...S.input,width:"100%",boxSizing:"border-box"}} />
            </div>
          ))}
          <CheckRow label="Enable email alerts" checked={smtp.alert_enabled||false} onChange={v=>setSmtp(s=>({...s,alert_enabled:v}))} desc="Send email on login/logout/register/failed auth events" />
          <div style={{display:"flex",gap:8,marginTop:12}}>
            <button onClick={saveSmtp} style={S.btn}>💾 Save SMTP</button>
            <button onClick={testEmail} disabled={testing} style={S.outlineBtn}>{testing?"Sending…":"📨 Test Email"}</button>
          </div>
        </Section>
      )}
    </div>
  );
}

function SecurityTab() {
  const [pw, setPw]       = useState({current:"",newPw:"",confirm:""});
  const [pwMsg, setPwMsg] = useState(null);
  const [pwLoad, setPwLoad]= useState(false);
  const [twofa, setTwofa] = useState(null); // null=loading, {enabled,secret,qr_uri}
  const [qrData, setQrData]= useState(null);
  const [code, setCode]   = useState("");
  const [tfMsg, setTfMsg] = useState(null);
  const [tfLoad, setTfLoad]= useState(false);

  useEffect(()=>{
    api.get("/profile/2fa-status").then(({data})=>setTwofa(data)).catch(()=>setTwofa({enabled:false}));
  },[]);

  const changePassword = async () => {
    if(pw.newPw!==pw.confirm){setPwMsg({ok:false,t:"Passwords do not match"});return;}
    if(pw.newPw.length<8){setPwMsg({ok:false,t:"Password must be at least 8 characters"});return;}
    setPwLoad(true);
    try {
      await api.post("/profile/change-password",{old_password:pw.current,new_password:pw.newPw});
      setPwMsg({ok:true,t:"Password changed successfully"});
      setPw({current:"",newPw:"",confirm:""});
    } catch(e){setPwMsg({ok:false,t:e.response?.data?.detail||"Failed"});}
    finally{setPwLoad(false);}
  };

  const setup2fa = async () => {
    setTfLoad(true);
    try {
      const {data} = await api.post("/auth/2fa/setup");
      setQrData(data);
      setTfMsg(null);
    } catch(e){setTfMsg({ok:false,t:e.response?.data?.detail||"Setup failed"});}
    finally{setTfLoad(false);}
  };

  const confirm2fa = async () => {
    setTfLoad(true);
    try {
      await api.post("/auth/2fa/confirm",{code});
      setTwofa(t=>({...t,enabled:true}));
      setQrData(null); setCode("");
      setTfMsg({ok:true,t:"2FA enabled successfully"});
    } catch(e){setTfMsg({ok:false,t:e.response?.data?.detail||"Invalid code"});}
    finally{setTfLoad(false);}
  };

  const disable2fa = async () => {
    if(!code){setTfMsg({ok:false,t:"Enter your 2FA code to disable"});return;}
    setTfLoad(true);
    try {
      await api.post("/auth/2fa/disable",{code});
      setTwofa(t=>({...t,enabled:false}));
      setCode("");
      setTfMsg({ok:true,t:"2FA disabled"});
    } catch(e){setTfMsg({ok:false,t:e.response?.data?.detail||"Invalid code"});}
    finally{setTfLoad(false);}
  };

  return (
    <div style={{maxWidth:560}}>
      <Section title="🔑 Change Password">
        {pwMsg && <Alert ok={pwMsg.ok} t={pwMsg.t} />}
        {[["Current Password","current","password"],["New Password","newPw","password"],["Confirm New Password","confirm","password"]].map(([label,key,type])=>(
          <div key={key} style={{marginBottom:10}}>
            <Label>{label}</Label>
            <input type={type} value={pw[key]} onChange={e=>setPw(p=>({...p,[key]:e.target.value}))} style={{...S.input,width:"100%",boxSizing:"border-box"}} />
          </div>
        ))}
        <button onClick={changePassword} disabled={pwLoad||!pw.current||!pw.newPw||!pw.confirm} style={{...S.btn,marginTop:4}}>
          {pwLoad?"Changing…":"🔑 Change Password"}
        </button>
      </Section>

      <Section title="🛡️ Two-Factor Authentication">
        {tfMsg && <Alert ok={tfMsg.ok} t={tfMsg.t} />}
        {twofa===null ? <p style={{color:"#52525b",fontSize:13}}>Loading 2FA status…</p> : (
          <>
            <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}>
              <div style={{width:10,height:10,borderRadius:"50%",background:twofa.enabled?"#22c55e":"#52525b",boxShadow:twofa.enabled?"0 0 6px #22c55e":"none"}} />
              <span style={{fontSize:13,color:twofa.enabled?"#34d399":"#71717a"}}>{twofa.enabled?"2FA is enabled":"2FA is disabled"}</span>
            </div>
            {!twofa.enabled && !qrData && (
              <button onClick={setup2fa} disabled={tfLoad} style={S.btn}>{tfLoad?"Setting up…":"🛡️ Enable 2FA"}</button>
            )}
            {qrData && (
              <div style={{padding:"16px",borderRadius:12,background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",marginBottom:12}}>
                <p style={{fontSize:13,color:"#a1a1aa",marginBottom:12}}>Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)</p>
                <img src={`https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(qrData.qr_uri)}`}
                  alt="2FA QR Code" style={{display:"block",margin:"0 auto 12px",borderRadius:8,background:"#fff",padding:8}} />
                <p style={{fontSize:11,color:"#52525b",textAlign:"center",marginBottom:12}}>Secret: <code style={{color:"#818cf8"}}>{qrData.secret}</code></p>
                <Label>Enter 6-digit code to confirm</Label>
                <div style={{display:"flex",gap:8}}>
                  <input value={code} onChange={e=>setCode(e.target.value)} placeholder="000000" maxLength={6}
                    style={{...S.input,flex:1,letterSpacing:"0.2em",textAlign:"center",fontSize:18}} />
                  <button onClick={confirm2fa} disabled={tfLoad||code.length!==6} style={S.btn}>{tfLoad?"Verifying…":"Confirm"}</button>
                </div>
              </div>
            )}
            {twofa.enabled && (
              <div>
                <p style={{fontSize:13,color:"#71717a",marginBottom:10}}>Enter your current 2FA code to disable two-factor authentication.</p>
                <div style={{display:"flex",gap:8}}>
                  <input value={code} onChange={e=>setCode(e.target.value)} placeholder="000000" maxLength={6}
                    style={{...S.input,flex:1,letterSpacing:"0.2em",textAlign:"center",fontSize:18}} />
                  <button onClick={disable2fa} disabled={tfLoad||!code} style={{...S.btn,background:"rgba(239,68,68,.15)",border:"1px solid rgba(239,68,68,.3)",color:"#f87171"}}>
                    {tfLoad?"Disabling…":"Disable 2FA"}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </Section>
    </div>
  );
}

function DangerZoneTab() {
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg]         = useState(null);

  const clearLocal = () => {
    const keep = ["token"];
    const keys = Object.keys(localStorage).filter(k=>!keep.includes(k));
    keys.forEach(k=>localStorage.removeItem(k));
    setMsg({ok:true,t:`Cleared ${keys.length} local storage entries`});
  };

  const resetPrefs = () => {
    const prefKeys = Object.keys(localStorage).filter(k=>k.startsWith("pref_")||k.startsWith("notif_")||k==="theme");
    prefKeys.forEach(k=>localStorage.removeItem(k));
    setMsg({ok:true,t:"Preferences reset to defaults"});
  };

  const deleteAccount = async () => {
    if(confirm!=="DELETE"){setMsg({ok:false,t:'Type "DELETE" to confirm account deletion'});return;}
    try {
      await api.delete("/profile/account");
      localStorage.clear();
      window.location.href="/login";
    } catch(e){setMsg({ok:false,t:e.response?.data?.detail||"Failed to delete account"});}
  };

  return (
    <div style={{maxWidth:560}}>
      {msg && <Alert ok={msg.ok} t={msg.t} />}
      <div style={{padding:"16px",borderRadius:12,border:"1px solid rgba(239,68,68,.2)",background:"rgba(239,68,68,.04)",marginBottom:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"#f87171",marginBottom:4}}>⚠️ Danger Zone</div>
        <p style={{fontSize:12,color:"#71717a",margin:0}}>These actions are irreversible. Proceed with caution.</p>
      </div>

      <Section title="Clear Local Data">
        <p style={{fontSize:13,color:"#71717a",marginBottom:10}}>Remove all locally stored data including API keys, preferences, and cached settings. Your account data on the server is not affected.</p>
        <button onClick={clearLocal} style={{...S.btn,background:"rgba(245,158,11,.1)",border:"1px solid rgba(245,158,11,.3)",color:"#f59e0b"}}>🗑️ Clear Local Data</button>
      </Section>

      <Section title="Reset Preferences">
        <p style={{fontSize:13,color:"#71717a",marginBottom:10}}>Reset all display preferences and notification settings to their default values.</p>
        <button onClick={resetPrefs} style={{...S.btn,background:"rgba(245,158,11,.1)",border:"1px solid rgba(245,158,11,.3)",color:"#f59e0b"}}>↺ Reset Preferences</button>
      </Section>

      <Section title="Delete Account">
        <p style={{fontSize:13,color:"#f87171",marginBottom:10}}>Permanently delete your account and all associated data. This cannot be undone.</p>
        <Label>Type "DELETE" to confirm</Label>
        <div style={{display:"flex",gap:8}}>
          <input value={confirm} onChange={e=>setConfirm(e.target.value)} placeholder='Type "DELETE"'
            style={{...S.input,flex:1,borderColor:"rgba(239,68,68,.3)"}} />
          <button onClick={deleteAccount} style={{...S.btn,background:"rgba(239,68,68,.15)",border:"1px solid rgba(239,68,68,.4)",color:"#f87171"}}>
            🗑️ Delete Account
          </button>
        </div>
      </Section>
    </div>
  );
}

// ── API Key Manager (multi-key rotation) ─────────────────────────────────────
function APIKeyManager() {
  const PROVIDERS = ["OpenAI", "AIML"];
  const [activeTab, setActiveTab] = useState(0);
  const [keys, setKeys] = useState({ OpenAI: [], AIML: [] });
  const [newKey, setNewKey] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [msg, setMsg] = useState(null);

  // Load from localStorage
  const loadKeys = () => {
    try {
      const stored = JSON.parse(localStorage.getItem("key_manager") || "{}");
      setKeys({ OpenAI: stored.OpenAI || [], AIML: stored.AIML || [] });
    } catch { setKeys({ OpenAI: [], AIML: [] }); }
  };

  const saveKeys = (updated) => {
    localStorage.setItem("key_manager", JSON.stringify(updated));
    setKeys(updated);
  };

  useEffect(() => { loadKeys(); }, []);

  const provider = PROVIDERS[activeTab];
  const providerKeys = keys[provider] || [];
  const stats = {
    total: providerKeys.length,
    ready: providerKeys.filter(k => k.status === "ready").length,
    cooldown: providerKeys.filter(k => k.status === "cooldown").length,
    paused: providerKeys.filter(k => k.status === "paused").length,
    calls: providerKeys.reduce((a, k) => a + (k.calls || 0), 0),
  };

  const addKey = () => {
    if (!newKey.trim()) return;
    const updated = {
      ...keys,
      [provider]: [...providerKeys, {
        id: Date.now(), key: newKey.trim(), label: newLabel || `Key ${providerKeys.length + 1}`,
        status: "ready", calls: 0, added: new Date().toISOString(),
      }]
    };
    saveKeys(updated);
    setNewKey(""); setNewLabel("");
    setMsg({ ok: true, t: "Key added" });
    setTimeout(() => setMsg(null), 2000);
  };

  const toggleStatus = (id) => {
    const updated = {
      ...keys,
      [provider]: providerKeys.map(k => k.id === id
        ? { ...k, status: k.status === "paused" ? "ready" : "paused" }
        : k)
    };
    saveKeys(updated);
  };

  const deleteKey = (id) => {
    const updated = { ...keys, [provider]: providerKeys.filter(k => k.id !== id) };
    saveKeys(updated);
  };

  const resetCooldowns = () => {
    const updated = {
      ...keys,
      [provider]: providerKeys.map(k => ({ ...k, status: k.status === "cooldown" ? "ready" : k.status }))
    };
    saveKeys(updated);
    setMsg({ ok: true, t: "Cooldowns reset" });
    setTimeout(() => setMsg(null), 2000);
  };

  const statusColor = { ready: "#22c55e", cooldown: "#f59e0b", paused: "#52525b" };

  return (
    <Section title="API Key Manager (Multi-Key Rotation)">
      {msg && <Alert ok={msg.ok} t={msg.t} />}
      {/* Provider tabs */}
      <div style={{ display:"flex", gap:4, marginBottom:14, borderBottom:"1px solid rgba(255,255,255,.06)" }}>
        {PROVIDERS.map((p, i) => (
          <button key={p} onClick={() => setActiveTab(i)}
            style={{ padding:"6px 14px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer",
              borderBottom:activeTab===i?"2px solid #6366f1":"2px solid transparent", color:activeTab===i?"#818cf8":"#52525b" }}>
            {p} Keys
          </button>
        ))}
      </div>
      {/* Stats row */}
      <div style={{ display:"flex", gap:10, marginBottom:14, flexWrap:"wrap" }}>
        {[["Total", stats.total, "#6366f1"], ["Ready", stats.ready, "#22c55e"],
          ["Cooldown", stats.cooldown, "#f59e0b"], ["Paused", stats.paused, "#52525b"],
          ["Total Calls", stats.calls, "#818cf8"]].map(([l, v, c]) => (
          <div key={l} style={{ flex:"1 1 80px", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:10, padding:"10px 14px" }}>
            <div style={{ fontSize:18, fontWeight:700, color:c }}>{v}</div>
            <div style={{ fontSize:10, color:"#52525b", marginTop:2 }}>{l}</div>
          </div>
        ))}
      </div>
      {/* Add key form */}
      <div style={{ display:"flex", gap:8, marginBottom:14, flexWrap:"wrap" }}>
        <input type="password" value={newKey} onChange={e => setNewKey(e.target.value)}
          placeholder={`${provider} API key…`}
          style={{ ...S.input, flex:2, minWidth:200 }} />
        <input value={newLabel} onChange={e => setNewLabel(e.target.value)}
          placeholder="Label (optional)"
          style={{ ...S.input, flex:1, minWidth:120 }} />
        <button onClick={addKey} disabled={!newKey.trim()} style={S.btn}>+ Add Key</button>
      </div>
      {/* Keys list */}
      <div style={{ display:"flex", flexDirection:"column", gap:6, marginBottom:10 }}>
        {providerKeys.length === 0 && <p style={{ fontSize:12, color:"#52525b" }}>No keys added yet.</p>}
        {providerKeys.map(k => (
          <div key={k.id} style={{ display:"flex", alignItems:"center", gap:10, padding:"10px 14px",
            background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:10 }}>
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ fontSize:12, fontWeight:600, color:"#f4f4f5" }}>{k.label}</div>
              <div style={{ fontSize:11, color:"#52525b", fontFamily:"monospace" }}>
                {k.key.slice(0, 8)}{"•".repeat(12)}{k.key.slice(-4)}
              </div>
            </div>
            <span style={{ fontSize:10, padding:"2px 8px", borderRadius:20, fontWeight:600,
              background:`${statusColor[k.status]}18`, color:statusColor[k.status] }}>
              {k.status.toUpperCase()}
            </span>
            <span style={{ fontSize:11, color:"#52525b" }}>{k.calls} calls</span>
            <button onClick={() => toggleStatus(k.id)}
              style={{ padding:"4px 10px", borderRadius:6, border:"1px solid rgba(255,255,255,.09)",
                background:"transparent", color:"#71717a", fontSize:11, cursor:"pointer" }}>
              {k.status === "paused" ? "▶ Resume" : "⏸ Pause"}
            </button>
            <button onClick={() => deleteKey(k.id)}
              style={{ padding:"4px 10px", borderRadius:6, border:"1px solid rgba(239,68,68,.3)",
                background:"transparent", color:"#f87171", fontSize:11, cursor:"pointer" }}>
              Delete
            </button>
          </div>
        ))}
      </div>
      {stats.cooldown > 0 && (
        <button onClick={resetCooldowns} style={{ ...S.btn, background:"rgba(245,158,11,.15)", color:"#f59e0b", border:"1px solid rgba(245,158,11,.3)" }}>
          ↺ Reset All Cooldowns
        </button>
      )}
    </Section>
  );
}

// ── Shared helpers ──────────────────────────────────────────────────────────
function Section({title,children}){
  return <div style={{marginBottom:24}}><div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:12}}>{title}</div>{children}</div>;
}
function Label({children}){return <label style={{fontSize:12,color:"#71717a",display:"block",marginBottom:4}}>{children}</label>;}
function Alert({ok,t}){
  return <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid",fontSize:13,marginBottom:12,background:ok?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)",borderColor:ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:ok?"#34d399":"#f87171"}}>{t}</div>;
}
function CheckRow({label,checked,onChange,desc}){
  return (
    <label style={{display:"flex",alignItems:"flex-start",gap:10,cursor:"pointer",marginBottom:12}}>
      <input type="checkbox" checked={checked} onChange={e=>onChange(e.target.checked)} style={{accentColor:"#6366f1",marginTop:2,flexShrink:0}} />
      <div><div style={{fontSize:13,color:"#f4f4f5"}}>{label}</div>{desc&&<div style={{fontSize:11,color:"#52525b",marginTop:2}}>{desc}</div>}</div>
    </label>
  );
}

const S = {
  page:      { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar:    { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 },
  icon:      { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:     { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:       { fontSize:11, color:"#52525b" },
  tabs:      { display:"flex", gap:2, marginBottom:20, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:       { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  btn:       { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  outlineBtn:{ padding:"9px 16px", borderRadius:10, border:"1px solid rgba(99,102,241,.4)", background:"transparent", color:"#818cf8", fontSize:13, fontWeight:600, cursor:"pointer" },
  input:     { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none", fontFamily:"inherit" },
  select:    { padding:"9px 12px", borderRadius:10, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none" },
};
