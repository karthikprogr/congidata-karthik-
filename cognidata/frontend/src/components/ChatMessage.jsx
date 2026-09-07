import PlotlyChart from "./PlotlyChart";
import Table from "./Table";

const AGENT_COLORS = {
  data:          "#71717a",
  insight:       "#6366f1",
  ml:            "#f59e0b",
  visualization: "#22c55e",
  anomaly:       "#ef4444",
  report:        "#ec4899",
  geo:           "#14b8a6",
  sql:           "#3b82f6",
  rag:           "#8b5cf6",
};

const AGENT_LABELS = {
  data: "📈 Data Agent", insight: "🧠 Insight Agent", ml: "🤖 ML Agent",
  visualization: "📊 Viz Agent", anomaly: "🔍 Anomaly Agent",
  report: "📄 Report Agent", geo: "🌍 Geo Agent", sql: "🗄️ SQL Agent", rag: "📚 RAG Agent",
};

export default function ChatMessage({ role, content }) {
  if (role === "user") {
    return (
      <div className="fade-up flex justify-end">
        <div style={{ maxWidth:"70%",padding:"10px 16px",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",borderRadius:"18px 18px 4px 18px",fontSize:14,lineHeight:1.6,color:"#fff",boxShadow:"0 4px 15px rgba(99,102,241,.25)" }}>
          {content}
        </div>
      </div>
    );
  }

  // Handle streaming placeholder
  if (content?.streaming && !content?.data) {
    return (
      <div className="fade-up" style={{ maxWidth:"85%",alignSelf:"flex-start",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:"4px 18px 18px 18px",padding:"14px 16px" }}>
        <div style={{ display:"flex",gap:4,alignItems:"center" }}>
          {[0,.15,.3].map((d,i) => <span key={i} style={{ width:7,height:7,borderRadius:"50%",background:"#6366f1",display:"inline-block",animation:`dotPulse 1.2s ease-in-out ${d}s infinite` }} />)}
          <span style={{ fontSize:12,color:"#3f3f46",marginLeft:6 }}>Thinking…</span>
        </div>
      </div>
    );
  }

  // Streaming in progress — show partial text
  if (content?.streaming && content?.data) {
    return (
      <div className="fade-up" style={{ maxWidth:"85%",alignSelf:"flex-start",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:"4px 18px 18px 18px",padding:"14px 16px" }}>
        <p style={{ fontSize:14,lineHeight:1.7,color:"#cbd5e1",whiteSpace:"pre-wrap" }}>{content.data}<span style={{ display:"inline-block",width:2,height:14,background:"#6366f1",marginLeft:2,animation:"blink 1s step-end infinite",verticalAlign:"text-bottom" }} /></p>
      </div>
    );
  }

  const { type, data, code, error, task_type, extra } = content || {};
  const accent = AGENT_COLORS[task_type] || "#6366f1";
  const label  = AGENT_LABELS[task_type] || task_type;

  const downloadPDF = () => {
    if (!data?.pdf_b64) return;
    const bytes = atob(data.pdf_b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const blob = new Blob([arr], { type:"application/pdf" });
    const a = document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="report.pdf"; a.click();
  };

  return (
    <div className="fade-up" style={{ maxWidth:"85%",alignSelf:"flex-start",background:"rgba(24,24,27,.8)",backdropFilter:"blur(10px)",border:"1px solid rgba(255,255,255,.06)",borderRadius:"4px 18px 18px 18px",padding:"14px 16px",display:"flex",flexDirection:"column",gap:10,boxShadow:"0 4px 20px rgba(0,0,0,.3)" }}>
      {task_type && <div style={{ display:"inline-flex",alignItems:"center",gap:5,fontSize:11,fontWeight:600,padding:"3px 10px",borderRadius:20,border:"1px solid",textTransform:"uppercase",letterSpacing:"0.05em",alignSelf:"flex-start",background:`${accent}15`,color:accent,borderColor:`${accent}30` }}>{label}</div>}
      {error && <div style={{ padding:"8px 12px",borderRadius:8,background:"rgba(239,68,68,.1)",border:"1px solid rgba(239,68,68,.3)",color:"#f87171",fontSize:13 }}>⚠ {error}</div>}
      {type==="text" && <p style={{ fontSize:14,lineHeight:1.7,color:"#cbd5e1",whiteSpace:"pre-wrap" }}>{data}</p>}
      {type==="table" && <Table data={data} />}
      {type==="chart" && <div style={{ borderRadius:10,overflow:"hidden",background:"rgba(0,0,0,.2)" }}><PlotlyChart figure={data} /></div>}
      {type==="list" && <ul style={{ paddingLeft:4,display:"flex",flexDirection:"column",gap:6 }}>{(Array.isArray(data)?data:[data]).map((item,i) => <li key={i} style={{ fontSize:14,color:"#cbd5e1",display:"flex",gap:8 }}><span style={{ color:accent }}>▸</span>{String(item)}</li>)}</ul>}
      {type==="json" && <pre style={{ fontSize:12,color:"#71717a",overflowX:"auto",background:"rgba(0,0,0,.3)",padding:12,borderRadius:8,lineHeight:1.5 }}>{JSON.stringify(data,null,2)}</pre>}
      {type==="report" && (
        <div style={{ display:"flex",flexDirection:"column",gap:8 }}>
          <div style={{ padding:"12px 16px",borderRadius:10,background:"rgba(236,72,153,.08)",border:"1px solid rgba(236,72,153,.2)" }}>
            <div style={{ fontSize:13,fontWeight:600,color:"#f9a8d4",marginBottom:4 }}>📄 PDF Report Generated</div>
            <div style={{ fontSize:12,color:"#71717a" }}>Size: {data?.size_kb||0} KB · Contains dataset overview, statistics, and AI insights</div>
          </div>
          {data?.pdf_b64 && (
            <button onClick={downloadPDF} style={{ padding:"9px 16px",borderRadius:10,border:"none",background:"linear-gradient(135deg,#ec4899,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:600,cursor:"pointer",alignSelf:"flex-start",display:"flex",alignItems:"center",gap:8 }}>
              ⬇ Download PDF Report
            </button>
          )}
        </div>
      )}
      {type==="chart" && extra && (
        <div style={{ display:"flex",gap:8,marginTop:4,flexWrap:"wrap" }}>
          {extra.cities && <span style={{ fontSize:11,color:"#14b8a6",background:"rgba(20,184,166,.1)",padding:"3px 10px",borderRadius:20 }}>🌍 {extra.cities} cities</span>}
          {extra.anomalies > 0 && <span style={{ fontSize:11,color:"#ef4444",background:"rgba(239,68,68,.1)",padding:"3px 10px",borderRadius:20 }}>⚠️ {extra.anomalies} anomalies</span>}
        </div>
      )}
      {code && <details style={{ marginTop:2 }}><summary style={{ cursor:"pointer",fontSize:12,color:"#3f3f46",userSelect:"none",padding:"4px 0" }}>⌥ View code</summary><pre style={{ marginTop:8,fontSize:12,color:"#a5f3fc",background:"rgba(0,0,0,.4)",padding:"12px 14px",borderRadius:8,overflowX:"auto",lineHeight:1.6,border:"1px solid rgba(165,243,252,.1)" }}>{code}</pre></details>}
    </div>
  );
}
