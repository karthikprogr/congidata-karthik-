import { useRef, useState, useCallback } from "react";
import { dataApi } from "../api/client";

export default function FileUpload({ onUploaded }) {
  const ref = useRef();
  const [status, setStatus]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);

  const upload = async (file) => {
    if (!file) return;
    setLoading(true); setStatus(null);
    try {
      const { data } = await dataApi.upload(file);
      setStatus({ ok:true, msg:`${data.rows?.toLocaleString()} rows · ${data.columns} cols` });
      onUploaded?.(data);
    } catch (e) {
      setStatus({ ok:false, msg: e.response?.data?.detail || "Upload failed" });
    } finally { setLoading(false); }
  };

  const handleChange = (e) => upload(e.target.files?.[0]);

  const handleDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) upload(file);
  }, []);

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);

  return (
    <div style={{ display:"flex",flexDirection:"column",gap:6 }}>
      <input ref={ref} type="file" accept=".csv,.xlsx,.xls,.json" style={{ display:"none" }} onChange={handleChange} />
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => ref.current.click()}
        style={{
          display:"flex",alignItems:"center",gap:6,padding:"7px 14px",borderRadius:8,
          border:`1px ${dragging?"solid":"solid"} ${dragging?"rgba(99,102,241,.6)":"rgba(99,102,241,.3)"}`,
          background:dragging?"rgba(99,102,241,.15)":"rgba(99,102,241,.08)",
          color:"#818cf8",cursor:"pointer",fontSize:13,fontWeight:500,
          transition:"all .15s",
        }}>
        {loading ? <span className="spinner" style={{ width:14,height:14 }} /> : "↑"}
        {dragging ? "Drop to upload" : "Upload Dataset"}
      </div>
      {status && <span style={{ fontSize:12,color:status.ok?"#34d399":"#f87171" }}>{status.ok?"✓ ":"✗ "}{status.msg}</span>}
    </div>
  );
}
