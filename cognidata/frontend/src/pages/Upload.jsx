import { useEffect, useState, useRef } from "react";
import { api, dataApi } from "../api/client";
import Table from "../components/Table";

export default function Upload() {
  const [info, setInfo]       = useState(null);
  const [preview, setPreview] = useState(null);
  const [stats, setStats]     = useState(null);
  const [loading, setLoad]    = useState(false);
  const [msg, setMsg]         = useState(null);
  const [previewTab, setPreviewTab] = useState(0);
  const [removeDups, setRemoveDups] = useState(true);
  const [fillMissing, setFillMissing] = useState(true);
  const [cleaning, setCleaning] = useState(false);
  const [cleanResult, setCleanResult] = useState(null);
  const [dragging, setDragging] = useState(false);
  // Datasets panel
  const [datasets, setDatasets] = useState([]);
  const [activeDataset, setActiveDataset] = useState(null);
  const [dsLoading, setDsLoading] = useState(false);
  // RAG
  const [ragFiles, setRagFiles] = useState([]);
  const [ragLoading, setRagLoad] = useState(false);
  const [ragMsg, setRagMsg]     = useState(null);
  const [ragChunks, setRagChunks] = useState(0);
  const [showRag, setShowRag]   = useState(false);
  const fileRef = useRef();
  const ragRef  = useRef();
  // RAG Datasets Management (Task 7.1)
  const [ragDatasets, setRagDatasets] = useState([]);
  const [ragDsLoading, setRagDsLoading] = useState(false);

  const loadDatasets = async () => {
    try {
      const { data } = await api.get("/data/datasets");
      setDatasets(data.datasets || []);
      setActiveDataset(data.active || null);
    } catch {}
  };

  const loadInfo = async () => {
    try {
      const [i, p, s] = await Promise.all([
        dataApi.info(), dataApi.preview(10), api.get("/data/stats")
      ]);
      setInfo(i.data); setPreview(p.data); setStats(s.data);
    } catch {}
  };

  const loadRagStatus = async () => {
    try {
      const { data } = await api.get("/rag/status");
      setRagChunks(data.chunks || 0);
    } catch {}
  };

  
  const loadRagDatasets = async () => {
    try {
      const { data } = await api.get("/rag/datasets");
      setRagDatasets(data || []);
    } catch (e) {
      console.error("Failed to load RAG datasets:", e);
    }
  };

  const indexDataset = async (datasetName) => {
    setRagDsLoading(true);
    setMsg(null);
    try {
      const { data } = await api.post(`/rag/index/${encodeURIComponent(datasetName)}`);
      setMsg({ ok: true, t: `✓ Indexed ${datasetName}: ${data.chunk_count} chunks` });
      await loadRagDatasets();
      await loadRagStatus();
    } catch (e) {
      setMsg({ ok: false, t: e.response?.data?.detail || "Indexing failed" });
    } finally {
      setRagDsLoading(false);
    }
  };

  const deleteRagDataset = async (datasetName, e) => {
    e.stopPropagation();
    if (!confirm(`Remove "${datasetName}" from RAG index?`)) return;
    try {
      await api.delete(`/rag/datasets/${encodeURIComponent(datasetName)}`);
      setMsg({ ok: true, t: `✓ Removed ${datasetName} from RAG index` });
      await loadRagDatasets();
      await loadRagStatus();
    } catch (e) {
      setMsg({ ok: false, t: e.response?.data?.detail || "Delete failed" });
    }
  };

  useEffect(() => { loadDatasets(); loadInfo(); loadRagStatus(); loadRagDatasets(); }, []);

  const switchDataset = async (name) => {
    setDsLoading(true);
    try {
      await api.post(`/data/datasets/switch?name=${encodeURIComponent(name)}`);
      setActiveDataset(name);
      await loadInfo();
    } catch (e) {
      setMsg({ ok: false, t: e.response?.data?.detail || "Switch failed" });
    } finally { setDsLoading(false); }
  };

  const deleteDataset = async (name, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/data/datasets/${encodeURIComponent(name)}`);
      await loadDatasets();
      if (name === activeDataset) { setInfo(null); setPreview(null); setStats(null); }
    } catch (err) {
      setMsg({ ok: false, t: err.response?.data?.detail || "Delete failed" });
    }
  };

  const upload = async (file) => {
    if (!file) return;
    setLoad(true); setMsg(null); setCleanResult(null);
    try {
      const { data } = await dataApi.upload(file);
      setMsg({ ok:true, t:`✓ Uploaded: ${data.rows?.toLocaleString()} rows × ${data.columns} columns` });
      await loadDatasets();
      await loadInfo();
      try { await api.post("/data/snapshot"); } catch {}
    } catch(e) {
      setMsg({ ok:false, t:e.response?.data?.detail || "Upload failed" });
    } finally { setLoad(false); }
  };

  const handleFiles = async (files) => {
    if (!files || files.length === 0) return;
    for (const file of Array.from(files)) {
      await upload(file);
    }
    await loadDatasets();
  };

  const handleFile = (e) => handleFiles(e.target.files);
  const handleDrop = (e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); };

  const cleanData = async () => {
    setCleaning(true);
    try {
      const { data } = await dataApi.clean();
      setCleanResult(data);
      await loadInfo();
    } catch(e) { setMsg({ ok:false, t:e.response?.data?.detail||"Clean failed" }); }
    finally { setCleaning(false); }
  };

  const indexRAG = async () => {
    if (ragFiles.length === 0) {
      setRagLoad(true); setRagMsg(null);
      try {
        const { data } = await api.post("/rag/index");
        const chunks = data.message?.match(/\d+/)?.[0] || 0;
        setRagChunks(chunks);
        setRagMsg({ ok:true, t:data.message });
        await loadRagStatus();
      } catch(e) { setRagMsg({ ok:false, t:e.response?.data?.detail||"Indexing failed" }); }
      finally { setRagLoad(false); }
      return;
    }
    setRagLoad(true); setRagMsg(null);
    try {
      let totalChunks = 0;
      for (const file of ragFiles) {
        const formData = new FormData();
        formData.append("file", file);
        if (file.name.endsWith(".csv")) {
          await dataApi.upload(file);
          const { data } = await api.post("/rag/index");
          totalChunks += parseInt(data.message?.match(/\d+/)?.[0] || 0);
        } else {
          const { data } = await api.post("/rag/index");
          totalChunks += parseInt(data.message?.match(/\d+/)?.[0] || 0);
        }
      }
      setRagChunks(totalChunks);
      setRagMsg({ ok:true, t:`Indexed ${ragFiles.length} file(s) — ${totalChunks} chunks` });
      setRagFiles([]);
      await loadRagStatus();
    } catch(e) { setRagMsg({ ok:false, t:e.response?.data?.detail||"Indexing failed" }); }
    finally { setRagLoad(false); }
  };

  const missing = info ? Object.values(info.missing_values||{}).reduce((a,b)=>a+b,0) : 0;

  const colInfoRows = info?.columns_info?.map(c=>({
    Column: c.name, Type: c.dtype,
    "Non-Null": (info.rows||0) - c.nulls,
    "Null Count": c.nulls,
    Unique: c.unique,
  })) || [];

  const statsRows = stats ? Object.entries(stats).slice(0,20).map(([col,s])=>({
    Column:col, Mean:s.mean?.toFixed?.(2)??"—", Std:s.std?.toFixed?.(2)??"—",
    Min:s.min?.toFixed?.(2)??"—", Max:s.max?.toFixed?.(2)??"—",
    "25%":s["25%"]?.toFixed?.(2)??"—", "50%":s["50%"]?.toFixed?.(2)??"—", "75%":s["75%"]?.toFixed?.(2)??"—",
  })) : [];

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.icon}>📤</div>
        <div>
          <div style={S.title}>Upload Dataset</div>
          <div style={S.sub}>CSV · Excel · JSON · up to 200MB · multi-file supported</div>
        </div>
      </div>

      {/* My Datasets Panel */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 16px",marginBottom:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:10}}>🗂️ My Datasets</div>
        {datasets.length === 0 ? (
          <div style={{fontSize:12,color:"#52525b"}}>No datasets uploaded yet.</div>
        ) : (
          <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
            {datasets.map(name => (
              <div
                key={name}
                onClick={() => !dsLoading && switchDataset(name)}
                style={{
                  display:"flex",alignItems:"center",gap:6,
                  padding:"6px 12px",borderRadius:10,cursor:"pointer",
                  border:`2px solid ${name === activeDataset ? "#10b981" : "rgba(255,255,255,.1)"}`,
                  background: name === activeDataset ? "rgba(16,185,129,.08)" : "rgba(24,24,27,.6)",
                  transition:"all .15s",
                }}
              >
                <span style={{fontSize:12,fontWeight:600,color: name === activeDataset ? "#34d399" : "#a1a1aa"}}>
                  {name === activeDataset ? "✓ " : ""}{name}
                </span>
                <button
                  onClick={(e) => deleteDataset(name, e)}
                  title="Delete dataset"
                  style={{background:"transparent",border:"none",cursor:"pointer",color:"#52525b",fontSize:12,padding:"0 2px",lineHeight:1}}
                >✕</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={e=>{e.preventDefault();setDragging(true);}}
        onDragLeave={()=>setDragging(false)}
        onClick={()=>fileRef.current.click()}
        style={{
          border:`2px dashed ${dragging?"#6366f1":"rgba(255,255,255,.12)"}`,
          borderRadius:16, padding:"40px 24px", textAlign:"center", cursor:"pointer",
          background:dragging?"rgba(99,102,241,.06)":"rgba(24,24,27,.4)",
          transition:"all .2s", marginBottom:16,
        }}>
        <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls,.json" multiple style={{display:"none"}} onChange={handleFile} />
        {loading ? (
          <div style={{display:"flex",alignItems:"center",justifyContent:"center",gap:10}}>
            <span className="spinner" style={{width:20,height:20}} />
            <span style={{color:"#52525b",fontSize:14}}>Uploading…</span>
          </div>
        ) : (
          <>
            <div style={{fontSize:32,marginBottom:8}}>📂</div>
            <div style={{fontSize:14,fontWeight:600,color:"#f4f4f5",marginBottom:4}}>
              {dragging ? "Drop to upload" : "Drag & drop or click to browse"}
            </div>
            <div style={{fontSize:12,color:"#52525b"}}>CSV, Excel (.xlsx/.xls), JSON — up to 200MB · select multiple files</div>
          </>
        )}
      </div>

      {msg && <div style={{...S.alert,background:msg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:msg.ok?"#34d399":"#f87171",marginBottom:16}}>{msg.t}</div>}

      {/* Dataset overview KPIs */}
      {info && (
        <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap"}}>
          {[["Rows",info.rows?.toLocaleString(),"#6366f1"],["Columns",info.columns,"#10b981"],["Missing",missing,"#f59e0b"],["Memory",`${info.memory_mb} MB`,"#818cf8"]].map(([l,v,c])=>(
            <div key={l} style={{flex:"1 1 100px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"12px 16px"}}>
              <div style={{fontSize:20,fontWeight:700,color:c}}>{v}</div>
              <div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div>
            </div>
          ))}
        </div>
      )}

      {/* Preview tabs */}
      {info && (
        <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 16px",marginBottom:16}}>
          <div style={{display:"flex",gap:4,marginBottom:12,borderBottom:"1px solid rgba(255,255,255,.06)"}}>
            {["📋 Table View","📊 Statistics","🔍 Column Info"].map((t,i)=>(
              <button key={t} onClick={()=>setPreviewTab(i)} style={{padding:"6px 12px",background:"transparent",border:"none",fontSize:12,fontWeight:500,cursor:"pointer",borderBottom:previewTab===i?"2px solid #6366f1":"2px solid transparent",color:previewTab===i?"#818cf8":"#52525b"}}>{t}</button>
            ))}
          </div>
          {previewTab===0 && preview?.data && <Table data={preview.data} />}
          {previewTab===1 && (statsRows.length>0 ? <Table data={statsRows} /> : <p style={{color:"#52525b",fontSize:13}}>No numeric columns.</p>)}
          {previewTab===2 && colInfoRows.length>0 && <Table data={colInfoRows} />}
        </div>
      )}

      {/* Data Cleaning */}
      {info && (
        <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 16px",marginBottom:16}}>
          <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginBottom:10}}>🧹 Data Cleaning</div>
          <div style={{display:"flex",gap:16,marginBottom:12,flexWrap:"wrap"}}>
            <label style={{display:"flex",alignItems:"center",gap:6,cursor:"pointer",fontSize:13,color:"#71717a"}}>
              <input type="checkbox" checked={removeDups} onChange={e=>setRemoveDups(e.target.checked)} style={{accentColor:"#6366f1"}} />
              Remove duplicates
            </label>
            <label style={{display:"flex",alignItems:"center",gap:6,cursor:"pointer",fontSize:13,color:"#71717a"}}>
              <input type="checkbox" checked={fillMissing} onChange={e=>setFillMissing(e.target.checked)} style={{accentColor:"#6366f1"}} />
              Fill missing values
            </label>
          </div>
          <button onClick={cleanData} disabled={cleaning} style={S.btn}>
            {cleaning?<><span className="spinner" style={{width:14,height:14}}/> Cleaning…</>:"✨ Clean Data"}
          </button>
          {cleanResult && (
            <div style={{marginTop:10,padding:"10px 14px",borderRadius:10,background:"rgba(16,185,129,.08)",border:"1px solid rgba(16,185,129,.2)",color:"#34d399",fontSize:13}}>
              ✅ {cleanResult.rows_removed||0} duplicates removed · {cleanResult.nulls_filled||0} nulls filled
            </div>
          )}
        </div>
      )}

      {/* Document RAG Upload */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 16px"}}>
        <button onClick={()=>setShowRag(s=>!s)} style={{background:"transparent",border:"none",cursor:"pointer",display:"flex",alignItems:"center",gap:8,fontSize:13,fontWeight:600,color:"#a1a1aa",width:"100%",textAlign:"left"}}>
          📚 Document Q&A Upload {showRag?"▲":"▼"}
        </button>
        {showRag && (
          <div style={{marginTop:12}}>
            <p style={{fontSize:12,color:"#52525b",marginBottom:10}}>Upload PDF, DOCX, TXT, MD, or CSV files to build a knowledge base for the RAG agent.</p>
            <input ref={ragRef} type="file" accept=".pdf,.docx,.txt,.md,.csv" multiple style={{display:"none"}}
              onChange={e=>setRagFiles(Array.from(e.target.files))} />
            <div style={{display:"flex",gap:10,marginBottom:10,flexWrap:"wrap"}}>
              <button onClick={()=>ragRef.current.click()} style={{...S.btn,background:"rgba(139,92,246,.15)",color:"#a78bfa",border:"1px solid rgba(139,92,246,.3)"}}>
                📎 Select Files
              </button>
              {ragFiles.length>0 && (
                <button onClick={indexRAG} disabled={ragLoading} style={S.btn}>
                  {ragLoading?<><span className="spinner" style={{width:14,height:14}}/> Indexing... This may take 60+ seconds</>:`🔍 Submit ${ragFiles.length} File${ragFiles.length>1?"s":""}`}
                </button>
              )}
              {ragFiles.length === 0 && info && (
                <button onClick={indexRAG} disabled={ragLoading} style={S.btn}>
                  {ragLoading?<><span className="spinner" style={{width:14,height:14}}/> Indexing... This may take 60+ seconds</>:"🔍 Submit"}
                </button>
              )}
            </div>
            {ragFiles.length>0 && (
              <div style={{display:"flex",flexWrap:"wrap",gap:6,marginBottom:10}}>
                {ragFiles.map((f,i)=>(
                  <span key={i} style={{padding:"3px 10px",borderRadius:20,background:"rgba(139,92,246,.1)",color:"#a78bfa",fontSize:11}}>{f.name}</span>
                ))}
              </div>
            )}
            {ragMsg && <div style={{...S.alert,background:ragMsg.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:ragMsg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:ragMsg.ok?"#34d399":"#f87171"}}>{ragMsg.t}</div>}
            <div style={{fontSize:12,color:ragChunks>0?"#10b981":"#52525b",marginTop:6,fontWeight:ragChunks>0?600:400}}>
              {ragChunks>0?`✓ Knowledge base: ${ragChunks} chunks indexed`:"No data indexed yet"}
            </div>
          </div>
        )}
      </div>

      {/* RAG Datasets Panel - Tasks 7.4, 7.5, 7.6, 7.7 */}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 16px",marginTop:16}}>
        <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
          <span style={{fontSize:14}}>🔍</span>
          <span style={{fontSize:13,fontWeight:600,color:"#a1a1aa"}}>Indexed RAG Datasets</span>
          <span style={{fontSize:11,color:"#52525b",marginLeft:"auto"}}>
            {ragDatasets.length} dataset{ragDatasets.length !== 1 ? "s" : ""} indexed
          </span>
        </div>

        {ragDatasets.length === 0 ? (
          <div style={{fontSize:12,color:"#52525b",padding:"12px 0"}}>
            No RAG datasets indexed yet. Select a dataset below to index it.
          </div>
        ) : (
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill, minmax(280px, 1fr))",gap:12,marginBottom:16}}>
            {ragDatasets.map(dataset => (
              <div key={dataset.name} style={{background:"rgba(24,24,27,.6)",border:"1px solid rgba(255,255,255,.08)",borderRadius:10,padding:12,transition:"all .15s"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",marginBottom:8}}>
                  <div style={{flex:1}}>
                    <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5",marginBottom:4}}>{dataset.name}</div>
                    <div style={{fontSize:11,color:"#71717a",marginBottom:2}}>{dataset.chunk_count} chunks</div>
                    <div style={{fontSize:11,color:"#71717a"}}>
                      Indexed: {new Date(dataset.indexed_at).toLocaleDateString()}
                    </div>
                  </div>
                  <button
                    onClick={(e) => deleteRagDataset(dataset.name, e)}
                    style={{background:"transparent",border:"none",cursor:"pointer",color:"#52525b",fontSize:14,padding:"0 4px",lineHeight:1,transition:"color .15s"}}
                    title="Remove from RAG index"
                  >✕</button>
                </div>
                <div style={{fontSize:10,color:"#10b981",fontWeight:600}}>✓ Indexed</div>
              </div>
            ))}
          </div>
        )}

        {/* Available datasets to index */}
        {datasets.length > 0 && (
          <>
            <div style={{fontSize:13,fontWeight:600,color:"#a1a1aa",marginTop:16,paddingTop:16,borderTop:"1px solid rgba(255,255,255,.06)",marginBottom:10}}>
              Available to Index
            </div>
            <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
              {datasets
                .filter(d => !ragDatasets.some(rd => rd.name === d))
                .map(d => (
                  <button
                    key={d}
                    onClick={() => indexDataset(d)}
                    disabled={ragDsLoading}
                    style={{
                      padding:"6px 12px",borderRadius:8,border:"1px solid rgba(99,102,241,.3)",
                      background:"rgba(99,102,241,.1)",color:"#818cf8",fontSize:12,fontWeight:500,
                      cursor:ragDsLoading?"not-allowed":"pointer",display:"inline-flex",alignItems:"center",gap:6,
                      transition:"all .15s",opacity:ragDsLoading?0.5:1
                    }}
                  >
                    {ragDsLoading ? (
                      <><span className="spinner" style={{width:12,height:12}}/> Indexing...</>
                    ) : (
                      <><span>🔍</span> Index {d}</>
                    )}
                  </button>
                ))}
              {datasets.every(d => ragDatasets.some(rd => rd.name === d)) && (
                <div style={{fontSize:12,color:"#52525b",padding:"12px 0"}}>
                  All uploaded datasets are indexed
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const S = {
  page:  { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  header:{ display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:  { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title: { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:   { fontSize:11, color:"#52525b" },
  btn:   { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  alert: { padding:"9px 13px", borderRadius:8, border:"1px solid", fontSize:13 },
};


