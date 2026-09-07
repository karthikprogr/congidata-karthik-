import { useEffect, useState, useMemo, Component } from "react";
import { api, dataApi } from "../api/client";
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

const TABS = ["🎯 Classification","📈 Regression","🔵 Clustering","🔍 Anomaly Detection"];
const CLF_MODELS = ["LogisticRegression","RandomForest","GradientBoosting","SVM","GaussianNB","KNN"];
const REG_MODELS = ["Linear","Ridge","Lasso","RandomForest","GradientBoosting","SVR"];
const CLU_ALGOS  = ["K-Means","DBSCAN","Agglomerative","Gaussian Mixture"];

export default function AutoML() {
  const [tab, setTab]       = useState(0);
  const [info, setInfo]     = useState(null);
  const [loading, setLoad]  = useState(true);
  const [error, setErr]     = useState(null);

  useEffect(()=>{
    dataApi.info().then(({data})=>setInfo(data)).catch(e=>setErr(e.response?.data?.detail||"Upload a dataset first.")).finally(()=>setLoad(false));
  },[]);

  if(loading) return <Spinner />;
  if(error)   return <Empty msg={error} />;

  const numCols = info?.numeric_columns||[];
  const catCols = info?.categorical_columns||[];
  const allCols = info?.columns_info?.map(c=>c.name)||[];

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={S.icon}>🧠</div>
          <div>
            <div style={S.title}>AutoML Studio</div>
            <div style={S.sub}>{info?.rows?.toLocaleString()} rows · {info?.columns} cols</div>
          </div>
        </div>
      </div>
      <div style={S.tabs}>
        {TABS.map((t,i)=>(
          <button key={t} onClick={()=>setTab(i)} style={{...S.tab,borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent",color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>
      {tab===0 && <ClassificationTab allCols={allCols} numCols={numCols} />}
      {tab===1 && <RegressionTab numCols={numCols} />}
      {tab===2 && <ClusteringTab numCols={numCols} />}
      {tab===3 && <AnomalyTab numCols={numCols} />}
    </div>
    </ErrorBoundary>
  );
}

function FeatureSelect({ cols, selected, onChange }) {
  const toggle = (c) => onChange(selected.includes(c)?selected.filter(x=>x!==c):[...selected,c]);
  return (
    <div style={{display:"flex",flexWrap:"wrap",gap:6,marginTop:4}}>
      {cols.map(c=>(
        <button key={c} onClick={()=>toggle(c)} style={{padding:"4px 10px",borderRadius:20,fontSize:11,cursor:"pointer",border:"1px solid",background:selected.includes(c)?"rgba(99,102,241,.15)":"transparent",borderColor:selected.includes(c)?"rgba(99,102,241,.4)":"rgba(255,255,255,.08)",color:selected.includes(c)?"#818cf8":"#52525b"}}>
          {c}
        </button>
      ))}
    </div>
  );
}

function TrainConfig({ children, onTrain, loading, label="🚀 Train" }) {
  return (
    <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"16px",marginBottom:16}}>
      {children}
      <button onClick={onTrain} disabled={loading} style={{...S.btn,marginTop:12}}>
        {loading?<><span className="spinner" style={{width:14,height:14}}/> Training…</>:label}
      </button>
    </div>
  );
}

function Viz3D({ title, fig }) {
  if(!fig) return null;
  return (
    <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 12px 8px",overflow:"hidden"}}>
      <div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:6,paddingLeft:4}}>{title}</div>
      <PlotlyChart figure={fig} style={{height:320}} />
    </div>
  );
}

function ClassificationTab({ allCols, numCols }) {
  const [target, setTarget]   = useState(allCols[0]||"");
  const [model, setModel]     = useState(CLF_MODELS[0]);
  const [features, setFeatures] = useState([]);
  const [testSplit, setTestSplit] = useState(20);
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [err, setErr]         = useState(null);

  const train = async () => {
    setLoad(true); setErr(null);
    try {
      const {data} = await api.post("/ml/classify",{target,model,features:features.length?features:undefined,test_size:testSplit/100});
      setResult(data);
    } catch(e){ setErr(e.response?.data?.detail||"Training failed"); }
    finally { setLoad(false); }
  };

  const featureCols = allCols.filter(c=>c!==target);

  const confFig = result?.confusion_matrix ? {
    data:[{type:"heatmap",z:result.confusion_matrix,colorscale:"Blues",showscale:true}],
    layout:{title:{text:"Confusion Matrix",font:{size:12}},xaxis:{title:"Predicted"},yaxis:{title:"Actual"}}
  } : null;

  const featFig = result?.feature_importance ? {
    data:[{type:"bar",x:Object.values(result.feature_importance),y:Object.keys(result.feature_importance),orientation:"h",marker:{color:"#6366f1"}}],
    layout:{title:{text:"Feature Importance",font:{size:12}},height:Math.max(200,Object.keys(result.feature_importance).length*25)}
  } : null;

  const rocFig = result?.roc_curve ? {
    data:[
      {type:"scatter",mode:"lines",x:result.roc_curve.fpr,y:result.roc_curve.tpr,line:{color:"#6366f1",width:2},name:`AUC=${result.roc_curve.auc?.toFixed(3)}`},
      {type:"scatter",mode:"lines",x:[0,1],y:[0,1],line:{color:"rgba(255,255,255,.2)",dash:"dash"},name:"Random"},
    ],
    layout:{title:{text:"ROC Curve",font:{size:12}},xaxis:{title:"FPR"},yaxis:{title:"TPR"}}
  } : null;

  // 3D figures from result data
  const scatter3d = result?.pca_3d ? {
    data:[{type:"scatter3d",mode:"markers",x:result.pca_3d.x,y:result.pca_3d.y,z:result.pca_3d.z,marker:{color:result.pca_3d.labels,colorscale:"Viridis",size:4,opacity:0.7}}],
    layout:{title:{text:"3D PCA Projection",font:{size:12}},scene:{xaxis:{title:"PC1"},yaxis:{title:"PC2"},zaxis:{title:"PC3"}}}
  } : null;

  const cm3d = result?.confusion_matrix ? {
    data:[{type:"surface",z:result.confusion_matrix,colorscale:"Blues"}],
    layout:{title:{text:"3D Confusion Matrix",font:{size:12}}}
  } : null;

  return (
    <div>
      <TrainConfig onTrain={train} loading={loading}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <div style={{flex:1,minWidth:160}}>
            <label style={S.label}>Target Column</label>
            <select value={target} onChange={e=>setTarget(e.target.value)} style={S.select}>
              {allCols.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{flex:1,minWidth:160}}>
            <label style={S.label}>Model</label>
            <select value={model} onChange={e=>setModel(e.target.value)} style={S.select}>
              {CLF_MODELS.map(m=><option key={m}>{m}</option>)}
            </select>
          </div>
          <div style={{minWidth:160}}>
            <label style={S.label}>Test Split: {testSplit}%</label>
            <input type="range" min={10} max={40} value={testSplit} onChange={e=>setTestSplit(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%",marginTop:6}} />
          </div>
        </div>
        <label style={S.label}>Features (click to select, empty = all)</label>
        <FeatureSelect cols={featureCols} selected={features} onChange={setFeatures} />
      </TrainConfig>

      {err && <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid rgba(239,68,68,.3)",background:"rgba(239,68,68,.08)",color:"#f87171",fontSize:13,marginBottom:12}}>{err}</div>}

      {result && (
        <>
          <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
            {[["Accuracy",`${((result.accuracy||0)*100).toFixed(1)}%`,"#22c55e"],["Train Samples",result.train_samples||0,"#6366f1"],["Test Samples",result.test_samples||0,"#818cf8"]].map(([l,v,c])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:c}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(400px,1fr))",gap:14,marginBottom:14}}>
            {confFig && <ChartCard title="Confusion Matrix"><PlotlyChart figure={confFig} /></ChartCard>}
            {featFig && <ChartCard title="Feature Importance"><PlotlyChart figure={featFig} /></ChartCard>}
            {rocFig  && <ChartCard title="ROC Curve"><PlotlyChart figure={rocFig} /></ChartCard>}
            {result.report && (
              <ChartCard title="Classification Report">
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                  <thead><tr>{["Class","Precision","Recall","F1","Support"].map(h=><th key={h} style={{padding:"6px 8px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:10,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
                  <tbody>{Object.entries(result.report).filter(([k])=>!["accuracy","macro avg","weighted avg"].includes(k)).map(([cls,m])=>(
                    <tr key={cls}><td style={S.td}>{cls}</td><td style={S.td}>{m.precision?.toFixed(2)}</td><td style={S.td}>{m.recall?.toFixed(2)}</td><td style={S.td}>{m["f1-score"]?.toFixed(2)}</td><td style={S.td}>{m.support}</td></tr>
                  ))}</tbody>
                </table>
              </ChartCard>
            )}
          </div>
          <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10}}>3D Visualizations</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(380px,1fr))",gap:14}}>
            {scatter3d && <Viz3D title="3D PCA Projection" fig={scatter3d} />}
            {cm3d      && <Viz3D title="3D Confusion Matrix Surface" fig={cm3d} />}
          </div>
        </>
      )}
    </div>
  );
}

function RegressionTab({ numCols }) {
  const [target, setTarget]   = useState(numCols[0]||"");
  const [model, setModel]     = useState(REG_MODELS[0]);
  const [features, setFeatures] = useState([]);
  const [testSplit, setTestSplit] = useState(20);
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [err, setErr]         = useState(null);

  const train = async () => {
    setLoad(true); setErr(null);
    try {
      const {data} = await api.post("/ml/regress",{target,model,features:features.length?features:undefined,test_size:testSplit/100});
      setResult(data);
    } catch(e){ setErr(e.response?.data?.detail||"Training failed"); }
    finally { setLoad(false); }
  };

  const featureCols = numCols.filter(c=>c!==target);

  const predFig = result?.predictions ? {
    data:[
      {type:"scatter",mode:"markers",x:result.predictions.actual,y:result.predictions.predicted,marker:{color:"#6366f1",size:5,opacity:0.6},name:"Predictions"},
      {type:"scatter",mode:"lines",x:[Math.min(...result.predictions.actual),Math.max(...result.predictions.actual)],y:[Math.min(...result.predictions.actual),Math.max(...result.predictions.actual)],line:{color:"#f59e0b",dash:"dash"},name:"Perfect"},
    ],
    layout:{title:{text:"Predicted vs Actual",font:{size:12}},xaxis:{title:"Actual"},yaxis:{title:"Predicted"}}
  } : null;

  const residFig = result?.predictions ? {
    data:[{type:"scatter",mode:"markers",x:result.predictions.actual,y:result.predictions.actual.map((a,i)=>a-(result.predictions.predicted[i]||0)),marker:{color:"#10b981",size:4,opacity:0.6}}],
    layout:{title:{text:"Residual Plot",font:{size:12}},xaxis:{title:"Actual"},yaxis:{title:"Residual"},shapes:[{type:"line",x0:Math.min(...result.predictions.actual),x1:Math.max(...result.predictions.actual),y0:0,y1:0,line:{color:"rgba(255,255,255,.3)",dash:"dash"}}]}
  } : null;

  const featFig = result?.feature_importance ? {
    data:[{type:"bar",x:Object.values(result.feature_importance),y:Object.keys(result.feature_importance),orientation:"h",marker:{color:"#8b5cf6"}}],
    layout:{title:{text:"Feature Importance",font:{size:12}},height:Math.max(200,Object.keys(result.feature_importance).length*25)}
  } : null;

  const scatter3d = result?.pca_3d ? {
    data:[{type:"scatter3d",mode:"markers",x:result.pca_3d.x,y:result.pca_3d.y,z:result.pca_3d.z||result.predictions?.predicted?.slice(0,result.pca_3d.x?.length)||[],marker:{color:result.pca_3d.z||[],colorscale:"Viridis",size:4,opacity:0.7}}],
    layout:{title:{text:"3D Features → Predicted",font:{size:12}},scene:{xaxis:{title:"PC1"},yaxis:{title:"PC2"},zaxis:{title:"Predicted"}}}
  } : null;

  return (
    <div>
      <TrainConfig onTrain={train} loading={loading}>
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <div style={{flex:1,minWidth:160}}>
            <label style={S.label}>Target (Numeric)</label>
            <select value={target} onChange={e=>setTarget(e.target.value)} style={S.select}>
              {numCols.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
          <div style={{flex:1,minWidth:160}}>
            <label style={S.label}>Model</label>
            <select value={model} onChange={e=>setModel(e.target.value)} style={S.select}>
              {REG_MODELS.map(m=><option key={m}>{m}</option>)}
            </select>
          </div>
          <div style={{minWidth:160}}>
            <label style={S.label}>Test Split: {testSplit}%</label>
            <input type="range" min={10} max={40} value={testSplit} onChange={e=>setTestSplit(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%",marginTop:6}} />
          </div>
        </div>
        <label style={S.label}>Features (click to select, empty = all)</label>
        <FeatureSelect cols={featureCols} selected={features} onChange={setFeatures} />
      </TrainConfig>

      {err && <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid rgba(239,68,68,.3)",background:"rgba(239,68,68,.08)",color:"#f87171",fontSize:13,marginBottom:12}}>{err}</div>}

      {result && (
        <>
          <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
            {[["R²",result.r2?.toFixed(4)||0,"#22c55e"],["RMSE",result.rmse?.toFixed(4)||0,"#6366f1"],["MAE",result.mae?.toFixed(4)||0,"#f59e0b"],["MSE",result.mse?.toFixed(4)||0,"#818cf8"]].map(([l,v,c])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:c}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(400px,1fr))",gap:14,marginBottom:14}}>
            {predFig && <ChartCard title="Predicted vs Actual"><PlotlyChart figure={predFig} /></ChartCard>}
            {residFig && <ChartCard title="Residual Plot"><PlotlyChart figure={residFig} /></ChartCard>}
            {featFig  && <ChartCard title="Feature Importance"><PlotlyChart figure={featFig} /></ChartCard>}
          </div>
          {scatter3d && (
            <>
              <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10}}>3D Visualizations</div>
              <Viz3D title="3D Features → Predicted" fig={scatter3d} />
            </>
          )}
        </>
      )}
    </div>
  );
}

function ClusteringTab({ numCols }) {
  const [algo, setAlgo]       = useState(CLU_ALGOS[0]);
  const [k, setK]             = useState(3);
  const [eps, setEps]         = useState(0.5);
  const [minSamples, setMinS] = useState(5);
  const [features, setFeatures] = useState([]);
  const [result, setResult]   = useState(null);
  const [loading, setLoad]    = useState(false);
  const [err, setErr]         = useState(null);

  const cluster = async () => {
    setLoad(true); setErr(null);
    try {
      const payload = { algorithm:algo, features:features.length?features:undefined };
      if(algo==="DBSCAN") { payload.eps=eps; payload.min_samples=minSamples; } else { payload.k=k; }
      const {data} = await api.post("/analytics/cluster",payload);
      setResult(data);
    } catch(e){ setErr(e.response?.data?.detail||"Clustering failed"); }
    finally { setLoad(false); }
  };

  const scatterFig = result?.scatter ? {
    data:[{type:"scatter",mode:"markers",x:result.scatter.x,y:result.scatter.y,marker:{color:result.scatter.labels,colorscale:"Viridis",size:6,opacity:0.7},text:result.scatter.labels?.map(l=>`Cluster ${l}`)}],
    layout:{title:{text:"Cluster Scatter",font:{size:12}},xaxis:{title:"PC1"},yaxis:{title:"PC2"}}
  } : null;

  const pieFig = result?.cluster_sizes ? {
    data:[{type:"pie",labels:Object.keys(result.cluster_sizes).map(k=>`Cluster ${k}`),values:Object.values(result.cluster_sizes),marker:{colorscale:"Viridis"}}],
    layout:{title:{text:"Cluster Distribution",font:{size:12}}}
  } : null;

  const heatFig = result?.correlation ? {
    data:[{type:"heatmap",z:result.correlation.values,x:result.correlation.cols,y:result.correlation.cols,colorscale:"RdBu",zmid:0}],
    layout:{title:{text:"Feature Correlation",font:{size:12}}}
  } : null;

  const scatter3d = result?.scatter3d ? {
    data:[{type:"scatter3d",mode:"markers",x:result.scatter3d.x,y:result.scatter3d.y,z:result.scatter3d.z,marker:{color:result.scatter3d.labels,colorscale:"Viridis",size:4,opacity:0.7}}],
    layout:{title:{text:"3D Cluster Space",font:{size:12}},scene:{xaxis:{title:"PC1"},yaxis:{title:"PC2"},zaxis:{title:"PC3"}}}
  } : null;

  return (
    <div>
      <TrainConfig onTrain={cluster} loading={loading} label="🔵 Cluster">
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <div style={{flex:1,minWidth:160}}>
            <label style={S.label}>Algorithm</label>
            <select value={algo} onChange={e=>setAlgo(e.target.value)} style={S.select}>
              {CLU_ALGOS.map(a=><option key={a}>{a}</option>)}
            </select>
          </div>
          {algo!=="DBSCAN" ? (
            <div style={{minWidth:160}}>
              <label style={S.label}>Clusters (k): {k}</label>
              <input type="range" min={2} max={10} value={k} onChange={e=>setK(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%",marginTop:6}} />
            </div>
          ) : (
            <>
              <div style={{minWidth:140}}>
                <label style={S.label}>Epsilon: {eps}</label>
                <input type="range" min={0.1} max={2.0} step={0.1} value={eps} onChange={e=>setEps(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%",marginTop:6}} />
              </div>
              <div style={{minWidth:140}}>
                <label style={S.label}>Min Samples: {minSamples}</label>
                <input type="range" min={2} max={20} value={minSamples} onChange={e=>setMinS(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%",marginTop:6}} />
              </div>
            </>
          )}
        </div>
        <label style={S.label}>Features (click to select, empty = all)</label>
        <FeatureSelect cols={numCols} selected={features} onChange={setFeatures} />
      </TrainConfig>

      {err && <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid rgba(239,68,68,.3)",background:"rgba(239,68,68,.08)",color:"#f87171",fontSize:13,marginBottom:12}}>{err}</div>}

      {result && (
        <>
          <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
            {[["Clusters",result.n_clusters||0,"#6366f1"],["Points",result.n_points||0,"#10b981"],["Silhouette",result.silhouette?.toFixed(3)||"N/A","#f59e0b"]].map(([l,v,c])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:c}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(400px,1fr))",gap:14,marginBottom:14}}>
            {scatterFig && <ChartCard title="2D Scatter"><PlotlyChart figure={scatterFig} /></ChartCard>}
            {pieFig     && <ChartCard title="Cluster Distribution"><PlotlyChart figure={pieFig} /></ChartCard>}
            {heatFig    && <ChartCard title="Feature Correlation"><PlotlyChart figure={heatFig} /></ChartCard>}
          </div>
          {result.summary && (
            <div style={{...S.card,marginBottom:14}}>
              <div style={S.cardTitle}>Cluster Summary</div>
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                <thead><tr>{["Cluster","Size","Centroid (mean)"].map(h=><th key={h} style={{padding:"7px 10px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
                <tbody>{result.summary.map((row,i)=><tr key={i}><td style={S.td}>{row.cluster}</td><td style={S.td}>{row.size}</td><td style={S.td}>{row.centroid}</td></tr>)}</tbody>
              </table>
            </div>
          )}
          {scatter3d && (
            <>
              <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10}}>3D Visualizations</div>
              <Viz3D title="3D Cluster Space" fig={scatter3d} />
            </>
          )}
        </>
      )}
    </div>
  );
}

function AnomalyTab({ numCols }) {
  const [contamination, setCont] = useState(0.05);
  const [features, setFeatures]  = useState([]);
  const [result, setResult]      = useState(null);
  const [loading, setLoad]       = useState(false);
  const [err, setErr]            = useState(null);

  const detect = async () => {
    setLoad(true); setErr(null);
    try {
      const {data} = await api.get(`/analytics/anomaly?contamination=${contamination}&features=${features.join(",")}`);
      setResult(data);
    } catch(e){ setErr(e.response?.data?.detail||"Detection failed"); }
    finally { setLoad(false); }
  };

  const scatterFig = result?.scatter ? {
    data:[
      {type:"scatter",mode:"markers",x:result.scatter.x?.filter((_,i)=>!result.scatter.is_anomaly?.[i]),y:result.scatter.y?.filter((_,i)=>!result.scatter.is_anomaly?.[i]),marker:{color:"#6366f1",size:5,opacity:0.6},name:"Normal"},
      {type:"scatter",mode:"markers",x:result.scatter.x?.filter((_,i)=>result.scatter.is_anomaly?.[i]),y:result.scatter.y?.filter((_,i)=>result.scatter.is_anomaly?.[i]),marker:{color:"#ef4444",size:8,symbol:"x"},name:"Anomaly"},
    ],
    layout:{title:{text:"Anomaly Scatter",font:{size:12}},xaxis:{title:"PC1"},yaxis:{title:"PC2"}}
  } : null;

  const scoreFig = result?.scores ? {
    data:[{type:"histogram",x:result.scores,marker:{color:"#8b5cf6",opacity:0.8},nbinsx:40}],
    layout:{title:{text:"Score Distribution",font:{size:12}}}
  } : null;

  return (
    <div>
      <TrainConfig onTrain={detect} loading={loading} label="🔍 Detect Anomalies">
        <div style={{display:"flex",gap:12,flexWrap:"wrap",marginBottom:12}}>
          <div style={{minWidth:200}}>
            <label style={S.label}>Contamination: {(contamination*100).toFixed(0)}%</label>
            <input type="range" min={0.01} max={0.30} step={0.01} value={contamination} onChange={e=>setCont(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%",marginTop:6}} />
          </div>
        </div>
        <label style={S.label}>Features (click to select, empty = all)</label>
        <FeatureSelect cols={numCols} selected={features} onChange={setFeatures} />
      </TrainConfig>

      {err && <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid rgba(239,68,68,.3)",background:"rgba(239,68,68,.08)",color:"#f87171",fontSize:13,marginBottom:12}}>{err}</div>}

      {result && (
        <>
          <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
            {[["Total Points",result.total||0,"#6366f1"],["Normal",result.normal||0,"#22c55e"],["Anomalies",result.anomalies||0,"#ef4444"]].map(([l,v,c])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:22,fontWeight:700,color:c}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div></div>
            ))}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(400px,1fr))",gap:14,marginBottom:14}}>
            {scatterFig && <ChartCard title="Anomaly Scatter"><PlotlyChart figure={scatterFig} /></ChartCard>}
            {scoreFig   && <ChartCard title="Score Distribution"><PlotlyChart figure={scoreFig} /></ChartCard>}
          </div>
          {result.anomalous_records?.length>0 && (
            <div style={S.card}>
              <div style={S.cardTitle}>Anomalous Records</div>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:11}}>
                  <thead><tr>{Object.keys(result.anomalous_records[0]).map(h=><th key={h} style={{padding:"6px 10px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:10,textTransform:"uppercase",whiteSpace:"nowrap"}}>{h}</th>)}</tr></thead>
                  <tbody>{result.anomalous_records.slice(0,20).map((row,i)=><tr key={i}>{Object.values(row).map((v,j)=><td key={j} style={{padding:"5px 10px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa",whiteSpace:"nowrap"}}>{String(v).slice(0,30)}</td>)}</tr>)}</tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Shared ────────────────────────────────────────────────────────────────────
function ChartCard({title,children}){
  return <div style={S.card}><div style={S.cardTitle}>{title}</div>{children}</div>;
}
function Spinner(){return <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",background:"#09090b",gap:12}}><span className="spinner" style={{width:28,height:28}}/><span style={{color:"#52525b"}}>Loading…</span></div>;}
function Empty({msg}){return <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",background:"#09090b"}}><div style={{textAlign:"center",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.07)",borderRadius:16,padding:"48px 56px"}}><div style={{fontSize:40,marginBottom:12}}>📂</div><p style={{color:"#a1a1aa",fontSize:15}}>{msg}</p></div></div>;}

const S = {
  page:      { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar:    { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 },
  icon:      { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:     { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:       { fontSize:11, color:"#52525b" },
  tabs:      { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:       { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  kpi:       { flex:"1 1 120px", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:"14px 18px" },
  btn:       { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  label:     { fontSize:12, color:"#71717a", display:"block", marginBottom:4 },
  select:    { padding:"8px 12px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:12, outline:"none", width:"100%" },
  card:      { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"14px 12px 8px", overflow:"hidden" },
  cardTitle: { fontSize:11, fontWeight:600, color:"#3f3f46", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:6, paddingLeft:4 },
  td:        { padding:"6px 10px", borderTop:"1px solid rgba(255,255,255,.04)", color:"#a1a1aa" },
};
