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

const TABS = ["📊 Multi-Chart Dashboard","🔍 Deep Dive Analysis","📈 Trend Analysis","🎯 Comparison View","💡 Auto Insights"];

export default function AdvancedAnalytics() {
  const [tab, setTab]       = useState(0);
  const [info, setInfo]     = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoad]  = useState(true);
  const [error, setErr]     = useState(null);

  useEffect(()=>{
    Promise.all([dataApi.info(), dataApi.preview(500)])
      .then(([i,p])=>{ setInfo(i.data); setPreview(p.data); })
      .catch(e=>setErr(e.response?.data?.detail||"Upload a dataset first."))
      .finally(()=>setLoad(false));
  },[]);

  if(loading) return <Spinner />;
  if(error)   return <Empty msg={error} />;

  const numCols = info?.numeric_columns||[];
  const catCols = info?.categorical_columns||[];
  const allCols = info?.columns_info?.map(c=>c.name)||[];
  const rows    = preview?.data||[];

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={S.icon}>📊</div>
          <div>
            <div style={S.title}>Advanced Analytics</div>
            <div style={S.sub}>{info?.rows?.toLocaleString()} rows · {info?.columns} cols</div>
          </div>
        </div>
      </div>
      <div style={S.tabs}>
        {TABS.map((t,i)=>(
          <button key={t} onClick={()=>setTab(i)} style={{...S.tab,borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent",color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>
      {tab===0 && <MultiChartTab numCols={numCols} catCols={catCols} rows={rows} />}
      {tab===1 && <DeepDiveTab numCols={numCols} catCols={catCols} allCols={allCols} rows={rows} />}
      {tab===2 && <TrendTab allCols={allCols} numCols={numCols} rows={rows} />}
      {tab===3 && <ComparisonTab catCols={catCols} numCols={numCols} rows={rows} />}
      {tab===4 && <AutoInsightsTab info={info} numCols={numCols} catCols={catCols} rows={rows} />}
    </div>
    </ErrorBoundary>
  );
}

function getColValues(rows, col) {
  return rows.map(r=>r[col]).filter(v=>v!=null);
}
function numStats(vals) {
  const n = vals.filter(v=>typeof v==="number"&&!isNaN(v));
  if(!n.length) return null;
  const sorted = [...n].sort((a,b)=>a-b);
  const mean = n.reduce((a,b)=>a+b,0)/n.length;
  const std  = Math.sqrt(n.reduce((a,b)=>a+(b-mean)**2,0)/n.length);
  return { mean, median:sorted[Math.floor(n.length/2)], std, min:sorted[0], max:sorted[sorted.length-1], range:sorted[sorted.length-1]-sorted[0], n };
}

function MultiChartTab({ numCols, catCols, rows }) {
  const [xCol, setXCol] = useState(numCols[0]||"");
  const [yCol, setYCol] = useState(numCols[1]||numCols[0]||"");
  const [catCol, setCatCol] = useState(catCols[0]||"");

  const histFig = useMemo(()=>{
    if(!xCol) return null;
    const vals = getColValues(rows,xCol).filter(v=>typeof v==="number");
    return { data:[{type:"histogram",x:vals,marker:{color:"#6366f1",opacity:0.8},nbinsx:30}], layout:{title:{text:`Distribution: ${xCol}`,font:{size:12}},xaxis:{title:xCol},yaxis:{title:"Count"}} };
  },[xCol,rows]);

  const scatterFig = useMemo(()=>{
    if(!xCol||!yCol) return null;
    const xs = getColValues(rows,xCol).filter(v=>typeof v==="number");
    const ys = getColValues(rows,yCol).filter(v=>typeof v==="number");
    const n  = Math.min(xs.length,ys.length);
    const xd = xs.slice(0,n), yd = ys.slice(0,n);
    const mx = xd.reduce((a,b)=>a+b,0)/n, my = yd.reduce((a,b)=>a+b,0)/n;
    const slope = xd.reduce((a,v,i)=>a+(v-mx)*(yd[i]-my),0)/xd.reduce((a,v)=>a+(v-mx)**2,0)||0;
    const trendY = xd.map(v=>my+slope*(v-mx));
    return { data:[
      {type:"scatter",mode:"markers",x:xd,y:yd,marker:{color:"#6366f1",opacity:0.6,size:5},name:"Data"},
      {type:"scatter",mode:"lines",x:xd,y:trendY,line:{color:"#f59e0b",width:2},name:"Trend"},
    ], layout:{title:{text:`${xCol} vs ${yCol}`,font:{size:12}},xaxis:{title:xCol},yaxis:{title:yCol}} };
  },[xCol,yCol,rows]);

  const boxFig = useMemo(()=>{
    const cols = numCols.slice(0,5);
    if(!cols.length) return null;
    return { data: cols.map(c=>({type:"box",y:getColValues(rows,c).filter(v=>typeof v==="number"),name:c,marker:{color:"#8b5cf6"}})),
      layout:{title:{text:"Box Plot Comparison",font:{size:12}}} };
  },[numCols,rows]);

  const barFig = useMemo(()=>{
    if(!catCol) return null;
    const counts = {};
    getColValues(rows,catCol).forEach(v=>{ counts[v]=(counts[v]||0)+1; });
    const sorted = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,10);
    return { data:[{type:"bar",x:sorted.map(([k])=>k),y:sorted.map(([,v])=>v),marker:{color:"#10b981"}}],
      layout:{title:{text:`Top 10: ${catCol}`,font:{size:12}},xaxis:{title:catCol},yaxis:{title:"Count"}} };
  },[catCol,rows]);

  const Sel = ({label,val,set,opts})=>(
    <div>
      <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>{label}</label>
      <select value={val} onChange={e=>set(e.target.value)} style={S.select}>
        {opts.map(o=><option key={o}>{o}</option>)}
      </select>
    </div>
  );

  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap"}}>
        <Sel label="X / Distribution Column" val={xCol} set={setXCol} opts={numCols} />
        <Sel label="Y Column (Scatter)" val={yCol} set={setYCol} opts={numCols} />
        <Sel label="Categorical Column" val={catCol} set={setCatCol} opts={catCols} />
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(460px,1fr))",gap:16}}>
        {[["Distribution Histogram",histFig],["Scatter + Trendline",scatterFig],["Box Plot",boxFig],["Top-10 Bar Chart",barFig]].map(([title,fig])=>(
          <div key={title} style={S.card}>
            <div style={S.cardTitle}>{title}</div>
            {fig ? <PlotlyChart figure={fig} /> : <div style={{height:200,display:"flex",alignItems:"center",justifyContent:"center",color:"#3f3f46",fontSize:12}}>Select columns above</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function DeepDiveTab({ numCols, catCols, allCols, rows }) {
  const [col, setCol] = useState(allCols[0]||"");
  const isNum = numCols.includes(col);

  const vals = useMemo(()=>getColValues(rows,col),[col,rows]);
  const stats = useMemo(()=>isNum?numStats(vals):null,[isNum,vals]);

  const histFig = useMemo(()=>{
    if(!isNum||!stats) return null;
    const n = vals.filter(v=>typeof v==="number");
    return { data:[{type:"histogram",x:n,marker:{color:"#6366f1",opacity:0.8},nbinsx:30}], layout:{title:{text:"Histogram",font:{size:12}}} };
  },[isNum,vals,stats]);

  const violinFig = useMemo(()=>{
    if(!isNum||!stats) return null;
    const n = vals.filter(v=>typeof v==="number");
    return { data:[{type:"violin",y:n,box:{visible:true},meanline:{visible:true},fillcolor:"rgba(99,102,241,.3)",line:{color:"#6366f1"},name:col}], layout:{title:{text:"Violin Plot",font:{size:12}}} };
  },[isNum,vals,stats,col]);

  const pctTable = useMemo(()=>{
    if(!isNum||!stats) return [];
    const n = [...vals.filter(v=>typeof v==="number")].sort((a,b)=>a-b);
    return [10,25,50,75,90,95,99].map(p=>{ const i=Math.floor(p/100*n.length); return [p,n[i]??n[n.length-1]]; });
  },[isNum,vals,stats]);

  const catCounts = useMemo(()=>{
    if(isNum) return null;
    const c={};
    vals.forEach(v=>{ c[v]=(c[v]||0)+1; });
    return Object.entries(c).sort((a,b)=>b[1]-a[1]);
  },[isNum,vals]);

  const catBarFig = useMemo(()=>{
    if(!catCounts) return null;
    const top = catCounts.slice(0,20);
    return { data:[{type:"bar",x:top.map(([k])=>k),y:top.map(([,v])=>v),marker:{color:"#10b981"}}], layout:{title:{text:`Value Counts: ${col}`,font:{size:12}}} };
  },[catCounts,col]);

  return (
    <div>
      <div style={{marginBottom:16}}>
        <label style={{fontSize:12,color:"#71717a",display:"block",marginBottom:4}}>Select Column</label>
        <select value={col} onChange={e=>setCol(e.target.value)} style={S.select}>
          {allCols.map(c=><option key={c}>{c}</option>)}
        </select>
      </div>

      {isNum && stats && (
        <>
          <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
            {[["Mean",stats.mean.toFixed(3)],["Median",stats.median.toFixed(3)],["Std Dev",stats.std.toFixed(3)],["Min",stats.min],["Max",stats.max],["Range",stats.range.toFixed(3)]].map(([l,v])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:18,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:2}}>{l}</div></div>
            ))}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:16}}>
            <div style={S.card}><div style={S.cardTitle}>Histogram</div><PlotlyChart figure={histFig} /></div>
            <div style={S.card}><div style={S.cardTitle}>Violin Plot</div><PlotlyChart figure={violinFig} /></div>
          </div>
          <div style={S.card}>
            <div style={S.cardTitle}>Percentile Table</div>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr>{["Percentile","Value"].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
              <tbody>{pctTable.map(([p,v])=><tr key={p}><td style={{padding:"7px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{p}th</td><td style={{padding:"7px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#6366f1",fontWeight:600}}>{v}</td></tr>)}</tbody>
            </table>
          </div>
        </>
      )}

      {!isNum && catCounts && (
        <>
          <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
            {[["Unique Values",catCounts.length],["Most Common",catCounts[0]?.[0]||"—"],["Least Common",catCounts[catCounts.length-1]?.[0]||"—"]].map(([l,v])=>(
              <div key={l} style={S.kpi}><div style={{fontSize:18,fontWeight:700,color:"#6366f1",wordBreak:"break-all"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:2}}>{l}</div></div>
            ))}
          </div>
          <div style={S.card}><div style={S.cardTitle}>Value Distribution</div><PlotlyChart figure={catBarFig} /></div>
        </>
      )}
    </div>
  );
}

function TrendTab({ allCols, numCols, rows }) {
  const dateCols = allCols.filter(c=>c.toLowerCase().includes("date")||c.toLowerCase().includes("time")||c.toLowerCase().includes("year")||c.toLowerCase().includes("month"));
  const [dateCol, setDateCol] = useState(dateCols[0]||allCols[0]||"");
  const [metricCol, setMetricCol] = useState(numCols[0]||"");
  const [maWindow, setMaWindow]   = useState(7);

  const { lineFig, maFig, summaryMetrics } = useMemo(()=>{
    if(!dateCol||!metricCol) return {};
    const sorted = [...rows].filter(r=>r[dateCol]!=null&&r[metricCol]!=null).sort((a,b)=>String(a[dateCol]).localeCompare(String(b[dateCol])));
    const xs = sorted.map(r=>r[dateCol]);
    const ys = sorted.map(r=>Number(r[metricCol])||0);
    const ma = ys.map((_,i)=>{ const w=ys.slice(Math.max(0,i-maWindow+1),i+1); return w.reduce((a,b)=>a+b,0)/w.length; });
    const first=ys[0]||0, last=ys[ys.length-1]||0;
    const changePct = first?((last-first)/Math.abs(first)*100).toFixed(1):0;
    const avg = (ys.reduce((a,b)=>a+b,0)/ys.length).toFixed(2);
    const mean = ys.reduce((a,b)=>a+b,0)/ys.length;
    const volatility = Math.sqrt(ys.reduce((a,v)=>a+(v-mean)**2,0)/ys.length).toFixed(2);
    const lineFig = { data:[{type:"scatter",mode:"lines",x:xs,y:ys,line:{color:"#6366f1",width:2},name:metricCol}], layout:{title:{text:`${metricCol} Over Time`,font:{size:12}}} };
    const maFig   = { data:[
      {type:"scatter",mode:"lines",x:xs,y:ys,line:{color:"rgba(99,102,241,.4)",width:1},name:"Raw"},
      {type:"scatter",mode:"lines",x:xs,y:ma,line:{color:"#f59e0b",width:2},name:`MA(${maWindow})`},
    ], layout:{title:{text:`Moving Average (${maWindow})`,font:{size:12}}} };
    return { lineFig, maFig, summaryMetrics:[["Change %",`${changePct}%`],["Average",avg],["Volatility",volatility]] };
  },[dateCol,metricCol,maWindow,rows]);

  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Date/Time Column</label>
          <select value={dateCol} onChange={e=>setDateCol(e.target.value)} style={S.select}>
            {allCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Metric Column</label>
          <select value={metricCol} onChange={e=>setMetricCol(e.target.value)} style={S.select}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div style={{minWidth:180}}>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:3}}>
            <label style={{fontSize:11,color:"#71717a"}}>Moving Average Window</label>
            <span style={{fontSize:11,color:"#6366f1",fontWeight:600}}>{maWindow}</span>
          </div>
          <input type="range" min={2} max={Math.max(2,Math.min(50,rows.length))} value={maWindow} onChange={e=>setMaWindow(Number(e.target.value))} style={{width:"100%",accentColor:"#6366f1"}} />
        </div>
      </div>

      {summaryMetrics && (
        <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
          {summaryMetrics.map(([l,v])=>(
            <div key={l} style={S.kpi}><div style={{fontSize:20,fontWeight:700,color:"#6366f1"}}>{v}</div><div style={{fontSize:11,color:"#52525b",marginTop:2}}>{l}</div></div>
          ))}
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
        {lineFig && <div style={S.card}><div style={S.cardTitle}>Line Chart</div><PlotlyChart figure={lineFig} /></div>}
        {maFig   && <div style={S.card}><div style={S.cardTitle}>Moving Average Overlay</div><PlotlyChart figure={maFig} /></div>}
      </div>
    </div>
  );
}

function ComparisonTab({ catCols, numCols, rows }) {
  const [groupCol, setGroupCol] = useState(catCols[0]||"");
  const [metricCol, setMetricCol] = useState(numCols[0]||"");
  const [agg, setAgg]           = useState("mean");

  const { avgFig, totalFig, table } = useMemo(()=>{
    if(!groupCol||!metricCol) return {};
    const groups = {};
    rows.forEach(r=>{ const g=r[groupCol]; const v=Number(r[metricCol]); if(g!=null&&!isNaN(v)){ if(!groups[g]) groups[g]=[]; groups[g].push(v); } });
    const entries = Object.entries(groups).map(([k,vs])=>{
      const sum=vs.reduce((a,b)=>a+b,0);
      const val = agg==="mean"?sum/vs.length:agg==="sum"?sum:vs.length;
      return [k,val];
    }).sort((a,b)=>b[1]-a[1]).slice(0,20);
    const avgFig = { data:[{type:"bar",x:entries.map(([k])=>k),y:entries.map(([,v])=>v),marker:{colorscale:"Blues",color:entries.map(([,v])=>v)}}], layout:{title:{text:`${agg} of ${metricCol} by ${groupCol}`,font:{size:12}}} };
    const totalFig = { data:[{type:"bar",x:entries.map(([k])=>k),y:entries.map(([,v])=>v),marker:{colorscale:"Reds",color:entries.map(([,v])=>v)}}], layout:{title:{text:`Total ${metricCol} by ${groupCol}`,font:{size:12}}} };
    return { avgFig, totalFig, table:entries };
  },[groupCol,metricCol,agg,rows]);

  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Group By (Categorical)</label>
          <select value={groupCol} onChange={e=>setGroupCol(e.target.value)} style={S.select}>
            {catCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Metric (Numeric)</label>
          <select value={metricCol} onChange={e=>setMetricCol(e.target.value)} style={S.select}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Aggregation</label>
          <select value={agg} onChange={e=>setAgg(e.target.value)} style={S.select}>
            {["mean","sum","count"].map(a=><option key={a}>{a}</option>)}
          </select>
        </div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:16}}>
        {avgFig   && <div style={S.card}><div style={S.cardTitle}>Average (Blues)</div><PlotlyChart figure={avgFig} /></div>}
        {totalFig && <div style={S.card}><div style={S.cardTitle}>Total (Reds)</div><PlotlyChart figure={totalFig} /></div>}
      </div>
      {table && (
        <div style={S.card}>
          <div style={S.cardTitle}>Comparison Table</div>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
            <thead><tr>{[groupCol,`${agg}(${metricCol})`].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
            <tbody>{table.map(([k,v])=><tr key={k}><td style={{padding:"7px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{k}</td><td style={{padding:"7px 12px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#6366f1",fontWeight:600}}>{typeof v==="number"?v.toFixed(2):v}</td></tr>)}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AutoInsightsTab({ info, numCols, catCols, rows }) {
  const [insights, setInsights] = useState(null);

  const generate = () => {
    const totalRows = info?.rows||rows.length;
    const totalCols = info?.columns||0;
    const missing   = Object.values(info?.missing_values||{}).reduce((a,b)=>a+b,0);
    const missingPct= totalRows>0?((missing/(totalRows*totalCols))*100).toFixed(1):0;

    const numStats2 = numCols.slice(0,3).map(col=>{
      const vals = rows.map(r=>Number(r[col])).filter(v=>!isNaN(v));
      if(!vals.length) return null;
      const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
      const std  = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length);
      const cv   = mean!==0?(std/Math.abs(mean)*100).toFixed(1):0;
      return { col, mean:mean.toFixed(2), std:std.toFixed(2), cv };
    }).filter(Boolean);

    const catStats2 = catCols.slice(0,2).map(col=>{
      const counts = {};
      rows.forEach(r=>{ const v=r[col]; if(v!=null) counts[v]=(counts[v]||0)+1; });
      const sorted = Object.entries(counts).sort((a,b)=>b[1]-a[1]);
      return { col, unique:sorted.length, top:sorted[0]?.[0]||"—", topCount:sorted[0]?.[1]||0 };
    });

    // Find strongest correlation
    let bestCorr = null, bestR = 0;
    for(let i=0;i<numCols.length;i++) for(let j=i+1;j<numCols.length;j++){
      const xs=rows.map(r=>Number(r[numCols[i]])).filter(v=>!isNaN(v));
      const ys=rows.map(r=>Number(r[numCols[j]])).filter(v=>!isNaN(v));
      const n=Math.min(xs.length,ys.length);
      if(n<5) continue;
      const mx=xs.slice(0,n).reduce((a,b)=>a+b,0)/n, my=ys.slice(0,n).reduce((a,b)=>a+b,0)/n;
      const num=xs.slice(0,n).reduce((a,v,k)=>a+(v-mx)*(ys[k]-my),0);
      const den=Math.sqrt(xs.slice(0,n).reduce((a,v)=>a+(v-mx)**2,0)*ys.slice(0,n).reduce((a,v)=>a+(v-my)**2,0));
      const r=den?num/den:0;
      if(Math.abs(r)>Math.abs(bestR)){bestR=r;bestCorr={a:numCols[i],b:numCols[j],r:r.toFixed(3)};}
    }

    setInsights({ totalRows, totalCols, missingPct, numStats2, catStats2, bestCorr });
  };

  const gradients = ["linear-gradient(135deg,#6366f1,#8b5cf6)","linear-gradient(135deg,#10b981,#059669)","linear-gradient(135deg,#f59e0b,#d97706)","linear-gradient(135deg,#ef4444,#dc2626)","linear-gradient(135deg,#0ea5e9,#0284c7)"];

  return (
    <div>
      <button onClick={generate} style={{...S.btn,marginBottom:20}}>💡 Generate Insights</button>
      {insights && (
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          {[
            { title:"📊 Dataset Overview", body:`${insights.totalRows.toLocaleString()} rows × ${insights.totalCols} columns. ${numCols.length} numeric and ${catCols.length} categorical features.` },
            { title:"🔍 Data Quality", body:`Missing data: ${insights.missingPct}% of all values. ${insights.missingPct<5?"Data quality looks good.":insights.missingPct<20?"Consider imputation for missing values.":"High missing rate — data cleaning recommended."}` },
            ...insights.numStats2.map(s=>({ title:`📈 ${s.col}`, body:`Mean: ${s.mean} · Std Dev: ${s.std} · Coefficient of Variation: ${s.cv}%. ${s.cv>100?"High variability detected.":s.cv<10?"Very stable distribution.":"Moderate variability."}` })),
            ...insights.catStats2.map(s=>({ title:`🏷️ ${s.col}`, body:`${s.unique} unique values. Most common: "${s.top}" (${s.topCount} occurrences, ${insights.totalRows>0?((s.topCount/insights.totalRows)*100).toFixed(1):0}% of data).` })),
            insights.bestCorr && { title:"🔗 Strongest Correlation", body:`${insights.bestCorr.a} ↔ ${insights.bestCorr.b}: r = ${insights.bestCorr.r}. ${Math.abs(insights.bestCorr.r)>0.7?"Strong correlation detected.":Math.abs(insights.bestCorr.r)>0.4?"Moderate correlation.":"Weak correlation."}` },
          ].filter(Boolean).map((ins,i)=>(
            <div key={i} style={{padding:"16px 20px",borderRadius:14,background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderLeft:`3px solid transparent`,backgroundImage:`${gradients[i%gradients.length].replace("linear-gradient","linear-gradient").replace("135deg","135deg").replace(")",", rgba(9,9,11,0))")},rgba(24,24,27,.95)`,backgroundOrigin:"border-box"}}>
              <div style={{fontSize:13,fontWeight:600,color:"#f4f4f5",marginBottom:4}}>{ins.title}</div>
              <div style={{fontSize:13,color:"#a1a1aa",lineHeight:1.6}}>{ins.body}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
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
  card:      { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"14px 12px 8px", overflow:"hidden" },
  cardTitle: { fontSize:11, fontWeight:600, color:"#3f3f46", textTransform:"uppercase", letterSpacing:"0.06em", marginBottom:4, paddingLeft:4 },
  kpi:       { flex:"1 1 120px", background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:12, padding:"14px 18px" },
  btn:       { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  select:    { padding:"8px 12px", borderRadius:8, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.09)", color:"#f4f4f5", fontSize:12, outline:"none" },
};
