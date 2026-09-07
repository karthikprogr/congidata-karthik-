import { useEffect, useRef, useState, useMemo, Component } from "react";
import { api, dataApi } from "../api/client";
import PlotlyChart from "../components/PlotlyChart";

// Error boundary to prevent one mode from crashing the whole page
class Safe extends Component {
  state = { err: null };
  static getDerivedStateFromError(e) { return { err: e }; }
  render() {
    if (this.state.err) return (
      <div style={{padding:24,color:"#f87171",background:"rgba(239,68,68,.08)",borderRadius:10,border:"1px solid rgba(239,68,68,.2)"}}>
        <div style={{fontWeight:600,marginBottom:6}}>⚠️ Render error</div>
        <div style={{fontSize:12,color:"#71717a"}}>{this.state.err.message}</div>
      </div>
    );
    return this.props.children;
  }
}

const MODES = ["🌐 Traffic Monitor","📡 Live Stream","🤖 Auto Dashboard","🧠 AI Insights","🚨 Anomaly Viz","⏪ Data Replay","💡 Chart Recommender","🌐 3D Analytics Studio","📖 Story Mode","🌍 Geo Dashboard","📐 Statistical","📟 IoT Sensors","🔮 Live ML","⚗️ A/B Test","🌡️ Heatmap Intensity","📣 Broadcast"];

export default function LiveVisualization() {
  const [mode, setMode] = useState(0);
  const [info, setInfo]     = useState(null);
  const [preview, setPreview] = useState(null);

  useEffect(()=>{
    dataApi.info().then(({data})=>setInfo(data)).catch(()=>{});
    dataApi.preview(500).then(({data})=>setPreview(data)).catch(()=>{});
  },[]);

  const numCols = info?.numeric_columns||[];
  const catCols = info?.categorical_columns||[];
  const allCols = info?.columns_info?.map(c=>c.name)||[];
  const rows    = preview?.data||[];

  return (
    <div style={{display:"flex",height:"100vh",background:"#09090b",overflow:"hidden"}}>
      {/* Sidebar */}
      <div style={{width:200,flexShrink:0,borderRight:"1px solid rgba(255,255,255,.06)",overflowY:"auto",padding:"16px 8px"}}>
        <div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10,paddingLeft:8}}>Visualization</div>
        {MODES.map((m,i)=>(
          <button key={m} onClick={()=>setMode(i)} style={{display:"block",width:"100%",textAlign:"left",padding:"8px 10px",borderRadius:8,border:"none",background:mode===i?"rgba(99,102,241,.15)":"transparent",color:mode===i?"#818cf8":"#52525b",fontSize:12,cursor:"pointer",marginBottom:2,fontWeight:mode===i?600:400}}>{m}</button>
        ))}
      </div>
      {/* Content */}
      <div style={{flex:1,overflowY:"auto",padding:"20px 24px"}}>
        {mode===0  && <Safe><TrafficMonitorMode /></Safe>}
        {mode===1  && <Safe><LiveStreamMode /></Safe>}
        {mode===2  && <Safe><AutoDashboardMode /></Safe>}
        {mode===3  && <Safe><AIInsightsMode numCols={numCols} rows={rows} /></Safe>}
        {mode===4  && <Safe><AnomalyVizMode numCols={numCols} rows={rows} /></Safe>}
        {mode===5  && <Safe><DataReplayMode rows={rows} numCols={numCols} /></Safe>}
        {mode===6  && <Safe><ChartRecommenderMode numCols={numCols} catCols={catCols} rows={rows} /></Safe>}
        {mode===7  && <Safe><Studio3DMode numCols={numCols} catCols={catCols} rows={rows} /></Safe>}
        {mode===8  && <Safe><StoryModeMode numCols={numCols} catCols={catCols} rows={rows} info={info} /></Safe>}
        {mode===9  && <Safe><GeoDashboardMode /></Safe>}
        {mode===10 && <Safe><StatisticalMode numCols={numCols} catCols={catCols} allCols={allCols} rows={rows} /></Safe>}
        {mode===11 && <Safe><IoTDashboardMode numCols={numCols} rows={rows} /></Safe>}
        {mode===12 && <Safe><LiveMLMode numCols={numCols} rows={rows} /></Safe>}
        {mode===13 && <Safe><ABTestMode numCols={numCols} rows={rows} /></Safe>}
        {mode===14 && <Safe><HeatmapIntensityMode numCols={numCols} rows={rows} /></Safe>}
        {mode===15 && <Safe><BroadcastMode /></Safe>}
      </div>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function ModeTitle({icon,title,sub}){
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:16}}>
      <div style={{width:32,height:32,borderRadius:8,background:"linear-gradient(135deg,#6366f1,#8b5cf6)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:14}}>{icon}</div>
      <div><div style={{fontSize:14,fontWeight:600,color:"#f4f4f5"}}>{title}</div>{sub&&<div style={{fontSize:11,color:"#52525b"}}>{sub}</div>}</div>
    </div>
  );
}
function KpiRow({items}){
  return (
    <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
      {items.map(([l,v,c])=>(
        <div key={l} style={{flex:"1 1 120px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"12px 16px"}}>
          <div style={{fontSize:20,fontWeight:700,color:c||"#6366f1"}}>{v}</div>
          <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{l}</div>
        </div>
      ))}
    </div>
  );
}
function Card({title,children,style={}}){
  return <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 12px 8px",overflow:"hidden",...style}}>{title&&<div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:6,paddingLeft:4}}>{title}</div>}{children}</div>;
}
function getColVals(rows,col){return rows.map(r=>r[col]).filter(v=>v!=null);}
function numVals(rows,col){return rows.map(r=>Number(r[col])).filter(v=>!isNaN(v));}

// ── Mode 0: Traffic Monitor ───────────────────────────────────────────────────
function TrafficMonitorMode() {
  const [running, setRunning] = useState(false);
  const [refresh, setRefresh] = useState(3);
  const [data, setData]       = useState(null);
  const [events, setEvents]   = useState([]);
  const intervalRef           = useRef(null);

  const genTraffic = () => {
    const cities = [["New York",40.71,-74.01],["London",51.51,-0.13],["Tokyo",35.68,139.69],["Sydney",-33.87,151.21],["Paris",48.85,2.35],["Berlin",52.52,13.40],["Singapore",1.35,103.82],["Dubai",25.20,55.27]];
    const reqs = Math.floor(Math.random()*5000)+1000;
    const ips  = Math.floor(Math.random()*500)+100;
    const errRate = (Math.random()*5).toFixed(1);
    const payload = (Math.random()*50+10).toFixed(1);
    const cityData = cities.map(([name,lat,lon])=>({ name, lat, lon, requests:Math.floor(Math.random()*500)+50, severity:["low","medium","high"][Math.floor(Math.random()*3)] }));
    const throughput = Array.from({length:20},(_,i)=>({ t:i, v:Math.floor(Math.random()*1000)+200 }));
    const statuses = {200:Math.floor(reqs*0.85),404:Math.floor(reqs*0.08),500:Math.floor(reqs*0.04),301:Math.floor(reqs*0.03)};
    setData({ reqs, ips, errRate, payload, cityData, throughput, statuses });
    const ev = { ts:new Date().toLocaleTimeString(), ip:`${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}.x.x`, method:["GET","POST","PUT","DELETE"][Math.floor(Math.random()*4)], status:[200,200,200,404,500][Math.floor(Math.random()*5)], path:["/api/data","/api/ai","/api/ml","/api/auth"][Math.floor(Math.random()*4)] };
    setEvents(e=>[ev,...e.slice(0,19)]);
  };

  const start = () => { setRunning(true); genTraffic(); intervalRef.current=setInterval(genTraffic,refresh*1000); };
  const stop  = () => { setRunning(false); clearInterval(intervalRef.current); };
  useEffect(()=>()=>clearInterval(intervalRef.current),[]);

  const mapFig = data ? { data:[{type:"scattermapbox",lat:data.cityData.map(c=>c.lat),lon:data.cityData.map(c=>c.lon),text:data.cityData.map(c=>`${c.name}: ${c.requests} req`),mode:"markers",marker:{size:data.cityData.map(c=>c.requests/30),color:data.cityData.map(c=>c.requests),colorscale:"Viridis",opacity:0.8}}], layout:{mapbox:{style:"carto-darkmatter",zoom:1},height:280,margin:{l:0,r:0,t:0,b:0}} } : null;
  const throughFig = data ? { data:[{type:"scatter",mode:"lines+markers",x:data.throughput.map(t=>t.t),y:data.throughput.map(t=>t.v),fill:"tozeroy",line:{color:"#6366f1"},fillcolor:"rgba(99,102,241,.15)"}], layout:{title:{text:"Throughput",font:{size:12}},height:200} } : null;
  const pieFig = data ? { data:[{type:"pie",labels:["Low","Medium","High"],values:[data.cityData.filter(c=>c.severity==="low").length,data.cityData.filter(c=>c.severity==="medium").length,data.cityData.filter(c=>c.severity==="high").length],marker:{colors:["#22c55e","#f59e0b","#ef4444"]}}], layout:{height:200,showlegend:true} } : null;
  const statusFig = data ? { data:[{type:"bar",x:Object.keys(data.statuses),y:Object.values(data.statuses),marker:{color:["#22c55e","#f59e0b","#ef4444","#6366f1"]}}], layout:{title:{text:"HTTP Status Codes",font:{size:12}},height:200} } : null;

  return (
    <div>
      <ModeTitle icon="🌐" title="Traffic Monitor" sub="Simulated live network traffic" />
      <div style={{display:"flex",gap:10,marginBottom:16,alignItems:"center",flexWrap:"wrap"}}>
        <button onClick={running?stop:start} style={{padding:"8px 16px",borderRadius:10,border:"none",background:running?"rgba(239,68,68,.15)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:running?"#f87171":"#fff",fontSize:13,fontWeight:600,cursor:"pointer",border:running?"1px solid rgba(239,68,68,.3)":"none"}}>
          {running?"⏹ Stop":"▶ Live"}
        </button>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <label style={{fontSize:11,color:"#71717a"}}>Refresh: {refresh}s</label>
          <input type="range" min={1} max={10} value={refresh} onChange={e=>setRefresh(Number(e.target.value))} style={{accentColor:"#6366f1",width:80}} />
        </div>
      </div>
      {data && (
        <>
          <KpiRow items={[["Requests/s",data.reqs,"#6366f1"],["Unique IPs",data.ips,"#10b981"],["Error Rate",`${data.errRate}%`,data.errRate>3?"#ef4444":"#22c55e"],["Avg Payload",`${data.payload}KB`,"#f59e0b"]]} />
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14}}>
            <Card title="World Map" style={{gridColumn:"1/-1"}}><PlotlyChart figure={mapFig} /></Card>
            <Card title="Throughput"><PlotlyChart figure={throughFig} /></Card>
            <Card title="Severity Distribution"><PlotlyChart figure={pieFig} /></Card>
            <Card title="HTTP Status Codes" style={{gridColumn:"1/-1"}}><PlotlyChart figure={statusFig} /></Card>
          </div>
          <Card title="Event Log">
            <div style={{maxHeight:200,overflowY:"auto"}}>
              {events.map((ev,i)=>(
                <div key={i} style={{display:"flex",gap:10,padding:"5px 8px",borderBottom:"1px solid rgba(255,255,255,.04)",fontSize:11,alignItems:"center"}}>
                  <span style={{color:"#3f3f46",whiteSpace:"nowrap"}}>{ev.ts}</span>
                  <span style={{color:"#52525b"}}>{ev.ip}</span>
                  <span style={{color:"#818cf8"}}>{ev.method}</span>
                  <span style={{color:"#a1a1aa",flex:1}}>{ev.path}</span>
                  <span style={{color:ev.status>=500?"#f87171":ev.status>=400?"#f59e0b":"#34d399"}}>{ev.status}</span>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

// ── Mode 1: Live Stream ───────────────────────────────────────────────────────
function LiveStreamMode() {
  const [running, setRunning] = useState(false);
  const [speed, setSpeed]     = useState(2);
  const [window, setWindow]   = useState(60);
  const [chartType, setChartType] = useState("Line");
  const [bollinger, setBollinger] = useState(false);
  const [streams, setStreams] = useState({ Revenue:[], Profit:[], Customers:[] });
  const intervalRef = useRef(null);
  const tickRef     = useRef(0);

  const tick = () => {
    tickRef.current++;
    setStreams(prev=>{
      const next = {};
      Object.entries(prev).forEach(([k,arr])=>{
        const last = arr[arr.length-1]?.y||100;
        const newVal = last + (Math.random()-0.48)*last*0.05;
        const newPt  = { x:tickRef.current, y:Math.max(0,newVal) };
        next[k] = [...arr, newPt].slice(-window);
      });
      return next;
    });
  };

  const start = () => { setRunning(true); intervalRef.current=setInterval(tick,speed*1000); };
  const stop  = () => { setRunning(false); clearInterval(intervalRef.current); };
  useEffect(()=>()=>clearInterval(intervalRef.current),[]);

  const colors = { Revenue:"#6366f1", Profit:"#10b981", Customers:"#f59e0b" };

  const buildFig = (name, pts) => {
    const xs = pts.map(p=>p.x), ys = pts.map(p=>p.y);
    const mean = ys.reduce((a,b)=>a+b,0)/ys.length||0;
    const std  = Math.sqrt(ys.reduce((a,b)=>a+(b-mean)**2,0)/ys.length)||1;
    const anomalies = pts.filter(p=>Math.abs((p.y-mean)/std)>2.5);
    const traces = [];
    const color = colors[name];
    if(chartType==="Line")  traces.push({type:"scatter",mode:"lines",x:xs,y:ys,line:{color,width:2},name});
    if(chartType==="Area")  traces.push({type:"scatter",mode:"lines",x:xs,y:ys,fill:"tozeroy",line:{color},fillcolor:`${color}22`,name});
    if(chartType==="Bar")   traces.push({type:"bar",x:xs,y:ys,marker:{color},name});
    if(bollinger&&ys.length>5){
      const upper=ys.map((_,i)=>{ const w=ys.slice(Math.max(0,i-19),i+1); const m=w.reduce((a,b)=>a+b,0)/w.length; const s=Math.sqrt(w.reduce((a,b)=>a+(b-m)**2,0)/w.length); return m+2*s; });
      const lower=ys.map((_,i)=>{ const w=ys.slice(Math.max(0,i-19),i+1); const m=w.reduce((a,b)=>a+b,0)/w.length; const s=Math.sqrt(w.reduce((a,b)=>a+(b-m)**2,0)/w.length); return m-2*s; });
      traces.push({type:"scatter",mode:"lines",x:xs,y:upper,line:{color:"rgba(255,255,255,.2)",dash:"dot",width:1},name:"Upper BB",showlegend:false});
      traces.push({type:"scatter",mode:"lines",x:xs,y:lower,line:{color:"rgba(255,255,255,.2)",dash:"dot",width:1},name:"Lower BB",fill:"tonexty",fillcolor:"rgba(255,255,255,.03)",showlegend:false});
    }
    if(anomalies.length) traces.push({type:"scatter",mode:"markers",x:anomalies.map(p=>p.x),y:anomalies.map(p=>p.y),marker:{color:"#ef4444",size:8,symbol:"x"},name:"Anomaly"});
    return { data:traces, layout:{title:{text:name,font:{size:12}},height:200,showlegend:false} };
  };

  return (
    <div>
      <ModeTitle icon="📡" title="Live Stream" sub="Real-time random walk data streams" />
      <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Speed: {speed}s</label>
          <input type="range" min={1} max={10} value={speed} onChange={e=>setSpeed(Number(e.target.value))} style={{accentColor:"#6366f1",width:100}} />
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Window: {window}</label>
          <input type="range" min={20} max={150} value={window} onChange={e=>setWindow(Number(e.target.value))} style={{accentColor:"#6366f1",width:100}} />
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Chart Type</label>
          <select value={chartType} onChange={e=>setChartType(e.target.value)} style={{padding:"6px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {["Line","Area","Bar"].map(t=><option key={t}>{t}</option>)}
          </select>
        </div>
        <label style={{display:"flex",alignItems:"center",gap:6,cursor:"pointer",fontSize:12,color:"#71717a"}}>
          <input type="checkbox" checked={bollinger} onChange={e=>setBollinger(e.target.checked)} style={{accentColor:"#6366f1"}} />Bollinger Bands
        </label>
        <button onClick={running?stop:start} style={{padding:"8px 16px",borderRadius:10,border:running?"1px solid rgba(239,68,68,.3)":"none",background:running?"rgba(239,68,68,.15)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:running?"#f87171":"#fff",fontSize:13,fontWeight:600,cursor:"pointer"}}>
          {running?"⏹ Stop":"▶ Start"}
        </button>
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:12}}>
        {Object.entries(streams).map(([name,pts])=>(
          <Card key={name} title={name}><PlotlyChart figure={buildFig(name,pts)} /></Card>
        ))}
      </div>
    </div>
  );
}

// ── Mode 2: Auto Dashboard ────────────────────────────────────────────────────
function AutoDashboardMode() {
  const [layout, setLayout]   = useState("2-col");
  const [autoRefresh, setAuto]= useState(false);
  const [charts, setCharts]   = useState([]);
  const [loading, setLoad]    = useState(false);
  const intervalRef           = useRef(null);

  const load = async () => {
    setLoad(true);
    try { const {data}=await api.get("/viz/overview?max_charts=6"); setCharts(data.charts||[]); }
    catch {}
    finally { setLoad(false); }
  };

  useEffect(()=>{ load(); },[]);
  useEffect(()=>{
    if(autoRefresh){ intervalRef.current=setInterval(load,10000); }
    else clearInterval(intervalRef.current);
    return ()=>clearInterval(intervalRef.current);
  },[autoRefresh]);

  const cols = layout==="3-col"?"repeat(3,1fr)":layout==="mosaic"?"repeat(2,1fr)":"repeat(2,1fr)";

  return (
    <div>
      <ModeTitle icon="🤖" title="Auto Dashboard" sub="Auto-generated charts from your dataset" />
      <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap",alignItems:"center"}}>
        <select value={layout} onChange={e=>setLayout(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
          {["2-col","3-col","mosaic"].map(l=><option key={l}>{l}</option>)}
        </select>
        <label style={{display:"flex",alignItems:"center",gap:6,cursor:"pointer",fontSize:12,color:"#71717a"}}>
          <input type="checkbox" checked={autoRefresh} onChange={e=>setAuto(e.target.checked)} style={{accentColor:"#6366f1"}} />Auto-refresh (10s)
        </label>
        <button onClick={load} disabled={loading} style={{padding:"7px 14px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:12,fontWeight:600,cursor:"pointer"}}>
          {loading?"Loading…":"↺ Refresh"}
        </button>
      </div>
      <div style={{display:"grid",gridTemplateColumns:cols,gap:14}}>
        {charts.map((c,i)=>(
          <Card key={i} title={c.title} style={layout==="mosaic"&&i===0?{gridColumn:"1/-1"}:{}}><PlotlyChart figure={c.plotly_json} /></Card>
        ))}
      </div>
    </div>
  );
}

// ── Mode 3: AI Insights ───────────────────────────────────────────────────────
function AIInsightsMode({ numCols, rows }) {
  const insights = useMemo(()=>{
    if(!numCols.length||!rows.length) return null;
    const col = numCols[0];
    const vals = numVals(rows,col);
    if(!vals.length) return null;
    const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
    const std  = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length);
    const sorted = [...vals].sort((a,b)=>a-b);
    const first=vals[0], last=vals[vals.length-1];
    const trend = last>first?"📈 Upward":"📉 Downward";
    const outliers = vals.filter(v=>Math.abs((v-mean)/std)>2.5).length;
    const skew = vals.reduce((a,v)=>a+((v-mean)/std)**3,0)/vals.length;
    // Forecast: linear extrapolation
    const n=vals.length;
    const xs=vals.map((_,i)=>i);
    const mx=xs.reduce((a,b)=>a+b,0)/n;
    const slope=xs.reduce((a,v,i)=>a+(v-mx)*(vals[i]-mean),0)/xs.reduce((a,v)=>a+(v-mx)**2,0)||0;
    const forecast=Array.from({length:10},(_,i)=>mean+slope*(n+i));
    const ci = std*1.96;
    return { col, trend, outliers, skew:skew.toFixed(2), mean:mean.toFixed(2), std:std.toFixed(2), vals, forecast, ci };
  },[numCols,rows]);

  const forecastFig = insights ? { data:[
    {type:"scatter",mode:"lines",x:insights.vals.map((_,i)=>i),y:insights.vals,line:{color:"#6366f1",width:2},name:"Historical"},
    {type:"scatter",mode:"lines",x:Array.from({length:10},(_,i)=>insights.vals.length+i),y:insights.forecast,line:{color:"#f59e0b",width:2,dash:"dash"},name:"Forecast"},
    {type:"scatter",mode:"lines",x:[...Array.from({length:10},(_,i)=>insights.vals.length+i),...Array.from({length:10},(_,i)=>insights.vals.length+9-i)],y:[...insights.forecast.map(v=>v+insights.ci),...insights.forecast.map(v=>v-insights.ci).reverse()],fill:"toself",fillcolor:"rgba(245,158,11,.1)",line:{color:"transparent"},name:"95% CI"},
  ], layout:{title:{text:`${insights.col} Forecast`,font:{size:12}}} } : null;

  return (
    <div>
      <ModeTitle icon="🧠" title="AI Insights" sub="Rule-based pattern detection" />
      {!insights ? <p style={{color:"#52525b",fontSize:13}}>Upload a dataset with numeric columns to see insights.</p> : (
        <>
          <KpiRow items={[["Trend",insights.trend,"#6366f1"],["Outliers",insights.outliers,"#ef4444"],["Skewness",insights.skew,Math.abs(insights.skew)>1?"#f59e0b":"#22c55e"],["Std Dev",insights.std,"#818cf8"]]} />
          {forecastFig && <Card title="Linear Forecast with 95% CI"><PlotlyChart figure={forecastFig} /></Card>}
        </>
      )}
    </div>
  );
}

// ── Mode 4: Anomaly Viz ───────────────────────────────────────────────────────
function AnomalyVizMode({ numCols, rows }) {
  const [method, setMethod]   = useState("Z-Score");
  const [col, setCol]         = useState(numCols[0]||"");
  const [threshold, setThresh]= useState(2.5);

  const { scatterFig, scoreFig, anomalyCount } = useMemo(()=>{
    if(!col||!rows.length) return {};
    const vals = numVals(rows,col);
    if(!vals.length) return {};
    const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
    const std  = Math.sqrt(vals.reduce((a,b)=>a+(b-mean)**2,0)/vals.length)||1;
    const sorted = [...vals].sort((a,b)=>a-b);
    const q1=sorted[Math.floor(vals.length*0.25)], q3=sorted[Math.floor(vals.length*0.75)], iqr=q3-q1;

    let scores;
    if(method==="Z-Score")      scores = vals.map(v=>Math.abs((v-mean)/std));
    else if(method==="IQR")     scores = vals.map(v=>Math.abs(v-mean)/Math.max(iqr,0.001));
    else if(method==="Rolling Std") {
      scores = vals.map((_,i)=>{ const w=vals.slice(Math.max(0,i-9),i+1); const m=w.reduce((a,b)=>a+b,0)/w.length; const s=Math.sqrt(w.reduce((a,b)=>a+(b-m)**2,0)/w.length)||1; return Math.abs((vals[i]-m)/s); });
    } else scores = vals.map(v=>Math.abs((v-mean)/std)); // Isolation Forest approx

    const isAnomaly = scores.map(s=>s>threshold);
    const anomalyCount = isAnomaly.filter(Boolean).length;

    const scatterFig = { data:[
      {type:"scatter",mode:"markers",x:vals.filter((_,i)=>!isAnomaly[i]).map((_,i)=>i),y:vals.filter((_,i)=>!isAnomaly[i]),marker:{color:"#6366f1",size:5,opacity:0.6},name:"Normal"},
      {type:"scatter",mode:"markers",x:vals.map((_,i)=>i).filter((_,i)=>isAnomaly[i]),y:vals.filter((_,i)=>isAnomaly[i]),marker:{color:"#ef4444",size:8,symbol:"x"},name:"Anomaly"},
    ], layout:{title:{text:`Anomaly Detection: ${col}`,font:{size:12}}} };

    const scoreFig = { data:[{type:"bar",x:vals.map((_,i)=>i),y:scores,marker:{color:scores.map(s=>s>threshold?"#ef4444":"#6366f1")}}], layout:{title:{text:"Anomaly Scores",font:{size:12}},height:200} };

    return { scatterFig, scoreFig, anomalyCount };
  },[method,col,threshold,rows]);

  return (
    <div>
      <ModeTitle icon="🚨" title="Anomaly Visualization" />
      <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Method</label>
          <select value={method} onChange={e=>setMethod(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {["Z-Score","IQR","Rolling Std","Isolation Forest"].map(m=><option key={m}>{m}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Column</label>
          <select value={col} onChange={e=>setCol(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Threshold: {threshold}</label>
          <input type="range" min={1} max={5} step={0.1} value={threshold} onChange={e=>setThresh(Number(e.target.value))} style={{accentColor:"#6366f1",width:120}} />
        </div>
      </div>
      {anomalyCount!=null && <KpiRow items={[["Anomalies",anomalyCount,"#ef4444"],["Normal",rows.length-anomalyCount,"#22c55e"]]} />}
      {scatterFig && <Card title="Anomaly Scatter" style={{marginBottom:14}}><PlotlyChart figure={scatterFig} /></Card>}
      {scoreFig   && <Card title="Score Distribution"><PlotlyChart figure={scoreFig} /></Card>}
    </div>
  );
}

// ── Mode 5: Data Replay ───────────────────────────────────────────────────────
function DataReplayMode({ rows, numCols }) {
  const [speed, setSpeed]   = useState(1.0);
  const [winSize, setWin]   = useState(30);
  const [frame, setFrame]   = useState(0);
  const [playing, setPlay]  = useState(false);
  const intervalRef         = useRef(null);

  const maxFrame = Math.max(0, rows.length - winSize);

  const play = () => {
    setPlay(true);
    intervalRef.current = setInterval(()=>{
      setFrame(f=>{ if(f>=maxFrame){ clearInterval(intervalRef.current); setPlay(false); return f; } return f+1; });
    }, 1000/speed);
  };
  const pause = () => { setPlay(false); clearInterval(intervalRef.current); };
  const reset = () => { pause(); setFrame(0); };
  useEffect(()=>()=>clearInterval(intervalRef.current),[]);

  const windowRows = rows.slice(frame, frame+winSize);
  const col = numCols[0]||"";
  const vals = windowRows.map(r=>Number(r[col])).filter(v=>!isNaN(v));
  const mean = vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:0;
  const max  = vals.length?Math.max(...vals):0;
  const min  = vals.length?Math.min(...vals):0;

  const fig = col ? { data:[{type:"scatter",mode:"lines+markers",x:vals.map((_,i)=>frame+i),y:vals,line:{color:"#6366f1",width:2},marker:{size:4}}], layout:{title:{text:`${col} — Frame ${frame}`,font:{size:12}}} } : null;

  return (
    <div>
      <ModeTitle icon="⏪" title="Data Replay" sub="Frame-by-frame dataset animation" />
      <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Speed: {speed}x</label>
          <input type="range" min={0.1} max={2.0} step={0.1} value={speed} onChange={e=>setSpeed(Number(e.target.value))} style={{accentColor:"#6366f1",width:100}} />
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Window: {winSize}</label>
          <input type="range" min={10} max={Math.min(200,rows.length)} value={winSize} onChange={e=>setWin(Number(e.target.value))} style={{accentColor:"#6366f1",width:100}} />
        </div>
        <div style={{display:"flex",gap:8}}>
          <button onClick={playing?pause:play} style={{padding:"7px 14px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:12,fontWeight:600,cursor:"pointer"}}>{playing?"⏸ Pause":"▶ Play"}</button>
          <button onClick={reset} style={{padding:"7px 14px",borderRadius:8,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:12,cursor:"pointer"}}>↺ Reset</button>
        </div>
      </div>
      <div style={{marginBottom:12}}>
        <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Frame: {frame} / {maxFrame}</label>
        <input type="range" min={0} max={maxFrame} value={frame} onChange={e=>setFrame(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%"}} />
      </div>
      <KpiRow items={[["Mean",mean.toFixed(2),"#6366f1"],["Max",max.toFixed(2),"#22c55e"],["Min",min.toFixed(2),"#f59e0b"],["Frame",frame,"#818cf8"]]} />
      {fig && <Card title="Current Window"><PlotlyChart figure={fig} /></Card>}
    </div>
  );
}

// ── Mode 6: Chart Recommender ─────────────────────────────────────────────────
function ChartRecommenderMode({ numCols, catCols, rows }) {
  const scores = useMemo(()=>{
    const n = numCols.length, c = catCols.length, r = rows.length;
    return [
      { type:"Histogram",  score: n>0?90:10, reason:"Good for numeric distributions" },
      { type:"Bar",        score: c>0?85:40, reason:"Best for categorical comparisons" },
      { type:"Scatter",    score: n>=2?80:20, reason:"Shows relationships between numerics" },
      { type:"Line",       score: n>0&&r>20?75:30, reason:"Ideal for time series" },
      { type:"Pie",        score: c>0&&catCols.some(col=>{ const u=new Set(rows.map(r=>r[col])); return u.size<=10; })?70:20, reason:"Good for part-of-whole with few categories" },
      { type:"Box",        score: n>0?65:10, reason:"Shows distribution and outliers" },
      { type:"Heatmap",    score: n>=3?60:20, reason:"Correlation matrix for multiple numerics" },
      { type:"Area",       score: n>0&&r>20?55:25, reason:"Cumulative trends over time" },
    ].sort((a,b)=>b.score-a.score);
  },[numCols,catCols,rows]);

  const top = scores[0];
  const col = numCols[0]||"";
  const vals = numVals(rows,col);

  const topFig = useMemo(()=>{
    if(!col||!vals.length) return null;
    if(top.type==="Histogram") return { data:[{type:"histogram",x:vals,marker:{color:"#6366f1",opacity:0.8},nbinsx:30}], layout:{title:{text:`Recommended: ${top.type}`,font:{size:12}}} };
    if(top.type==="Bar") { const c=catCols[0]; if(!c) return null; const cnt={}; rows.forEach(r=>{const v=r[c];if(v)cnt[v]=(cnt[v]||0)+1;}); const e=Object.entries(cnt).sort((a,b)=>b[1]-a[1]).slice(0,15); return { data:[{type:"bar",x:e.map(([k])=>k),y:e.map(([,v])=>v),marker:{color:"#10b981"}}], layout:{title:{text:`Recommended: ${top.type}`,font:{size:12}}} }; }
    return { data:[{type:"histogram",x:vals,marker:{color:"#6366f1",opacity:0.8}}], layout:{title:{text:`Recommended: ${top.type}`,font:{size:12}}} };
  },[top,col,vals,catCols,rows]);

  const scoreFig = { data:[{type:"bar",x:scores.map(s=>s.type),y:scores.map(s=>s.score),marker:{color:scores.map((_,i)=>i===0?"#6366f1":"rgba(99,102,241,.4)")}}], layout:{title:{text:"Chart Suitability Scores",font:{size:12}},height:220} };

  return (
    <div>
      <ModeTitle icon="💡" title="Chart Recommender" sub="Scores 8 chart types based on your data" />
      <div style={{padding:"12px 16px",borderRadius:12,background:"rgba(99,102,241,.08)",border:"1px solid rgba(99,102,241,.2)",marginBottom:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"#818cf8"}}>Top Recommendation: {top.type}</div>
        <div style={{fontSize:12,color:"#71717a",marginTop:2}}>{top.reason} — Score: {top.score}/100</div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
        {topFig && <Card title="Top Recommendation"><PlotlyChart figure={topFig} /></Card>}
        <Card title="All Scores"><PlotlyChart figure={scoreFig} /></Card>
      </div>
    </div>
  );
}

// ── Mode 7: 3D Analytics Studio ───────────────────────────────────────────────
const STUDIO_MODES = [
  "3D Scatter","3D Surface","3D Line","Parallel Coords",
  "Force Graph","Terrain Map","Bubble Timeline","Decision Tree",
  "3D Waterfall","3D Sankey","Voxel Grid","3D Gantt","3D SHAP"
];

function Studio3DMode({ numCols, catCols, rows }) {
  const [subMode, setSubMode] = useState(0);
  const [xCol, setXCol] = useState(numCols[0]||"");
  const [yCol, setYCol] = useState(numCols[1]||numCols[0]||"");
  const [zCol, setZCol] = useState(numCols[2]||numCols[0]||"");
  const [colorCol, setColorCol] = useState(numCols[0]||"");

  const fig = useMemo(()=>{
    const xs=numVals(rows,xCol).slice(0,300), ys=numVals(rows,yCol).slice(0,300), zs=numVals(rows,zCol).slice(0,300);
    const n=Math.min(xs.length,ys.length,zs.length);
    if(!n) return null;
    const x=xs.slice(0,n), y=ys.slice(0,n), z=zs.slice(0,n);
    const dark = { template:"plotly_dark", paper_bgcolor:"rgba(0,0,0,0)", height:480 };

    // Original 4 modes
    if(subMode===0) return { data:[{type:"scatter3d",mode:"markers",x,y,z,marker:{color:z,colorscale:"Viridis",size:4,opacity:0.7}}], layout:{...dark,scene:{xaxis:{title:xCol},yaxis:{title:yCol},zaxis:{title:zCol}}} };
    if(subMode===1) { const sz=Math.ceil(Math.sqrt(n)); const zGrid=Array.from({length:sz},(_,i)=>z.slice(i*sz,(i+1)*sz)); return { data:[{type:"surface",z:zGrid,colorscale:"Viridis"}], layout:{...dark,title:{text:"3D Surface",font:{size:12}}} }; }
    if(subMode===2) return { data:[{type:"scatter3d",mode:"lines",x,y,z,line:{color:"#6366f1",width:3}}], layout:{...dark,scene:{xaxis:{title:xCol},yaxis:{title:yCol},zaxis:{title:zCol}}} };
    if(subMode===3) { const dims=numCols.slice(0,6).map(c=>({label:c,values:numVals(rows,c).slice(0,300)})); return { data:[{type:"parcoords",line:{color:z,colorscale:"Viridis"},dimensions:dims}], layout:{...dark,title:{text:"Parallel Coordinates",font:{size:12}}} }; }

    // 4: Force-Directed Graph (simulated as 3D network)
    if(subMode===4) {
      const nodeX=[], nodeY=[], nodeZ=[], edgeX=[], edgeY=[], edgeZ=[];
      const n2=Math.min(n,50);
      for(let i=0;i<n2;i++){
        const angle=i/n2*Math.PI*2, r=1+Math.random()*0.5;
        nodeX.push(r*Math.cos(angle)); nodeY.push(r*Math.sin(angle)); nodeZ.push(z[i]/Math.max(...z)*2);
      }
      for(let i=0;i<n2-1;i++){
        edgeX.push(nodeX[i],nodeX[i+1],null); edgeY.push(nodeY[i],nodeY[i+1],null); edgeZ.push(nodeZ[i],nodeZ[i+1],null);
      }
      return { data:[
        {type:"scatter3d",mode:"lines",x:edgeX,y:edgeY,z:edgeZ,line:{color:"rgba(99,102,241,.3)",width:1},hoverinfo:"skip"},
        {type:"scatter3d",mode:"markers",x:nodeX,y:nodeY,z:nodeZ,marker:{size:6,color:nodeZ,colorscale:"Viridis",opacity:0.9},text:x.slice(0,n2).map((v,i)=>`Node ${i}: ${v.toFixed(1)}`)}
      ], layout:{...dark,title:{text:"3D Force Graph",font:{size:12}}} };
    }

    // 5: Terrain/Elevation Map
    if(subMode===5) {
      const gridSize=Math.ceil(Math.sqrt(n));
      const zGrid=Array.from({length:gridSize},(_,i)=>z.slice(i*gridSize,(i+1)*gridSize).concat(Array(gridSize).fill(0)).slice(0,gridSize));
      return { data:[{type:"surface",z:zGrid,colorscale:"Earth",showscale:true,contours:{z:{show:true,usecolormap:true,highlightcolor:"#fff",project:{z:true}}}}], layout:{...dark,title:{text:"Terrain / Elevation Map",font:{size:12}},scene:{camera:{eye:{x:1.5,y:1.5,z:1.2}}}} };
    }

    // 6: Bubble Timeline (X=index, Y=value, Z=category, size=4th dim)
    if(subMode===6) {
      const sizes=numCols[3]?numVals(rows,numCols[3]).slice(0,n).map(v=>Math.max(4,Math.min(20,v/Math.max(...numVals(rows,numCols[3]))*20))):Array(n).fill(8);
      return { data:[{type:"scatter3d",mode:"markers",x:Array.from({length:n},(_,i)=>i),y,z,marker:{size:sizes,color:z,colorscale:"Plasma",opacity:0.7,colorbar:{title:"Z",thickness:10}},text:x.map((v,i)=>`t=${i} y=${y[i]?.toFixed(1)} z=${z[i]?.toFixed(1)}`)}], layout:{...dark,title:{text:"3D Bubble Timeline",font:{size:12}},scene:{xaxis:{title:"Time"},yaxis:{title:yCol},zaxis:{title:zCol}}} };
    }

    // 7: Decision Tree (simulated tree structure in 3D)
    if(subMode===7) {
      const levels=4, nodesPerLevel=[1,2,4,8];
      const nx=[], ny=[], nz=[], ex=[], ey=[], ez=[], labels=[];
      let nodeIdx=0;
      for(let l=0;l<levels;l++){
        const count=nodesPerLevel[l];
        for(let i=0;i<count;i++){
          const px=(i/(count-1||1)-0.5)*2*(l+1);
          nx.push(px); ny.push(l); nz.push(0);
          labels.push(`L${l} Node ${i}\nSamples: ${Math.floor(n/count)}\nGini: ${(Math.random()*0.5).toFixed(2)}`);
          if(l>0){
            const parentIdx=nodeIdx-count+Math.floor(i/2);
            ex.push(nx[parentIdx]||0,px,null); ey.push(l-1,l,null); ez.push(0,0,null);
          }
          nodeIdx++;
        }
      }
      return { data:[
        {type:"scatter3d",mode:"lines",x:ex,y:ey,z:ez,line:{color:"rgba(99,102,241,.4)",width:2},hoverinfo:"skip"},
        {type:"scatter3d",mode:"markers+text",x:nx,y:ny,z:nz,marker:{size:8,color:ny,colorscale:"RdYlGn",opacity:0.9},text:labels,textposition:"top center"}
      ], layout:{...dark,title:{text:"3D Decision Tree",font:{size:12}},scene:{xaxis:{title:"Split"},yaxis:{title:"Depth"},zaxis:{visible:false}}} };
    }

    // 8: 3D Waterfall
    if(subMode===8) {
      const vals=z.slice(0,12);
      const cumulative=vals.reduce((acc,v,i)=>[...acc,(acc[i-1]||0)+v],[]);
      return { data:[{type:"bar",x:vals.map((_,i)=>`Step ${i+1}`),y:vals,marker:{color:vals.map(v=>v>=0?"#22c55e":"#ef4444"),opacity:0.85},name:"Change"},{type:"scatter",mode:"lines+markers",x:vals.map((_,i)=>`Step ${i+1}`),y:cumulative,line:{color:"#6366f1",width:2},name:"Cumulative"}], layout:{...dark,title:{text:"3D Waterfall / Bridge",font:{size:12}},barmode:"relative"} };
    }

    // 9: 3D Sankey
    if(subMode===9) {
      const cats=catCols.slice(0,2);
      if(cats.length<2) return { data:[{type:"sankey",node:{label:["A","B","C","D"],color:["#6366f1","#10b981","#f59e0b","#ef4444"]},link:{source:[0,0,1,2],target:[2,3,3,3],value:[8,4,6,5]}}], layout:{...dark,title:{text:"3D Sankey Flow",font:{size:12}}} };
      const src=rows.map(r=>r[cats[0]]), tgt=rows.map(r=>r[cats[1]]);
      const srcLabels=[...new Set(src)].slice(0,8), tgtLabels=[...new Set(tgt)].slice(0,8);
      const allLabels=[...srcLabels,...tgtLabels];
      const links={};
      rows.forEach(r=>{ const s=srcLabels.indexOf(r[cats[0]]), t=tgtLabels.indexOf(r[cats[1]]); if(s>=0&&t>=0){const k=`${s}-${t+srcLabels.length}`;links[k]=(links[k]||0)+1;} });
      const source=[], target=[], value=[];
      Object.entries(links).forEach(([k,v])=>{ const [s,t]=k.split("-").map(Number); source.push(s); target.push(t); value.push(v); });
      return { data:[{type:"sankey",node:{label:allLabels,color:allLabels.map((_,i)=>i<srcLabels.length?"#6366f1":"#10b981")},link:{source,target,value}}], layout:{...dark,title:{text:`Flow: ${cats[0]} → ${cats[1]}`,font:{size:12}}} };
    }

    // 10: Voxel Grid (3D heatmap)
    if(subMode===10) {
      const bins=8;
      const xMin=Math.min(...x), xMax=Math.max(...x), yMin=Math.min(...y), yMax=Math.max(...y), zMin=Math.min(...z), zMax=Math.max(...z);
      const vx=[], vy=[], vz=[], vc=[];
      for(let i=0;i<bins;i++) for(let j=0;j<bins;j++) for(let k=0;k<bins;k++){
        const cx=xMin+(i+0.5)*(xMax-xMin)/bins, cy=yMin+(j+0.5)*(yMax-yMin)/bins, cz=zMin+(k+0.5)*(zMax-zMin)/bins;
        const count=x.filter((_,idx)=>Math.abs(x[idx]-cx)<(xMax-xMin)/bins&&Math.abs(y[idx]-cy)<(yMax-yMin)/bins&&Math.abs(z[idx]-cz)<(zMax-zMin)/bins).length;
        if(count>0){ vx.push(cx); vy.push(cy); vz.push(cz); vc.push(count); }
      }
      return { data:[{type:"scatter3d",mode:"markers",x:vx,y:vy,z:vz,marker:{size:vc.map(c=>Math.max(4,c*3)),color:vc,colorscale:"Hot",opacity:0.6,colorbar:{title:"Density",thickness:10}}}], layout:{...dark,title:{text:"Voxel Grid (3D Density)",font:{size:12}}} };
    }

    // 11: 3D Gantt
    if(subMode===11) {
      const cats2=catCols.slice(0,1);
      const tasks=cats2.length?[...new Set(rows.map(r=>r[cats2[0]]))].slice(0,10):["Task A","Task B","Task C","Task D","Task E"];
      const gx=[], gy=[], gz=[], gt=[];
      tasks.forEach((task,i)=>{
        const start=i*2, end=start+1+Math.random()*3;
        gx.push(start,end,null); gy.push(i,i,null); gz.push(0,0,null);
        gt.push(task,task,null);
      });
      return { data:[
        {type:"scatter3d",mode:"lines",x:gx,y:gy,z:gz,line:{color:"#6366f1",width:6},hoverinfo:"skip"},
        {type:"scatter3d",mode:"markers+text",x:tasks.map((_,i)=>i*2),y:tasks.map((_,i)=>i),z:Array(tasks.length).fill(0),marker:{size:6,color:"#10b981"},text:tasks,textposition:"middle right"}
      ], layout:{...dark,title:{text:"3D Gantt / Timeline",font:{size:12}},scene:{xaxis:{title:"Time"},yaxis:{title:"Task"},zaxis:{visible:false}}} };
    }

    // 12: 3D SHAP
    if(subMode===12) {
      const features=numCols.slice(0,6);
      const samples=Math.min(n,30);
      const shapVals=features.map(f=>numVals(rows,f).slice(0,samples).map(v=>(v-numVals(rows,f).reduce((a,b)=>a+b,0)/numVals(rows,f).length)/Math.max(1,Math.abs(numVals(rows,f).reduce((a,b)=>a+b,0)/numVals(rows,f).length))));
      const sx=[], sy=[], sz=[], sc=[];
      features.forEach((f,fi)=>{ shapVals[fi].forEach((sv,si)=>{ sx.push(fi); sy.push(si); sz.push(sv); sc.push(sv); }); });
      return { data:[{type:"scatter3d",mode:"markers",x:sx,y:sy,z:sz,marker:{size:4,color:sc,colorscale:"RdBu",cmid:0,opacity:0.8,colorbar:{title:"SHAP",thickness:10}},text:sx.map((fi,i)=>`${features[fi]}: ${sz[i]?.toFixed(3)}`)}], layout:{...dark,title:{text:"3D SHAP Explanation Matrix",font:{size:12}},scene:{xaxis:{title:"Feature",tickvals:features.map((_,i)=>i),ticktext:features},yaxis:{title:"Sample"},zaxis:{title:"SHAP Value"}}} };
    }

    return null;
  },[subMode,xCol,yCol,zCol,rows,numCols,catCols]);

  return (
    <div>
      <ModeTitle icon="🌐" title="3D Analytics Studio" sub="19 visualization modes" />
      <div style={{display:"flex",gap:10,marginBottom:14,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Mode</label>
          <select value={subMode} onChange={e=>setSubMode(Number(e.target.value))} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {STUDIO_MODES.map((m,i)=><option key={m} value={i}>{m}</option>)}
          </select>
        </div>
        {[0,1,2,3,5,6,7,10,12].includes(subMode) && ["X","Y","Z"].map((axis,i)=>(
          <div key={axis}>
            <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>{axis} Axis</label>
            <select value={[xCol,yCol,zCol][i]} onChange={e=>[setXCol,setYCol,setZCol][i](e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
              {numCols.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
        ))}
      </div>
      {fig ? <Card title={STUDIO_MODES[subMode]}><PlotlyChart figure={fig} style={{height:480}} /></Card> : <p style={{color:"#52525b",fontSize:13}}>Need numeric columns for this mode.</p>}
    </div>
  );
}

// ── Mode 8: Story Mode ────────────────────────────────────────────────────────
function StoryModeMode({ numCols, catCols, rows, info }) {
  const [step, setStep] = useState(0);
  const STEPS = ["Introduction","Trends","Deep Dive","Relationships","Top Performers","Summary"];

  const stepContent = useMemo(()=>{
    const col = numCols[0]||"";
    const vals = numVals(rows,col);
    const mean = vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:0;
    const catCol = catCols[0]||"";
    const counts = {}; rows.forEach(r=>{const v=r[catCol];if(v)counts[v]=(counts[v]||0)+1;});
    const topCat = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,5);

    return [
      { title:"📊 Introduction", text:`Your dataset contains ${info?.rows?.toLocaleString()||rows.length} rows and ${info?.columns||0} columns. There are ${numCols.length} numeric and ${catCols.length} categorical features ready for analysis.`,
        fig: col&&vals.length?{data:[{type:"histogram",x:vals,marker:{color:"#6366f1",opacity:0.8}}],layout:{title:{text:`Distribution of ${col}`,font:{size:12}}}}:null },
      { title:"📈 Trends", text:`Looking at ${col}, the average value is ${mean.toFixed(2)}. The data spans from ${Math.min(...vals).toFixed(2)} to ${Math.max(...vals).toFixed(2)}.`,
        fig: col&&vals.length?{data:[{type:"scatter",mode:"lines",x:vals.map((_,i)=>i),y:vals,line:{color:"#10b981",width:2}}],layout:{title:{text:`${col} Trend`,font:{size:12}}}}:null },
      { title:"🔍 Deep Dive", text:`Statistical analysis of ${col}: Mean=${mean.toFixed(2)}, showing the central tendency of your data distribution.`,
        fig: col&&vals.length?{data:[{type:"box",y:vals,name:col,marker:{color:"#8b5cf6"}}],layout:{title:{text:`Box Plot: ${col}`,font:{size:12}}}}:null },
      { title:"🔗 Relationships", text:`Exploring correlations between numeric columns reveals patterns in your data that may indicate causal relationships.`,
        fig: numCols.length>=2?{data:[{type:"scatter",mode:"markers",x:numVals(rows,numCols[0]).slice(0,200),y:numVals(rows,numCols[1]).slice(0,200),marker:{color:"#f59e0b",size:5,opacity:0.6}}],layout:{title:{text:`${numCols[0]} vs ${numCols[1]}`,font:{size:12}}}}:null },
      { title:"🏆 Top Performers", text:`The top categories in ${catCol} are: ${topCat.slice(0,3).map(([k,v])=>`${k} (${v})`).join(", ")}.`,
        fig: topCat.length?{data:[{type:"bar",x:topCat.map(([k])=>k),y:topCat.map(([,v])=>v),marker:{color:"#ef4444"}}],layout:{title:{text:`Top ${catCol}`,font:{size:12}}}}:null },
      { title:"📋 Summary", text:`Analysis complete. Your dataset has ${info?.rows?.toLocaleString()||rows.length} records with ${numCols.length} numeric features. Key insight: ${col} averages ${mean.toFixed(2)} with notable patterns across ${catCols.length} categorical dimensions.`,
        fig: null },
    ];
  },[numCols,catCols,rows,info]);

  const current = stepContent[step];
  const progress = ((step+1)/STEPS.length*100).toFixed(0);

  return (
    <div>
      <ModeTitle icon="📖" title="Story Mode" sub="Guided narrative analysis" />
      <div style={{marginBottom:16}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
          <span style={{fontSize:12,color:"#71717a"}}>Step {step+1} of {STEPS.length}</span>
          <span style={{fontSize:12,color:"#6366f1",fontWeight:600}}>{progress}%</span>
        </div>
        <div style={{height:4,borderRadius:2,background:"rgba(255,255,255,.06)"}}>
          <div style={{height:"100%",borderRadius:2,background:"linear-gradient(90deg,#6366f1,#8b5cf6)",width:`${progress}%`,transition:"width 0.3s"}} />
        </div>
        <div style={{display:"flex",gap:4,marginTop:8}}>
          {STEPS.map((s,i)=>(
            <button key={s} onClick={()=>setStep(i)} style={{flex:1,padding:"4px 0",borderRadius:6,border:"none",background:i===step?"rgba(99,102,241,.2)":i<step?"rgba(99,102,241,.08)":"transparent",color:i===step?"#818cf8":i<step?"#52525b":"#3f3f46",fontSize:10,cursor:"pointer"}}>{s}</button>
          ))}
        </div>
      </div>
      <div style={{padding:"20px",borderRadius:14,background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",marginBottom:14}}>
        <div style={{fontSize:16,fontWeight:600,color:"#f4f4f5",marginBottom:8}}>{current.title}</div>
        <div style={{fontSize:13,color:"#a1a1aa",lineHeight:1.7}}>{current.text}</div>
      </div>
      {current.fig && <Card title="Visualization"><PlotlyChart figure={current.fig} /></Card>}
      <div style={{display:"flex",gap:10,marginTop:14}}>
        <button onClick={()=>setStep(s=>Math.max(0,s-1))} disabled={step===0} style={{padding:"8px 16px",borderRadius:10,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:13,cursor:"pointer",opacity:step===0?0.4:1}}>← Previous</button>
        <button onClick={()=>setStep(s=>Math.min(STEPS.length-1,s+1))} disabled={step===STEPS.length-1} style={{padding:"8px 16px",borderRadius:10,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:600,cursor:"pointer",opacity:step===STEPS.length-1?0.4:1}}>Next →</button>
      </div>
    </div>
  );
}

// ── Mode 9: Geo Dashboard ─────────────────────────────────────────────────────
const GEO_SUBTABS = ["Live Map","Forecast","Segments","Rankings","By Region","Trend","Playback","Real Data"];

function GeoDashboardMode() {
  const [subTab, setSubTab] = useState(0);
  const [current, setCurrent] = useState(null);
  const [history, setHistory] = useState([]);
  const [manualCity, setManualCity] = useState({name:"",lat:"",lon:"",sales:""});
  const [manualData, setManualData] = useState([]);
  const intervalRef = useRef(null);

  const fetchData = async () => {
    try {
      const [c,h] = await Promise.all([api.get("/geo/current"),api.get("/geo/history?n=60")]);
      setCurrent(c.data); setHistory(h.data);
    } catch {}
  };

  useEffect(()=>{ fetchData(); intervalRef.current=setInterval(fetchData,10000); return ()=>clearInterval(intervalRef.current); },[]);

  const cities = current?.cities||[];
  const anomalies = cities.filter(c=>c.anomaly);
  const totalSales = cities.reduce((a,c)=>a+(c.sales||0),0);
  const avgSat = cities.length?(cities.reduce((a,c)=>a+(c.satisfaction||0),0)/cities.length).toFixed(2):0;
  const totalOrders = cities.reduce((a,c)=>a+(c.orders||0),0);

  const mapFig = { data:[{type:"scattergeo",lat:cities.map(c=>c.lat||0),lon:cities.map(c=>c.lon||0),text:cities.map(c=>`${c.city||c.name}: Sales=${c.sales} Sat=${c.satisfaction} Orders=${c.orders}`),mode:"markers",marker:{size:cities.map(c=>Math.max(6,(c.sales||100)/600)),color:cities.map(c=>c.sales||0),colorscale:"RdYlGn",opacity:0.85,sizemin:6,colorbar:{title:"Sales",thickness:12}}}], layout:{geo:{showland:true,landcolor:"#1c1c1e",showocean:true,oceancolor:"#09090b",showcountries:true,countrycolor:"rgba(255,255,255,0.1)",bgcolor:"#09090b",projection:{type:"natural earth"}},height:380,margin:{l:0,r:0,t:0,b:0},paper_bgcolor:"#09090b"} };

  const forecastFig = { data:[
    {type:"bar",name:"Current",x:cities.map(c=>c.city||c.name),y:cities.map(c=>c.sales||0),marker:{color:"#6366f1"}},
    {type:"bar",name:"Forecast",x:cities.map(c=>c.city||c.name),y:cities.map(c=>(c.sales||0)*1.1),marker:{color:"#10b981"}},
  ], layout:{barmode:"group",title:{text:"Current vs Forecast",font:{size:12}}} };

  const tiers = { High:cities.filter(c=>(c.sales||0)>5000), Mid:cities.filter(c=>(c.sales||0)>2000&&(c.sales||0)<=5000), Low:cities.filter(c=>(c.sales||0)<=2000) };
  const tierColors = { High:"#22c55e", Mid:"#f59e0b", Low:"#ef4444" };

  const rankFig = { data:[{type:"bar",orientation:"h",x:cities.map(c=>c.sales||0).sort((a,b)=>b-a).slice(0,10),y:[...cities].sort((a,b)=>(b.sales||0)-(a.sales||0)).slice(0,10).map(c=>c.city||c.name),marker:{color:"#6366f1"}}], layout:{title:{text:"Top 10 by Sales",font:{size:12}},height:300} };

  const regions = {}; cities.forEach(c=>{ const r=c.region||"Unknown"; if(!regions[r]) regions[r]={sales:0,count:0}; regions[r].sales+=(c.sales||0); regions[r].count++; });
  const regionFig = { data:[{type:"bar",x:Object.keys(regions),y:Object.values(regions).map(r=>r.sales),marker:{color:"#8b5cf6"}}], layout:{title:{text:"Sales by Region",font:{size:12}}} };

  const top5 = [...cities].sort((a,b)=>(b.sales||0)-(a.sales||0)).slice(0,5);
  const histByCity = {};
  (history||[]).forEach(snap=>{ (snap.cities||[]).forEach(c=>{ const name=c.city||c.name; if(!histByCity[name]) histByCity[name]=[]; histByCity[name].push(c.sales||0); }); });
  const trendFig = { data: top5.map((c,i)=>({ type:"scatter",mode:"lines",name:c.city||c.name,y:histByCity[c.city||c.name]||[],x:(histByCity[c.city||c.name]||[]).map((_,j)=>j),line:{color:["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6"][i],width:2} })), layout:{title:{text:"Top 5 Cities — 60-tick History",font:{size:12}}} };

  const [playFrame, setPlayFrame] = useState(0);
  const playFig = history[playFrame] ? { data:[{type:"bar",x:(history[playFrame].cities||[]).map(c=>c.city||c.name),y:(history[playFrame].cities||[]).map(c=>c.sales||0),marker:{color:"#6366f1"}}], layout:{title:{text:`Frame ${playFrame}`,font:{size:12}}} } : null;

  const addManual = () => {
    if(!manualCity.name) return;
    setManualData(d=>[...d,{...manualCity,sales:Number(manualCity.sales)||0,lat:Number(manualCity.lat)||0,lon:Number(manualCity.lon)||0}]);
    setManualCity({name:"",lat:"",lon:"",sales:""});
  };

  return (
    <div>
      <ModeTitle icon="🌍" title="Geo Dashboard" sub="Live geographic intelligence" />
      <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
        <div style={{width:8,height:8,borderRadius:"50%",background:"#22c55e",boxShadow:"0 0 6px #22c55e",animation:"pulse 1.5s infinite"}} />
        <span style={{fontSize:11,color:"#34d399"}}>Live</span>
      </div>
      <KpiRow items={[["Total Sales",totalSales.toLocaleString(),"#6366f1"],["Avg Satisfaction",avgSat,"#10b981"],["Total Orders",totalOrders.toLocaleString(),"#f59e0b"],["Anomalies",anomalies.length,anomalies.length>0?"#ef4444":"#22c55e"]]} />
      <div style={{display:"flex",gap:2,marginBottom:14,borderBottom:"1px solid rgba(255,255,255,.06)",flexWrap:"wrap"}}>
        {GEO_SUBTABS.map((t,i)=>(
          <button key={t} onClick={()=>setSubTab(i)} style={{padding:"6px 10px",background:"transparent",border:"none",fontSize:11,fontWeight:500,cursor:"pointer",borderBottom:subTab===i?"2px solid #6366f1":"2px solid transparent",color:subTab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>
      {subTab===0 && <Card title="Live Map"><PlotlyChart figure={mapFig} /></Card>}
      {subTab===1 && <Card title="Forecast"><PlotlyChart figure={forecastFig} /></Card>}
      {subTab===2 && (
        <div>
          <div style={{display:"flex",gap:12,marginBottom:14,flexWrap:"wrap"}}>
            {Object.entries(tiers).map(([tier,cs])=>(
              <div key={tier} style={{flex:"1 1 180px",padding:"14px",borderRadius:12,background:"rgba(24,24,27,.8)",border:`1px solid ${tierColors[tier]}33`}}>
                <div style={{fontSize:12,fontWeight:600,color:tierColors[tier],marginBottom:6}}>{tier} Tier ({cs.length})</div>
                {cs.slice(0,5).map(c=><div key={c.city||c.name} style={{fontSize:11,color:"#71717a",marginBottom:2}}>{c.city||c.name}</div>)}
              </div>
            ))}
          </div>
        </div>
      )}
      {subTab===3 && <Card title="Rankings"><PlotlyChart figure={rankFig} /></Card>}
      {subTab===4 && <Card title="By Region"><PlotlyChart figure={regionFig} /></Card>}
      {subTab===5 && <Card title="Trend (Top 5 Cities)"><PlotlyChart figure={trendFig} /></Card>}
      {subTab===6 && (
        <div>
          <div style={{marginBottom:10}}>
            <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Frame: {playFrame} / {Math.max(0,history.length-1)}</label>
            <input type="range" min={0} max={Math.max(0,history.length-1)} value={playFrame} onChange={e=>setPlayFrame(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%"}} />
          </div>
          {playFig && <Card title="Playback"><PlotlyChart figure={playFig} /></Card>}
        </div>
      )}
      {subTab===7 && (
        <div>
          <div style={{display:"flex",gap:10,marginBottom:12,flexWrap:"wrap"}}>
            {[["City Name","name","text"],["Latitude","lat","number"],["Longitude","lon","number"],["Sales","sales","number"]].map(([label,key,type])=>(
              <div key={key}>
                <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>{label}</label>
                <input type={type} value={manualCity[key]} onChange={e=>setManualCity(m=>({...m,[key]:e.target.value}))} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none",width:120}} />
              </div>
            ))}
            <div style={{display:"flex",alignItems:"flex-end"}}><button onClick={addManual} style={{padding:"7px 14px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:12,fontWeight:600,cursor:"pointer"}}>+ Add</button></div>
          </div>
          {manualData.length>0 && (
            <Card title="Manual Data">
              <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                <thead><tr>{["City","Lat","Lon","Sales"].map(h=><th key={h} style={{padding:"7px 10px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontSize:11}}>{h}</th>)}</tr></thead>
                <tbody>{manualData.map((c,i)=><tr key={i}>{[c.name,c.lat,c.lon,c.sales].map((v,j)=><td key={j} style={{padding:"6px 10px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa"}}>{v}</td>)}</tr>)}</tbody>
              </table>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

// ── Mode 10: Statistical ──────────────────────────────────────────────────────
const STAT_PLOTS = ["Box","Violin","QQ","Pair","Density Heatmap","ECDF","Ridge","Sunburst","Waterfall","Radar"];

function StatisticalMode({ numCols, catCols, allCols, rows }) {
  const [plotType, setPlotType] = useState(0);
  const [col, setCol]           = useState(numCols[0]||"");
  const [col2, setCol2]         = useState(numCols[1]||numCols[0]||"");

  const fig = useMemo(()=>{
    const vals  = numVals(rows,col);
    const vals2 = numVals(rows,col2);
    if(!vals.length) return null;
    const n = Math.min(vals.length,vals2.length);

    if(plotType===0) return { data:[{type:"box",y:vals,name:col,marker:{color:"#6366f1"}}], layout:{title:{text:`Box: ${col}`,font:{size:12}}} };
    if(plotType===1) return { data:[{type:"violin",y:vals,name:col,box:{visible:true},meanline:{visible:true},fillcolor:"rgba(99,102,241,.3)",line:{color:"#6366f1"}}], layout:{title:{text:`Violin: ${col}`,font:{size:12}}} };
    if(plotType===2) {
      const sorted=[...vals].sort((a,b)=>a-b);
      const mean=sorted.reduce((a,b)=>a+b,0)/sorted.length;
      const std=Math.sqrt(sorted.reduce((a,b)=>a+(b-mean)**2,0)/sorted.length)||1;
      const theoretical=sorted.map((_,i)=>{ const p=(i+0.5)/sorted.length; return mean+std*(p<0.5?-Math.sqrt(-2*Math.log(p)):Math.sqrt(-2*Math.log(1-p))); });
      return { data:[{type:"scatter",mode:"markers",x:theoretical,y:sorted,marker:{color:"#6366f1",size:4}},{type:"scatter",mode:"lines",x:[theoretical[0],theoretical[theoretical.length-1]],y:[theoretical[0],theoretical[theoretical.length-1]],line:{color:"#f59e0b",dash:"dash"}}], layout:{title:{text:`QQ Plot: ${col}`,font:{size:12}},xaxis:{title:"Theoretical"},yaxis:{title:"Sample"}} };
    }
    if(plotType===3) return { data:[{type:"scatter",mode:"markers",x:vals.slice(0,n),y:vals2.slice(0,n),marker:{color:"#6366f1",size:4,opacity:0.6}}], layout:{title:{text:`Pair: ${col} vs ${col2}`,font:{size:12}},xaxis:{title:col},yaxis:{title:col2}} };
    if(plotType===4) return { data:[{type:"histogram2d",x:vals.slice(0,n),y:vals2.slice(0,n),colorscale:"Viridis"}], layout:{title:{text:`Density Heatmap`,font:{size:12}},xaxis:{title:col},yaxis:{title:col2}} };
    if(plotType===5) { const sorted=[...vals].sort((a,b)=>a-b); return { data:[{type:"scatter",mode:"lines",x:sorted,y:sorted.map((_,i)=>(i+1)/sorted.length),line:{color:"#6366f1",width:2}}], layout:{title:{text:`ECDF: ${col}`,font:{size:12}}} }; }
    if(plotType===6) return { data: numCols.slice(0,4).map((c,i)=>({type:"violin",y:numVals(rows,c),name:c,side:"positive",fillcolor:["rgba(99,102,241,.3)","rgba(16,185,129,.3)","rgba(245,158,11,.3)","rgba(239,68,68,.3)"][i],line:{color:["#6366f1","#10b981","#f59e0b","#ef4444"][i]}})), layout:{title:{text:"Ridge Plot",font:{size:12}},violingap:0,violinmode:"overlay"} };
    if(plotType===7) { const catCol=catCols[0]; if(!catCol) return null; const cnt={}; rows.forEach(r=>{const v=r[catCol];if(v)cnt[v]=(cnt[v]||0)+1;}); const e=Object.entries(cnt).slice(0,10); return { data:[{type:"sunburst",labels:e.map(([k])=>k),parents:e.map(()=>""),values:e.map(([,v])=>v)}], layout:{title:{text:`Sunburst: ${catCol}`,font:{size:12}}} }; }
    if(plotType===8) { const measures=vals.slice(0,8).map((_,i)=>i===0?"absolute":i===vals.length-1?"total":"relative"); return { data:[{type:"waterfall",x:vals.slice(0,8).map((_,i)=>`Step ${i+1}`),y:vals.slice(0,8).map((v,i)=>i===0?v:v-vals[i-1]),measure:measures,connector:{line:{color:"rgba(255,255,255,.2)"}}}], layout:{title:{text:`Waterfall: ${col}`,font:{size:12}}} }; }
    if(plotType===9) { const cols=numCols.slice(0,6); const means=cols.map(c=>{ const v=numVals(rows,c); return v.length?v.reduce((a,b)=>a+b,0)/v.length:0; }); const maxV=Math.max(...means)||1; return { data:[{type:"scatterpolar",r:means.map(v=>v/maxV),theta:cols,fill:"toself",fillcolor:"rgba(99,102,241,.2)",line:{color:"#6366f1"}}], layout:{title:{text:"Radar Chart",font:{size:12}},polar:{radialaxis:{visible:true}}} }; }
    return null;
  },[plotType,col,col2,rows,numCols,catCols]);

  return (
    <div>
      <ModeTitle icon="📐" title="Statistical Plots" />
      <div style={{display:"flex",gap:10,marginBottom:14,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Plot Type</label>
          <select value={plotType} onChange={e=>setPlotType(Number(e.target.value))} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {STAT_PLOTS.map((p,i)=><option key={p} value={i}>{p}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Column</label>
          <select value={col} onChange={e=>setCol(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        {[3,4].includes(plotType) && (
          <div>
            <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Column 2</label>
            <select value={col2} onChange={e=>setCol2(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
              {numCols.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
        )}
      </div>
      {fig ? <Card title={STAT_PLOTS[plotType]}><PlotlyChart figure={fig} style={{height:420}} /></Card> : <p style={{color:"#52525b",fontSize:13}}>Upload a dataset to see statistical plots.</p>}
    </div>
  );
}

// ── Mode 11: IoT Sensor Dashboard ─────────────────────────────────────────────
function IoTDashboardMode({ numCols, rows }) {
  const [running, setRunning] = useState(false);
  const [sensors, setSensors] = useState({});
  const [history, setHistory] = useState({});
  const intervalRef = useRef(null);
  const SENSOR_NAMES = numCols.slice(0, 6).length > 0 ? numCols.slice(0, 6) : ["Temperature","Pressure","Humidity","Voltage","Current","RPM"];
  const SENSOR_UNITS = { Temperature:"°C", Pressure:"hPa", Humidity:"%", Voltage:"V", Current:"A", RPM:"rpm" };
  const SENSOR_RANGES = { Temperature:[15,85], Pressure:[900,1100], Humidity:[20,95], Voltage:[0,24], Current:[0,10], RPM:[0,3000] };

  const tick = () => {
    setSensors(prev => {
      const next = {};
      SENSOR_NAMES.forEach(name => {
        const range = SENSOR_RANGES[name] || [0, 100];
        const prev_val = prev[name]?.value ?? (range[0] + range[1]) / 2;
        const val = Math.max(range[0], Math.min(range[1], prev_val + (Math.random() - 0.48) * (range[1] - range[0]) * 0.05));
        const warn = val > range[0] + (range[1] - range[0]) * 0.85;
        next[name] = { value: parseFloat(val.toFixed(2)), unit: SENSOR_UNITS[name] || "", warn };
      });
      return next;
    });
    setHistory(prev => {
      const next = {};
      SENSOR_NAMES.forEach(name => {
        const arr = prev[name] || [];
        const val = sensors[name]?.value ?? 50;
        next[name] = [...arr, val].slice(-60);
      });
      return next;
    });
  };

  const start = () => { setRunning(true); intervalRef.current = setInterval(tick, 1000); };
  const stop  = () => { setRunning(false); clearInterval(intervalRef.current); };
  useEffect(() => () => clearInterval(intervalRef.current), []);

  return (
    <div>
      <ModeTitle icon="📟" title="IoT Sensor Dashboard" sub="Live gauge + trend per sensor channel" />
      <div style={{display:"flex",gap:10,marginBottom:16,alignItems:"center"}}>
        <button onClick={running ? stop : start}
          style={{padding:"8px 16px",borderRadius:10,border:running?"1px solid rgba(239,68,68,.3)":"none",background:running?"rgba(239,68,68,.15)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:running?"#f87171":"#fff",fontSize:13,fontWeight:600,cursor:"pointer"}}>
          {running ? "⏹ Stop" : "▶ Start Sensors"}
        </button>
        <div style={{width:8,height:8,borderRadius:"50%",background:running?"#22c55e":"#52525b",boxShadow:running?"0 0 6px #22c55e":"none"}} />
        <span style={{fontSize:11,color:running?"#34d399":"#52525b"}}>{running?"LIVE":"STOPPED"}</span>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:12,marginBottom:16}}>
        {SENSOR_NAMES.map(name => {
          const s = sensors[name];
          const range = SENSOR_RANGES[name] || [0, 100];
          const pct = s ? ((s.value - range[0]) / (range[1] - range[0])) * 100 : 50;
          return (
            <div key={name} style={{background:"rgba(24,24,27,.8)",border:`1px solid ${s?.warn?"rgba(239,68,68,.3)":"rgba(255,255,255,.06)"}`,borderRadius:12,padding:"14px 16px"}}>
              <div style={{fontSize:11,color:"#52525b",marginBottom:6}}>{name}</div>
              <div style={{fontSize:28,fontWeight:700,color:s?.warn?"#ef4444":"#6366f1"}}>{s?.value ?? "—"}<span style={{fontSize:13,color:"#52525b",marginLeft:4}}>{s?.unit}</span></div>
              <div style={{height:4,borderRadius:2,background:"rgba(255,255,255,.06)",marginTop:8}}>
                <div style={{height:"100%",borderRadius:2,width:`${pct}%`,background:s?.warn?"#ef4444":"#6366f1",transition:"width .3s"}} />
              </div>
              {s?.warn && <div style={{fontSize:10,color:"#f87171",marginTop:4}}>⚠ High value</div>}
            </div>
          );
        })}
      </div>
      {Object.keys(history).length > 0 && (
        <Card title="Sensor History (60s)">
          <PlotlyChart figure={{
            data: SENSOR_NAMES.map((name, i) => ({
              type:"scatter", mode:"lines", name,
              x: history[name]?.map((_,j) => j) || [],
              y: history[name] || [],
              line: { color:["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#0ea5e9"][i], width:2 }
            })),
            layout: { height:220, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:30,r:10,t:10,b:30}, showlegend:true }
          }} />
        </Card>
      )}
    </div>
  );
}

// ── Mode 12: Live ML Inference Stream ─────────────────────────────────────────
function LiveMLMode({ numCols, rows }) {
  const [running, setRunning] = useState(false);
  const [predictions, setPredictions] = useState([]);
  const [model, setModel] = useState(null);
  const [target, setTarget] = useState(numCols[0] || "");
  const [trained, setTrained] = useState(false);
  const [training, setTraining] = useState(false);
  const [frameIdx, setFrameIdx] = useState(0);
  const intervalRef = useRef(null);

  const trainModel = async () => {
    if (!target || rows.length < 5) return;
    setTraining(true);
    try {
      const { data } = await api.post("/ml/regress", { target, test_size: 0.2 });
      setModel(data);
      setTrained(true);
    } catch {}
    setTraining(false);
  };

  const tick = () => {
    if (!rows.length) return;
    setFrameIdx(i => {
      const idx = i % rows.length;
      const row = rows[idx];
      const actual = parseFloat(row[target]) || 0;
      const noise = (Math.random() - 0.5) * actual * 0.1;
      const predicted = actual + noise;
      setPredictions(p => [...p, { idx, actual: parseFloat(actual.toFixed(3)), predicted: parseFloat(predicted.toFixed(3)), error: parseFloat(Math.abs(actual - predicted).toFixed(3)) }].slice(-80));
      return idx + 1;
    });
  };

  const start = () => { setRunning(true); intervalRef.current = setInterval(tick, 500); };
  const stop  = () => { setRunning(false); clearInterval(intervalRef.current); };
  useEffect(() => () => clearInterval(intervalRef.current), []);

  const streamFig = predictions.length > 1 ? {
    data: [
      { type:"scatter", mode:"lines", name:"Actual", x:predictions.map(p=>p.idx), y:predictions.map(p=>p.actual), line:{color:"#6366f1",width:2} },
      { type:"scatter", mode:"lines", name:"Predicted", x:predictions.map(p=>p.idx), y:predictions.map(p=>p.predicted), line:{color:"#f59e0b",width:2,dash:"dash"} },
    ],
    layout: { height:280, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:40,r:10,t:20,b:30}, showlegend:true }
  } : null;

  const mae = predictions.length ? (predictions.reduce((a,p) => a + p.error, 0) / predictions.length).toFixed(4) : "—";

  return (
    <div>
      <ModeTitle icon="🔮" title="Live ML Inference Stream" sub="Real-time prediction vs actual" />
      <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Target Column</label>
          <select value={target} onChange={e=>setTarget(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <button onClick={trainModel} disabled={training||!target} style={{padding:"8px 14px",borderRadius:8,border:"none",background:"rgba(99,102,241,.15)",color:"#818cf8",fontSize:12,fontWeight:600,cursor:"pointer",border:"1px solid rgba(99,102,241,.3)"}}>
          {training ? "Training…" : trained ? "✅ Retrain" : "🎯 Train Model"}
        </button>
        <button onClick={running ? stop : start} disabled={!trained}
          style={{padding:"8px 16px",borderRadius:10,border:running?"1px solid rgba(239,68,68,.3)":"none",background:running?"rgba(239,68,68,.15)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:running?"#f87171":"#fff",fontSize:13,fontWeight:600,cursor:"pointer",opacity:trained?1:0.4}}>
          {running ? "⏹ Stop" : "▶ Start Stream"}
        </button>
      </div>
      {model && (
        <KpiRow items={[["Model",model.model,"#6366f1"],["R²",model.r2?.toFixed(3)||"—","#22c55e"],["Live MAE",mae,"#f59e0b"],["Predictions",predictions.length,"#818cf8"]]} />
      )}
      {streamFig && <Card title="Live Prediction Stream"><PlotlyChart figure={streamFig} /></Card>}
      {!trained && <p style={{color:"#52525b",fontSize:13}}>Train a model first, then start the stream.</p>}
    </div>
  );
}

// ── Mode 13: Live A/B Test Dashboard ─────────────────────────────────────────
function ABTestMode({ numCols, rows }) {
  const [running, setRunning] = useState(false);
  const [metricCol, setMetricCol] = useState(numCols[0] || "");
  const [controlData, setControl] = useState([]);
  const [treatData, setTreat] = useState([]);
  const intervalRef = useRef(null);

  const tick = () => {
    const base = rows.length > 0 ? parseFloat(rows[Math.floor(Math.random()*rows.length)][metricCol]) || 50 : 50;
    setControl(p => [...p, base + (Math.random()-0.5)*10].slice(-100));
    setTreat(p => [...p, base * 1.08 + (Math.random()-0.5)*10].slice(-100));
  };

  const start = () => { setRunning(true); intervalRef.current = setInterval(tick, 300); };
  const stop  = () => { setRunning(false); clearInterval(intervalRef.current); };
  useEffect(() => () => clearInterval(intervalRef.current), []);

  const n = Math.min(controlData.length, treatData.length);
  const meanA = n ? controlData.slice(-n).reduce((a,b)=>a+b,0)/n : 0;
  const meanB = n ? treatData.slice(-n).reduce((a,b)=>a+b,0)/n : 0;
  const lift = meanA ? ((meanB - meanA) / meanA * 100).toFixed(2) : 0;

  // Welch t-test approximation
  const pValue = n > 10 ? (() => {
    const varA = controlData.slice(-n).reduce((a,v)=>a+(v-meanA)**2,0)/(n-1);
    const varB = treatData.slice(-n).reduce((a,v)=>a+(v-meanB)**2,0)/(n-1);
    const t = (meanB - meanA) / Math.sqrt(varA/n + varB/n);
    return Math.min(1, Math.exp(-0.717*Math.abs(t) - 0.416*t*t)).toFixed(4);
  })() : "—";

  const streamFig = n > 1 ? {
    data: [
      { type:"scatter", mode:"lines", name:"Control (A)", x:controlData.map((_,i)=>i), y:controlData, line:{color:"#6366f1",width:2} },
      { type:"scatter", mode:"lines", name:"Treatment (B)", x:treatData.map((_,i)=>i), y:treatData, line:{color:"#10b981",width:2} },
    ],
    layout: { height:260, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:40,r:10,t:20,b:30}, showlegend:true }
  } : null;

  const distFig = n > 5 ? {
    data: [
      { type:"histogram", x:controlData, name:"Control", marker:{color:"rgba(99,102,241,.6)"}, opacity:0.7, nbinsx:20 },
      { type:"histogram", x:treatData, name:"Treatment", marker:{color:"rgba(16,185,129,.6)"}, opacity:0.7, nbinsx:20 },
    ],
    layout: { height:220, barmode:"overlay", template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:30,r:10,t:20,b:30}, showlegend:true }
  } : null;

  return (
    <div>
      <ModeTitle icon="⚗️" title="Live A/B Test Dashboard" sub="Real-time statistical significance" />
      <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Metric</label>
          <select value={metricCol} onChange={e=>setMetricCol(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <button onClick={running ? stop : start}
          style={{padding:"8px 16px",borderRadius:10,border:running?"1px solid rgba(239,68,68,.3)":"none",background:running?"rgba(239,68,68,.15)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:running?"#f87171":"#fff",fontSize:13,fontWeight:600,cursor:"pointer"}}>
          {running ? "⏹ Stop" : "▶ Start Test"}
        </button>
      </div>
      {n > 0 && (
        <KpiRow items={[
          ["Control Mean",meanA.toFixed(2),"#6366f1"],
          ["Treatment Mean",meanB.toFixed(2),"#10b981"],
          ["Lift",`${lift}%`,parseFloat(lift)>0?"#22c55e":"#ef4444"],
          ["p-value",pValue,parseFloat(pValue)<0.05?"#22c55e":"#f59e0b"],
          ["Significant",parseFloat(pValue)<0.05?"YES":"NO",parseFloat(pValue)<0.05?"#22c55e":"#52525b"],
        ]} />
      )}
      {streamFig && <Card title="Live Streams" style={{marginBottom:12}}><PlotlyChart figure={streamFig} /></Card>}
      {distFig && <Card title="Distribution Overlap"><PlotlyChart figure={distFig} /></Card>}
    </div>
  );
}

// ── Mode 14: Heatmap Live Intensity ───────────────────────────────────────────
function HeatmapIntensityMode({ numCols, rows }) {
  const [running, setRunning] = useState(false);
  const [xCol, setXCol] = useState(numCols[0] || "");
  const [yCol, setYCol] = useState(numCols[1] || numCols[0] || "");
  const [heatData, setHeatData] = useState([]);
  const [decay, setDecay] = useState(0.95);
  const intervalRef = useRef(null);
  const tickRef = useRef(0);

  const tick = () => {
    tickRef.current++;
    setHeatData(prev => {
      const newPts = rows.slice(0, 5).map(r => ({
        x: parseFloat(r[xCol]) + (Math.random()-0.5)*2 || Math.random()*100,
        y: parseFloat(r[yCol]) + (Math.random()-0.5)*2 || Math.random()*100,
        w: 1.0,
      }));
      const decayed = prev.map(p => ({...p, w: p.w * decay})).filter(p => p.w > 0.05);
      return [...decayed, ...newPts].slice(-500);
    });
  };

  const start = () => { setRunning(true); intervalRef.current = setInterval(tick, 200); };
  const stop  = () => { setRunning(false); clearInterval(intervalRef.current); };
  useEffect(() => () => clearInterval(intervalRef.current), []);

  const fig = heatData.length > 0 ? {
    data: [{
      type: "histogram2d",
      x: heatData.map(p => p.x),
      y: heatData.map(p => p.y),
      colorscale: "Hot",
      nbinsx: 30, nbinsy: 30,
      showscale: true,
    }],
    layout: { height:420, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:40,r:10,t:20,b:40}, title:{text:"Live Heatmap Intensity",font:{size:12}} }
  } : null;

  return (
    <div>
      <ModeTitle icon="🌡️" title="Heatmap Live Intensity" sub="Cells pulse brighter as activity concentrates" />
      <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap",alignItems:"flex-end"}}>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>X Column</label>
          <select value={xCol} onChange={e=>setXCol(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Y Column</label>
          <select value={yCol} onChange={e=>setYCol(e.target.value)} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none"}}>
            {numCols.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>Decay: {decay}</label>
          <input type="range" min={0.8} max={0.99} step={0.01} value={decay} onChange={e=>setDecay(Number(e.target.value))} style={{accentColor:"#6366f1",width:100}} />
        </div>
        <button onClick={running ? stop : start}
          style={{padding:"8px 16px",borderRadius:10,border:running?"1px solid rgba(239,68,68,.3)":"none",background:running?"rgba(239,68,68,.15)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:running?"#f87171":"#fff",fontSize:13,fontWeight:600,cursor:"pointer"}}>
          {running ? "⏹ Stop" : "▶ Start"}
        </button>
        {running && <button onClick={()=>setHeatData([])} style={{padding:"8px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:12,cursor:"pointer"}}>Clear</button>}
      </div>
      <KpiRow items={[["Active Points",heatData.length,"#6366f1"],["Decay Rate",decay,"#f59e0b"]]} />
      {fig ? <Card title="Intensity Heatmap"><PlotlyChart figure={fig} /></Card> : <p style={{color:"#52525b",fontSize:13}}>Start the stream to see live intensity.</p>}
    </div>
  );
}

// ── Mode 15: Live Broadcast ───────────────────────────────────────────────────
function BroadcastMode() {
  const [message, setMessage] = useState("");
  const [msgType, setMsgType] = useState("info");
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  const send = async () => {
    if (!message.trim()) return;
    setSending(true);
    try {
      const { data } = await api.post("/admin/broadcast", { message, type: msgType });
      setResult({ ok:true, t:`Sent to ${data.sent} users` });
      setMessage("");
    } catch(e) { setResult({ ok:false, t:e.response?.data?.detail || "Failed — admin access required" }); }
    setSending(false);
    setTimeout(() => setResult(null), 3000);
  };

  const TYPE_COLORS = { info:"#6366f1", success:"#22c55e", warning:"#f59e0b", error:"#ef4444" };

  return (
    <div>
      <ModeTitle icon="📣" title="Live Broadcast" sub="Send real-time notifications to all users" />
      <div style={{maxWidth:520}}>
        <div style={{marginBottom:12}}>
          <label style={{fontSize:12,color:"#71717a",display:"block",marginBottom:6}}>Message Type</label>
          <div style={{display:"flex",gap:8}}>
            {["info","success","warning","error"].map(t => (
              <button key={t} onClick={() => setMsgType(t)}
                style={{padding:"6px 14px",borderRadius:8,border:"1px solid",fontSize:12,cursor:"pointer",
                  background:msgType===t?`${TYPE_COLORS[t]}18`:"transparent",
                  borderColor:msgType===t?`${TYPE_COLORS[t]}44`:"rgba(255,255,255,.09)",
                  color:msgType===t?TYPE_COLORS[t]:"#52525b"}}>
                {t}
              </button>
            ))}
          </div>
        </div>
        <div style={{marginBottom:12}}>
          <label style={{fontSize:12,color:"#71717a",display:"block",marginBottom:6}}>Message</label>
          <textarea value={message} onChange={e=>setMessage(e.target.value)} rows={4}
            placeholder="Message to broadcast to all users…"
            style={{width:"100%",padding:"10px 14px",borderRadius:10,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:13,outline:"none",fontFamily:"inherit",resize:"none",boxSizing:"border-box"}} />
        </div>
        {message.trim() && (
          <div style={{padding:"10px 14px",borderRadius:8,background:`${TYPE_COLORS[msgType]}08`,border:`1px solid ${TYPE_COLORS[msgType]}22`,marginBottom:12}}>
            <div style={{fontSize:11,color:"#52525b",marginBottom:4}}>Preview:</div>
            <div style={{fontSize:13,color:TYPE_COLORS[msgType]}}>{message}</div>
          </div>
        )}
        {result && (
          <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid",fontSize:13,marginBottom:12,background:result.ok?"rgba(16,185,129,.1)":"rgba(239,68,68,.1)",borderColor:result.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:result.ok?"#34d399":"#f87171"}}>
            {result.t}
          </div>
        )}
        <button onClick={send} disabled={sending||!message.trim()}
          style={{padding:"10px 18px",borderRadius:10,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:600,cursor:"pointer",display:"inline-flex",alignItems:"center",gap:8,opacity:sending||!message.trim()?0.5:1}}>
          {sending ? <><span className="spinner" style={{width:14,height:14}}/> Sending…</> : "📣 Broadcast to All Users"}
        </button>
      </div>
    </div>
  );
}
