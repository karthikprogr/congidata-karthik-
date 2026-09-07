import { useState, useEffect, Component } from "react";
import { api } from "../api/client";
import Table from "../components/Table";
import PlotlyChart from "../components/PlotlyChart";

class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(e) { return { error: e }; }
  render() {
    if (this.state.error) return (
      <div style={{padding:40,color:"#f87171",background:"#09090b",minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",flexDirection:"column",gap:12}}>
        <div style={{fontSize:32}}>⚠️</div>
        <div style={{fontSize:16,fontWeight:600,color:"#f4f4f5"}}>Page Error</div>
        <div style={{fontSize:13,color:"#71717a",maxWidth:400,textAlign:"center"}}>{this.state.error.message}</div>
        <button onClick={()=>window.location.reload()} style={{padding:"8px 20px",borderRadius:8,border:"none",background:"#6366f1",color:"#fff",cursor:"pointer",fontSize:13}}>Reload</button>
      </div>
    );
    return this.props.children;
  }
}

const TABS = ["🧹 Smart Cleaning","🎯 Classification","📈 Regression","🔵 Clustering"];

export default function AIAnalyst() {
  const [tab, setTab] = useState(0);
  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.header}>
        <div style={S.icon}>🧠</div>
        <div>
          <div style={S.title}>AI Analyst</div>
          <div style={S.sub}>LLM-powered data cleaning · classification · regression · clustering</div>
        </div>
      </div>
      <div style={S.tabs}>
        {TABS.map((t,i)=>(
          <button key={t} onClick={()=>setTab(i)} style={{...S.tab,borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent",color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>
      {tab===0 && <CleaningTab />}
      {tab===1 && <ClassificationTab />}
      {tab===2 && <RegressionTab />}
      {tab===3 && <ClusteringTab />}
    </div>
    </ErrorBoundary>
  );
}

function CleaningTab() {
  const [preview, setPreview] = useState(null);
  const [info, setInfo]       = useState(null);
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [saving, setSaving]   = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  useEffect(()=>{
    api.get("/data/preview?n=10").then(({data})=>setPreview(data)).catch(()=>{});
    api.get("/data/info").then(({data})=>setInfo(data)).catch(()=>{});
  },[]);

  const run = async () => {
    setLoad(true);
    try {
      const { data } = await api.post("/ml/clean");
      setResult(data);
    } catch(e) {
      const { data } = await api.post("/data/clean");
      setResult({ message:"Cleaned", rows_removed:data.rows_removed||0, nulls_filled:data.nulls_filled||0 });
    } finally { setLoad(false); }
  };

  const downloadCleaned = async () => {
    const resp = await api.get("/reports/export/csv", { responseType:"blob" });
    const a = document.createElement("a"); a.href=URL.createObjectURL(resp.data); a.download="cleaned_data.csv"; a.click();
  };

  const useCleanedData = async () => {
    setSaving(true); setSaveMsg(null);
    try {
      await api.post("/data/upload-clean");
      setSaveMsg({ ok:true, t:"Cleaned dataset saved as active dataset." });
    } catch(e) {
      setSaveMsg({ ok:false, t:e.response?.data?.detail||"Failed to save." });
    } finally { setSaving(false); }
  };

  // Null counts from info
  const nullCols = info?.columns_info?.filter(c => c.nulls > 0) || [];

  return (
    <div style={S.section}>
      {/* Null counts table */}
      {nullCols.length > 0 && (
        <div style={{marginBottom:12}}>
          <h3 style={S.sectionTitle}>Columns with Null Values</h3>
          <div style={{overflowX:"auto",borderRadius:8,border:"1px solid rgba(255,255,255,.06)",marginTop:6}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr>{["Column","Type","Nulls","Null %"].map(h=><th key={h} style={{padding:"7px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:10,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
              <tbody>
                {nullCols.map((c,i)=>(
                  <tr key={i}>
                    <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{c.name}</td>
                    <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#71717a"}}>{c.dtype}</td>
                    <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#f59e0b"}}>{c.nulls}</td>
                    <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#f59e0b"}}>{c.null_pct?.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <h3 style={S.sectionTitle}>Original Data Preview</h3>
      {preview?.data && <Table data={preview.data} />}
      <button onClick={run} disabled={loading} style={{...S.btn,marginTop:12}}>
        {loading?<><span className="spinner" style={{width:14,height:14}}/> Running LLM Pipeline…</>:"🧹 Run LLM Cleaning Pipeline"}
      </button>
      {result && (
        <div style={{marginTop:16}}>
          <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
            {[["Duplicates Removed",result.rows_removed||0],["Nulls Filled",result.nulls_filled||0],["Columns Dropped",result.cols_dropped||0],["Encodings Applied",result.encodings||0]].map(([l,v])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:20,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>

          {/* LLM Null Strategies */}
          {result.null_strategies && result.null_strategies.length > 0 && (
            <div style={{marginBottom:12}}>
              <h3 style={{...S.sectionTitle,marginBottom:6}}>LLM Null Strategies</h3>
              <div style={{overflowX:"auto",borderRadius:8,border:"1px solid rgba(255,255,255,.06)"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                  <thead><tr>{["Column","Strategy","Reason"].map(h=><th key={h} style={{padding:"7px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:10,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
                  <tbody>
                    {result.null_strategies.map((s,i)=>(
                      <tr key={i}>
                        <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{s.column}</td>
                        <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#818cf8"}}>{s.strategy}</td>
                        <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#71717a"}}>{s.reason||"—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* LLM Encoding Decisions */}
          {result.encoding_decisions && result.encoding_decisions.length > 0 && (
            <div style={{marginBottom:12}}>
              <h3 style={{...S.sectionTitle,marginBottom:6}}>LLM Encoding Decisions</h3>
              <div style={{overflowX:"auto",borderRadius:8,border:"1px solid rgba(255,255,255,.06)"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                  <thead><tr>{["Column","Encoding","Reason"].map(h=><th key={h} style={{padding:"7px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:10,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
                  <tbody>
                    {result.encoding_decisions.map((d,i)=>(
                      <tr key={i}>
                        <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{d.column}</td>
                        <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#22c55e"}}>{d.encoding}</td>
                        <td style={{padding:"6px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#71717a"}}>{d.reason||"—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {saveMsg && <div style={{padding:"8px 12px",borderRadius:8,border:"1px solid",fontSize:12,marginBottom:10,background:saveMsg.ok?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)",borderColor:saveMsg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:saveMsg.ok?"#34d399":"#f87171"}}>{saveMsg.t}</div>}
          <div style={{display:"flex",gap:10,flexWrap:"wrap"}}>
            <button onClick={downloadCleaned} style={S.btn}>📥 Download Cleaned CSV</button>
            <button onClick={useCleanedData} disabled={saving} style={{...S.btn,background:"rgba(34,197,94,.15)",border:"1px solid rgba(34,197,94,.3)",color:"#34d399"}}>
              {saving?"Saving…":"✅ Use Cleaned Data"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ClassificationTab() {
  const [info, setInfo]     = useState(null);
  const [target, setTarget] = useState("");
  const [testSize, setTest] = useState(0.2);
  const [result, setResult] = useState(null);
  const [shap, setShap]     = useState(null);
  const [loading, setLoad]  = useState(false);

  useEffect(()=>{
    api.get("/data/info").then(({data})=>{ setInfo(data); setTarget(data.columns_info?.[0]?.name||""); }).catch(()=>{});
  },[]);

  const run = async () => {
    setLoad(true); setResult(null); setShap(null);
    try {
      const { data } = await api.post("/ml/classify", { target, test_size:testSize });
      setResult(data);
    } catch(e) { setResult({ error: e.response?.data?.detail||"Classification failed" }); }
    finally { setLoad(false); }
  };

  const runShap = async () => {
    setLoad(true);
    try {
      const { data } = await api.post("/ml/explain", { target, model_type:"classification" });
      setShap(data);
    } catch(e) { setShap({ error: e.response?.data?.detail||"SHAP failed" }); }
    finally { setLoad(false); }
  };

  const cols = info?.columns_info?.map(c=>c.name)||[];

  return (
    <div style={S.section}>
      <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:16}}>
        <div>
          <label style={S.label}>Target Variable</label>
          <select value={target} onChange={e=>setTarget(e.target.value)} style={S.select}>
            {cols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={S.label}>Test Size: {Math.round(testSize*100)}%</label>
          <input type="range" min={0.1} max={0.4} step={0.05} value={testSize} onChange={e=>setTest(parseFloat(e.target.value))}
            style={{display:"block",marginTop:8,accentColor:"#6366f1",width:160}} />
        </div>
      </div>
      <button onClick={run} disabled={loading||!target} style={S.btn}>
        {loading?<><span className="spinner" style={{width:14,height:14}}/> Training…</>:"🎯 Run LLM Classification"}
      </button>
      {result?.error && <div style={S.err}>{result.error}</div>}
      {result && !result.error && (
        <div style={{marginTop:16}}>
          <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:16}}>
            {[["Model",result.model],["Accuracy",`${(result.accuracy*100).toFixed(1)}%`],["F1",result.f1?.toFixed(3)],["AUC",result.auc?.toFixed(3)]].map(([l,v])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:16,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          {result.confusion_matrix && (() => {
            const cm = Array.isArray(result.confusion_matrix) ? result.confusion_matrix : null;
            if (!cm) return null;
            const fig = {
              data:[{type:"heatmap",z:cm,colorscale:"Blues",showscale:true}],
              layout:{height:280,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{l:40,r:10,t:40,b:40},title:{text:"Confusion Matrix",font:{size:12,color:"#a1a1aa"}},xaxis:{title:{text:"Predicted",font:{size:10}}},yaxis:{title:{text:"Actual",font:{size:10}}}}
            };
            return <PlotlyChart figure={fig} />;
          })()}
          {result.feature_importance && (() => {
            const fi = result.feature_importance;
            if (!fi || typeof fi !== "object") return null;
            const fig = {
              data:[{type:"bar",x:Object.values(fi),y:Object.keys(fi),orientation:"h",marker:{color:"#6366f1"}}],
              layout:{height:Math.max(200,Object.keys(fi).length*25),template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{l:120,r:10,t:30,b:30},title:{text:"Feature Importance",font:{size:12,color:"#a1a1aa"}}}
            };
            return <PlotlyChart figure={fig} />;
          })()}
          {result.roc_curve && (() => {
            const roc = result.roc_curve;
            if (!roc?.fpr) return null;
            const fig = {
              data:[
                {type:"scatter",mode:"lines",x:roc.fpr,y:roc.tpr,name:`AUC=${roc.auc?.toFixed(3)}`,line:{color:"#6366f1",width:2}},
                {type:"scatter",mode:"lines",x:[0,1],y:[0,1],name:"Random",line:{color:"rgba(255,255,255,.2)",dash:"dash",width:1}},
              ],
              layout:{height:260,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{l:40,r:10,t:40,b:40},title:{text:"ROC Curve",font:{size:12,color:"#a1a1aa"}},xaxis:{title:{text:"FPR",font:{size:10}}},yaxis:{title:{text:"TPR",font:{size:10}}}}
            };
            return <PlotlyChart figure={fig} />;
          })()}
          <button onClick={runShap} disabled={loading} style={{...S.btn,marginTop:12,background:"rgba(99,102,241,.15)",color:"#818cf8",border:"1px solid rgba(99,102,241,.3)"}}>
            🔍 SHAP Explanation
          </button>
          {shap?.error && <div style={S.err}>{shap.error}</div>}
          {shap && !shap.error && shap.chart && <PlotlyChart figure={shap.chart} />}
        </div>
      )}
    </div>
  );
}

function RegressionTab() {
  const [info, setInfo]     = useState(null);
  const [target, setTarget] = useState("");
  const [testSize, setTest] = useState(0.2);
  const [result, setResult] = useState(null);
  const [shap, setShap]     = useState(null);
  const [loading, setLoad]  = useState(false);

  useEffect(()=>{
    api.get("/data/info").then(({data})=>{ setInfo(data); const num=data.columns_info?.find(c=>c.dtype!=="object"); setTarget(num?.name||""); }).catch(()=>{});
  },[]);

  const run = async () => {
    setLoad(true); setResult(null); setShap(null);
    try {
      const { data } = await api.post("/ml/regress", { target, test_size:testSize });
      setResult(data);
    } catch(e) { setResult({ error: e.response?.data?.detail||"Regression failed" }); }
    finally { setLoad(false); }
  };

  const runShap = async () => {
    setLoad(true);
    try {
      const { data } = await api.post("/ml/explain", { target, model_type:"regression" });
      setShap(data);
    } catch(e) { setShap({ error: e.response?.data?.detail||"SHAP failed" }); }
    finally { setLoad(false); }
  };

  const numCols = info?.columns_info?.filter(c=>c.dtype!=="object").map(c=>c.name)||[];

  return (
    <div style={S.section}>
      <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:16}}>
        <div>
          <label style={S.label}>Target (numeric)</label>
          <select value={target} onChange={e=>setTarget(e.target.value)} style={S.select}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={S.label}>Test Size: {Math.round(testSize*100)}%</label>
          <input type="range" min={0.1} max={0.4} step={0.05} value={testSize} onChange={e=>setTest(parseFloat(e.target.value))}
            style={{display:"block",marginTop:8,accentColor:"#6366f1",width:160}} />
        </div>
      </div>
      <button onClick={run} disabled={loading||!target} style={S.btn}>
        {loading?<><span className="spinner" style={{width:14,height:14}}/> Training…</>:"📈 Run LLM Regression"}
      </button>
      {result?.error && <div style={S.err}>{result.error}</div>}
      {result && !result.error && (
        <div style={{marginTop:16}}>
          <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:16}}>
            {[["Model",result.model],["R²",result.r2?.toFixed(3)],["RMSE",result.rmse?.toFixed(3)],["MAE",result.mae?.toFixed(3)]].map(([l,v])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:16,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          {/* Predicted vs Actual — build from predictions data */}
          {result.predictions && (() => {
            const { actual, predicted } = result.predictions;
            const mn = Math.min(...actual, ...predicted), mx = Math.max(...actual, ...predicted);
            const fig = {
              data:[
                {type:"scatter",mode:"markers",x:actual,y:predicted,name:"Predictions",marker:{color:"#6366f1",size:5,opacity:0.6}},
                {type:"scatter",mode:"lines",x:[mn,mx],y:[mn,mx],name:"Perfect Fit",line:{color:"#f59e0b",dash:"dash",width:1.5}},
              ],
              layout:{height:280,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{l:40,r:10,t:30,b:40},title:{text:"Predicted vs Actual",font:{size:12,color:"#a1a1aa"}},xaxis:{title:{text:"Actual",font:{size:10}}},yaxis:{title:{text:"Predicted",font:{size:10}}}}
            };
            return <PlotlyChart figure={fig} />;
          })()}
          {/* Residual Plot */}
          {result.predictions && (() => {
            const { actual, predicted } = result.predictions;
            const residuals = actual.map((a,i)=>a-predicted[i]);
            const fig = {
              data:[{type:"scatter",mode:"markers",x:predicted,y:residuals,name:"Residuals",marker:{color:"#10b981",size:5,opacity:0.6}}],
              layout:{height:240,template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{l:40,r:10,t:30,b:40},title:{text:"Residual Plot",font:{size:12,color:"#a1a1aa"}},xaxis:{title:{text:"Predicted",font:{size:10}}},yaxis:{title:{text:"Residual",font:{size:10}}},shapes:[{type:"line",x0:Math.min(...predicted),x1:Math.max(...predicted),y0:0,y1:0,line:{color:"rgba(255,255,255,.2)",dash:"dash"}}]}
            };
            return <PlotlyChart figure={fig} />;
          })()}
          {/* QQ Plot */}
          {result.residuals && (() => {
            const sorted = [...result.residuals].sort((a,b)=>a-b);
            const n = sorted.length;
            const theoretical = sorted.map((_,i) => {
              const p = (i + 0.5) / n;
              const sign = p < 0.5 ? -1 : 1;
              return sign * Math.sqrt(-Math.log(Math.min(p,1-p)) * 2);
            });
            const qqFig = {
              data: [
                { type:"scatter", mode:"markers", x:theoretical, y:sorted, name:"Residuals", marker:{color:"#6366f1",size:5,opacity:0.7} },
                { type:"scatter", mode:"lines", x:[theoretical[0],theoretical[n-1]], y:[theoretical[0],theoretical[n-1]], name:"Normal line", line:{color:"#f59e0b",dash:"dash",width:1.5} }
              ],
              layout: { height:240, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", margin:{l:40,r:10,t:30,b:40}, title:{text:"QQ Plot (Residuals)",font:{size:12,color:"#a1a1aa"}}, xaxis:{title:{text:"Theoretical Quantiles",font:{size:10}}}, yaxis:{title:{text:"Sample Quantiles",font:{size:10}}} }
            };
            return <PlotlyChart figure={qqFig} />;
          })()}
          {result.feature_importance && (() => {
            const fi = result.feature_importance;
            const fig = {
              data:[{type:"bar",x:Object.values(fi),y:Object.keys(fi),orientation:"h",marker:{color:"#8b5cf6"}}],
              layout:{height:Math.max(200,Object.keys(fi).length*25),template:"plotly_dark",paper_bgcolor:"transparent",plot_bgcolor:"transparent",margin:{l:120,r:10,t:30,b:30},title:{text:"Feature Importance",font:{size:12,color:"#a1a1aa"}}}
            };
            return <PlotlyChart figure={fig} />;
          })()}
          <button onClick={runShap} disabled={loading} style={{...S.btn,marginTop:12,background:"rgba(99,102,241,.15)",color:"#818cf8",border:"1px solid rgba(99,102,241,.3)"}}>
            🔍 SHAP Explanation
          </button>
          {shap?.error && <div style={S.err}>{shap.error}</div>}
          {shap && !shap.error && shap.chart && <PlotlyChart figure={shap.chart} />}
        </div>
      )}
    </div>
  );
}

function ClusteringTab() {
  const [k, setK]           = useState(3);
  const [autoK, setAutoK]   = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoad]  = useState(false);

  const run = async () => {
    setLoad(true); setResult(null);
    try {
      const { data } = await api.post("/analytics/cluster", { k: autoK ? 0 : k });
      setResult(data);
    } catch(e) { setResult({ error: e.response?.data?.detail||"Clustering failed" }); }
    finally { setLoad(false); }
  };

  const downloadClustered = async () => {
    const resp = await api.get("/reports/export/csv", { responseType:"blob" });
    const a = document.createElement("a"); a.href=URL.createObjectURL(resp.data); a.download="clustered_data.csv"; a.click();
  };

  // Build Plotly figures from result
  const buildPieFig = (result) => {
    if (!result?.points) return null;
    const counts = {};
    result.points.forEach(p => { counts[p.cluster] = (counts[p.cluster]||0) + 1; });
    const labels = Object.keys(counts).map(c => `Cluster ${c}`);
    const values = Object.values(counts);
    return {
      data: [{ type:"pie", labels, values, hole:0.35, marker:{ colors:["#6366f1","#10b981","#f59e0b","#ef4444","#0ea5e9","#8b5cf6","#ec4899","#14b8a6"] } }],
      layout: { height:260, showlegend:true, template:"plotly_dark", paper_bgcolor:"transparent", margin:{l:0,r:0,t:20,b:0}, title:{text:"Cluster Distribution",font:{size:12,color:"#a1a1aa"}} }
    };
  };

  const buildScatterFig = (result) => {
    if (!result?.points) return null;
    const clusters = [...new Set(result.points.map(p => p.cluster))];
    const colors = ["#6366f1","#10b981","#f59e0b","#ef4444","#0ea5e9","#8b5cf6","#ec4899","#14b8a6"];
    const traces = clusters.map(c => ({
      type: "scatter",
      mode: "markers",
      name: `Cluster ${c}`,
      x: result.points.filter(p=>p.cluster===c).map(p=>p.x),
      y: result.points.filter(p=>p.cluster===c).map(p=>p.y),
      marker: { color: colors[c%8], size:6, opacity:0.7 }
    }));
    return {
      data: traces,
      layout: { height:280, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", margin:{l:30,r:10,t:20,b:30}, title:{text:"Cluster Scatter",font:{size:12,color:"#a1a1aa"}} }
    };
  };

  const build3DFig = (result) => {
    if (!result?.points_3d) return null;
    const clusters = [...new Set(result.points_3d.map(p => p.cluster))];
    const colors = ["#6366f1","#10b981","#f59e0b","#ef4444","#0ea5e9","#8b5cf6","#ec4899","#14b8a6"];
    const traces = clusters.map(c => ({
      type: "scatter3d",
      mode: "markers",
      name: `Cluster ${c}`,
      x: result.points_3d.filter(p=>p.cluster===c).map(p=>p.x),
      y: result.points_3d.filter(p=>p.cluster===c).map(p=>p.y),
      z: result.points_3d.filter(p=>p.cluster===c).map(p=>p.z),
      marker: { color: colors[c%8], size:4, opacity:0.7 }
    }));
    return {
      data: traces,
      layout: { height:320, template:"plotly_dark", paper_bgcolor:"transparent", margin:{l:0,r:0,t:20,b:0}, title:{text:"3D Cluster View",font:{size:12,color:"#a1a1aa"}} }
    };
  };

  return (
    <div style={S.section}>
      <div style={{display:"flex",gap:16,alignItems:"center",marginBottom:16,flexWrap:"wrap"}}>
        <label style={{display:"flex",alignItems:"center",gap:8,cursor:"pointer",fontSize:13,color:"#71717a"}}>
          <input type="checkbox" checked={autoK} onChange={e=>setAutoK(e.target.checked)} style={{accentColor:"#6366f1"}} />
          Let LLM decide k
        </label>
        {!autoK && (
          <div>
            <label style={S.label}>Clusters (k): {k}</label>
            <input type="range" min={2} max={10} value={k} onChange={e=>setK(parseInt(e.target.value))}
              style={{display:"block",marginTop:6,accentColor:"#6366f1",width:160}} />
          </div>
        )}
      </div>
      <button onClick={run} disabled={loading} style={S.btn}>
        {loading?<><span className="spinner" style={{width:14,height:14}}/> Clustering…</>:"🔵 Run LLM Clustering"}
      </button>
      {result?.error && <div style={S.err}>{result.error}</div>}
      {result && !result.error && (
        <div style={{marginTop:16}}>
          <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:16}}>
            {[
              ["k", result.k],
              ["Silhouette", result.silhouette?.toFixed(3)||"—"],
              ["Points", result.points?.length||0],
              ["Davies-Bouldin", result.davies_bouldin?.toFixed(3)||"—"],
              ["Calinski-Harabasz", result.calinski_harabasz?.toFixed(1)||"—"],
            ].map(([l,v])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:16,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          {/* Cluster Distribution Pie */}
          {buildPieFig(result) && (
            <div style={{...S.chartCard,marginBottom:12}}>
              <PlotlyChart figure={buildPieFig(result)} />
            </div>
          )}
          {/* 2D Scatter */}
          {buildScatterFig(result) && (
            <div style={{...S.chartCard,marginBottom:12}}>
              <PlotlyChart figure={buildScatterFig(result)} />
            </div>
          )}
          {/* 3D Scatter */}
          {build3DFig(result) && (
            <div style={{...S.chartCard,marginBottom:12}}>
              <PlotlyChart figure={build3DFig(result)} />
            </div>
          )}
          <button onClick={downloadClustered} style={{...S.btn,marginTop:4}}>📥 Download Clustered CSV</button>
        </div>
      )}
    </div>
  );
}

const S = {
  page:        { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  header:      { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:        { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:       { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:         { fontSize:11, color:"#52525b" },
  tabs:        { display:"flex", gap:4, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:         { padding:"8px 14px", background:"transparent", border:"none", fontSize:13, fontWeight:500, cursor:"pointer" },
  section:     { display:"flex", flexDirection:"column", gap:12 },
  sectionTitle:{ fontSize:13, fontWeight:600, color:"#a1a1aa", margin:0 },
  kpi:         { flex:"1 1 100px", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:"12px 16px" },
  chartCard:   { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:12 },
  label:       { fontSize:11, color:"#71717a", display:"block", marginBottom:4 },
  select:      { padding:"8px 12px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:13, outline:"none" },
  btn:         { padding:"10px 18px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8, alignSelf:"flex-start" },
  err:         { padding:"9px 13px", borderRadius:8, background:"rgba(239,68,68,.1)", border:"1px solid rgba(239,68,68,.3)", color:"#f87171", fontSize:13, marginTop:8 },
};
