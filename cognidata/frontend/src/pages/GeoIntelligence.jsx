import { useEffect, useRef, useState, Component } from "react";
import { api } from "../api/client";
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

const TABS = ["🗺️ Live Map","🔮 Forecast","🧬 Segments","🏆 Rankings","📊 By Region","📈 Trend","⏪ Playback","🔌 Real Data"];

export default function GeoIntelligence() {
  const [tab, setTab]         = useState(0);
  const [current, setCurrent] = useState(null);
  const [history, setHistory] = useState([]);
  const intervalRef           = useRef(null);

  const fetchData = async () => {
    try {
      const [c,h] = await Promise.all([api.get("/geo/current"), api.get("/geo/history?n=60")]);
      setCurrent(c.data); setHistory(h.data||[]);
    } catch {}
  };

  useEffect(()=>{
    fetchData();
    // Only poll when tab is visible, 10s interval instead of 3s
    const onVisible = () => {
      if (!document.hidden) {
        fetchData();
        intervalRef.current = setInterval(fetchData, 10000);
      } else {
        clearInterval(intervalRef.current);
      }
    };
    intervalRef.current = setInterval(fetchData, 10000);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      clearInterval(intervalRef.current);
      document.removeEventListener("visibilitychange", onVisible);
    };
  },[]);

  const cities    = current?.cities||[];
  const anomalies = cities.filter(c=>c.anomaly);
  const totalSales= cities.reduce((a,c)=>a+(c.sales||0),0);
  const avgSat    = cities.length?(cities.reduce((a,c)=>a+(c.satisfaction||0),0)/cities.length).toFixed(2):0;
  const totalOrders=cities.reduce((a,c)=>a+(c.orders||0),0);

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={{display:"flex",alignItems:"center",gap:12}}>
          <div style={S.icon}>🌍</div>
          <div>
            <div style={S.title}>Geo Intelligence</div>
            <div style={S.sub}>{cities.length} cities · live data</div>
          </div>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <div style={{width:8,height:8,borderRadius:"50%",background:"#22c55e",boxShadow:"0 0 6px #22c55e"}} />
          <span style={{fontSize:11,color:"#34d399",fontWeight:600}}>LIVE</span>
        </div>
      </div>

      {/* KPI Row */}
      <div style={{display:"flex",gap:10,marginBottom:16,flexWrap:"wrap"}}>
        {[["Total Sales",totalSales.toLocaleString(),"#6366f1"],["Avg Satisfaction",avgSat,"#10b981"],["Total Orders",totalOrders.toLocaleString(),"#f59e0b"],["Anomalies",anomalies.length,anomalies.length>0?"#ef4444":"#22c55e"]].map(([l,v,c])=>(
          <div key={l} style={{flex:"1 1 140px",background:"rgba(24,24,27,.8)",border:`1px solid ${c}22`,borderRadius:12,padding:"14px 18px"}}>
            <div style={{fontSize:22,fontWeight:700,color:c}}>{v}</div>
            <div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div>
          </div>
        ))}
      </div>

      <div style={S.tabs}>
        {TABS.map((t,i)=>(
          <button key={t} onClick={()=>setTab(i)} style={{...S.tab,borderBottom:tab===i?"2px solid #6366f1":"2px solid transparent",color:tab===i?"#818cf8":"#52525b"}}>{t}</button>
        ))}
      </div>

      {tab===0 && <LiveMapTab cities={cities} anomalies={anomalies} />}
      {tab===1 && <ForecastTab cities={cities} />}
      {tab===2 && <SegmentsTab cities={cities} />}
      {tab===3 && <RankingsTab cities={cities} />}
      {tab===4 && <ByRegionTab cities={cities} />}
      {tab===5 && <TrendTab history={history} cities={cities} />}
      {tab===6 && <PlaybackTab history={history} />}
      {tab===7 && <RealDataTab />}
    </div>
    </ErrorBoundary>
  );
}

function LiveMapTab({ cities, anomalies }) {
  const mapFig = {
    data:[{
      type:"scattermapbox",
      lat:cities.map(c=>c.lat||0),
      lon:cities.map(c=>c.lon||0),
      text:cities.map(c=>`<b>${c.city||c.name}</b><br>Sales: ${c.sales}<br>Satisfaction: ${c.satisfaction}<br>Orders: ${c.orders}`),
      mode:"markers",
      marker:{
        size:cities.map(c=>Math.max(8,(c.sales||100)/500)),
        color:cities.map(c=>c.sales||0),
        colorscale:"RdYlGn",
        opacity:0.85,
        sizemin:6,
        colorbar:{title:"Sales",thickness:12},
      },
      hoverinfo:"text",
    },
    anomalies.length>0 && {
      type:"scattermapbox",
      lat:anomalies.map(c=>c.lat||0),
      lon:anomalies.map(c=>c.lon||0),
      text:anomalies.map(c=>`⚠️ ANOMALY: ${c.city||c.name}`),
      mode:"markers",
      marker:{ size:16, color:"#ef4444", opacity:1, symbol:"circle" },
      name:"Anomalies",
    }].filter(Boolean),
    layout:{
      mapbox:{ style:"carto-darkmatter", zoom:1, center:{lat:20,lon:0} },
      height:420,
      margin:{l:0,r:0,t:0,b:0},
      showlegend:false,
    }
  };

  return (
    <div>
      <Card title="Live Geographic Map">
        <PlotlyChart figure={mapFig} style={{height:420}} />
      </Card>
      {anomalies.length>0 && (
        <div style={{marginTop:12,padding:"10px 14px",borderRadius:10,background:"rgba(239,68,68,.06)",border:"1px solid rgba(239,68,68,.2)"}}>
          <div style={{fontSize:12,fontWeight:600,color:"#f87171",marginBottom:6}}>⚠️ Anomaly Cities</div>
          <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
            {anomalies.map(c=>(
              <span key={c.city||c.name} style={{padding:"3px 10px",borderRadius:20,background:"rgba(239,68,68,.12)",color:"#f87171",fontSize:11}}>{c.city||c.name}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ForecastTab({ cities }) {
  const sorted = [...cities].sort((a,b)=>(b.sales||0)-(a.sales||0)).slice(0,15);
  const forecastFig = {
    data:[
      { type:"bar", name:"Current Sales", x:sorted.map(c=>c.city||c.name), y:sorted.map(c=>c.sales||0), marker:{color:"#6366f1"} },
      { type:"bar", name:"Forecast (+10%)", x:sorted.map(c=>c.city||c.name), y:sorted.map(c=>Math.round((c.sales||0)*1.1)), marker:{color:"#10b981"} },
    ],
    layout:{ barmode:"group", title:{text:"Current vs Forecast Sales",font:{size:12}} }
  };

  const totalCurrent  = cities.reduce((a,c)=>a+(c.sales||0),0);
  const totalForecast = Math.round(totalCurrent*1.1);
  const topCity       = sorted[0];
  const avgSales      = cities.length?(totalCurrent/cities.length).toFixed(0):0;

  return (
    <div>
      <div style={{display:"flex",gap:10,marginBottom:14,flexWrap:"wrap"}}>
        {[["Total Current",totalCurrent.toLocaleString(),"#6366f1"],["Total Forecast",totalForecast.toLocaleString(),"#10b981"],["Top City",topCity?.city||topCity?.name||"—","#f59e0b"],["Avg Sales",avgSales,"#818cf8"]].map(([l,v,c])=>(
          <div key={l} style={{flex:"1 1 140px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12,padding:"14px 18px"}}>
            <div style={{fontSize:18,fontWeight:700,color:c,wordBreak:"break-all"}}>{v}</div>
            <div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div>
          </div>
        ))}
      </div>
      <Card title="Forecast Chart"><PlotlyChart figure={forecastFig} /></Card>
    </div>
  );
}

function SegmentsTab({ cities }) {
  const tiers = {
    High: cities.filter(c=>(c.sales||0)>5000),
    Mid:  cities.filter(c=>(c.sales||0)>2000&&(c.sales||0)<=5000),
    Low:  cities.filter(c=>(c.sales||0)<=2000),
  };
  const tierColors = { High:"#22c55e", Mid:"#f59e0b", Low:"#ef4444" };

  const scatterFig = {
    data: Object.entries(tiers).map(([tier,cs])=>({
      type:"scatter", mode:"markers",
      x:cs.map(c=>c.sales||0), y:cs.map(c=>c.satisfaction||0),
      text:cs.map(c=>c.city||c.name),
      marker:{ color:tierColors[tier], size:10, opacity:0.8 },
      name:tier,
    })),
    layout:{ title:{text:"Segments Scatter",font:{size:12}}, xaxis:{title:"Sales"}, yaxis:{title:"Satisfaction"} }
  };

  const pieFig = {
    data:[{ type:"pie", labels:Object.keys(tiers), values:Object.values(tiers).map(cs=>cs.length), marker:{colors:Object.values(tierColors)} }],
    layout:{ title:{text:"Tier Distribution",font:{size:12}} }
  };

  return (
    <div>
      <div style={{display:"flex",gap:12,marginBottom:14,flexWrap:"wrap"}}>
        {Object.entries(tiers).map(([tier,cs])=>(
          <div key={tier} style={{flex:"1 1 200px",padding:"16px",borderRadius:12,background:"rgba(24,24,27,.8)",border:`1px solid ${tierColors[tier]}33`}}>
            <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:10}}>
              <div style={{width:10,height:10,borderRadius:"50%",background:tierColors[tier]}} />
              <span style={{fontSize:13,fontWeight:600,color:tierColors[tier]}}>{tier} Tier</span>
              <span style={{fontSize:11,color:"#52525b",marginLeft:"auto"}}>{cs.length} cities</span>
            </div>
            <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
              {cs.slice(0,8).map(c=>(
                <span key={c.city||c.name} style={{padding:"2px 8px",borderRadius:20,background:`${tierColors[tier]}18`,color:tierColors[tier],fontSize:10}}>{c.city||c.name}</span>
              ))}
              {cs.length>8 && <span style={{fontSize:10,color:"#52525b"}}>+{cs.length-8} more</span>}
            </div>
          </div>
        ))}
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
        <Card title="Segment Scatter"><PlotlyChart figure={scatterFig} /></Card>
        <Card title="Tier Distribution"><PlotlyChart figure={pieFig} /></Card>
      </div>
    </div>
  );
}

function RankingsTab({ cities }) {
  const sorted = [...cities].sort((a,b)=>(b.sales||0)-(a.sales||0)).slice(0,15);

  const barFig = {
    data:[{ type:"bar", orientation:"h", x:sorted.map(c=>c.sales||0).reverse(), y:sorted.map(c=>c.city||c.name).reverse(), marker:{color:sorted.map((_,i)=>i===0?"#f59e0b":i<3?"#6366f1":"rgba(99,102,241,.5)").reverse()} }],
    layout:{ title:{text:"Top Cities by Sales",font:{size:12}}, xaxis:{title:"Sales"}, height:Math.max(300,sorted.length*28) }
  };

  const satFig = {
    data:[{ type:"scatter", mode:"markers+text", x:sorted.map(c=>c.sales||0), y:sorted.map(c=>c.satisfaction||0), text:sorted.map(c=>c.city||c.name), textposition:"top center", marker:{color:"#10b981",size:10,opacity:0.8} }],
    layout:{ title:{text:"Sales vs Satisfaction",font:{size:12}}, xaxis:{title:"Sales"}, yaxis:{title:"Satisfaction"} }
  };

  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
      <Card title="Rankings"><PlotlyChart figure={barFig} /></Card>
      <Card title="Sales vs Satisfaction"><PlotlyChart figure={satFig} /></Card>
    </div>
  );
}

function ByRegionTab({ cities }) {
  const regions = {};
  cities.forEach(c=>{ const r=c.region||"Unknown"; if(!regions[r]) regions[r]={sales:0,orders:0,count:0}; regions[r].sales+=(c.sales||0); regions[r].orders+=(c.orders||0); regions[r].count++; });
  const entries = Object.entries(regions).sort((a,b)=>b[1].sales-a[1].sales);

  const barFig = {
    data:[{ type:"bar", x:entries.map(([k])=>k), y:entries.map(([,v])=>v.sales), marker:{color:"#8b5cf6"} }],
    layout:{ title:{text:"Sales by Region",font:{size:12}} }
  };

  const donutFig = {
    data:[{ type:"pie", labels:entries.map(([k])=>k), values:entries.map(([,v])=>v.sales), hole:0.4, marker:{colorscale:"Viridis"} }],
    layout:{ title:{text:"Region Share",font:{size:12}} }
  };

  return (
    <div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14}}>
        <Card title="Bar Chart"><PlotlyChart figure={barFig} /></Card>
        <Card title="Donut Chart"><PlotlyChart figure={donutFig} /></Card>
      </div>
      <Card title="Aggregation Table">
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
          <thead><tr>{["Region","Cities","Total Sales","Total Orders","Avg Sales"].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
          <tbody>{entries.map(([r,v])=>(
            <tr key={r}>
              <td style={S.td}>{r}</td>
              <td style={S.td}>{v.count}</td>
              <td style={S.td}>{v.sales.toLocaleString()}</td>
              <td style={S.td}>{v.orders.toLocaleString()}</td>
              <td style={S.td}>{v.count?(v.sales/v.count).toFixed(0):0}</td>
            </tr>
          ))}</tbody>
        </table>
      </Card>
    </div>
  );
}

function TrendTab({ history, cities }) {
  const top5 = [...cities].sort((a,b)=>(b.sales||0)-(a.sales||0)).slice(0,5);
  const histByCity = {};
  history.forEach(snap=>{
    (snap.cities||[]).forEach(c=>{ const name=c.city||c.name; if(!histByCity[name]) histByCity[name]=[]; histByCity[name].push(c.sales||0); });
  });

  const trendFig = {
    data: top5.map((c,i)=>{
      const name = c.city||c.name;
      const vals = histByCity[name]||[];
      return { type:"scatter", mode:"lines", name, x:vals.map((_,j)=>j), y:vals, line:{color:["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6"][i],width:2} };
    }),
    layout:{ title:{text:"Top 5 Cities — Sales History (60 ticks)",font:{size:12}}, xaxis:{title:"Tick"}, yaxis:{title:"Sales"} }
  };

  return (
    <div>
      <Card title="Multi-City Trend"><PlotlyChart figure={trendFig} style={{height:400}} /></Card>
      <div style={{display:"flex",gap:8,marginTop:12,flexWrap:"wrap"}}>
        {top5.map((c,i)=>{
          const name=c.city||c.name;
          const vals=histByCity[name]||[];
          const last=vals[vals.length-1]||0, first=vals[0]||0;
          const change=first?((last-first)/Math.abs(first)*100).toFixed(1):0;
          return (
            <div key={name} style={{flex:"1 1 140px",padding:"12px 14px",borderRadius:10,background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)"}}>
              <div style={{fontSize:12,fontWeight:600,color:["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6"][i]}}>{name}</div>
              <div style={{fontSize:11,color:"#52525b",marginTop:2}}>{change>0?"+":""}{change}% change</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PlaybackTab({ history }) {
  const [frame, setFrame]   = useState(0);
  const [playing, setPlay]  = useState(false);
  const intervalRef         = useRef(null);

  const maxFrame = Math.max(0, history.length-1);

  const play = () => {
    setPlay(true);
    intervalRef.current = setInterval(()=>{
      setFrame(f=>{ if(f>=maxFrame){ clearInterval(intervalRef.current); setPlay(false); return f; } return f+1; });
    }, 500);
  };
  const pause = () => { setPlay(false); clearInterval(intervalRef.current); };
  useEffect(()=>()=>clearInterval(intervalRef.current),[]);

  const snap = history[frame];
  const snapCities = snap?.cities||[];

  const barFig = snapCities.length ? {
    data:[{ type:"bar", x:snapCities.map(c=>c.city||c.name), y:snapCities.map(c=>c.sales||0), marker:{color:snapCities.map(c=>c.sales||0),colorscale:"Viridis"} }],
    layout:{ title:{text:`Frame ${frame} — Sales`,font:{size:12}} }
  } : null;

  const lineFig = snapCities.length ? {
    data:[{ type:"scatter", mode:"lines+markers", x:snapCities.map(c=>c.city||c.name), y:snapCities.map(c=>c.sales||0), line:{color:"#6366f1",width:2}, marker:{size:6} }],
    layout:{ title:{text:`Frame ${frame} — Trend`,font:{size:12}} }
  } : null;

  return (
    <div>
      <div style={{marginBottom:12}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
          <label style={{fontSize:12,color:"#71717a"}}>Frame: {frame} / {maxFrame}</label>
          <span style={{fontSize:11,color:"#52525b"}}>{snap?.ts?new Date(snap.ts).toLocaleTimeString():""}</span>
        </div>
        <input type="range" min={0} max={maxFrame} value={frame} onChange={e=>setFrame(Number(e.target.value))} style={{accentColor:"#6366f1",width:"100%"}} />
      </div>
      <div style={{display:"flex",gap:8,marginBottom:14}}>
        <button onClick={playing?pause:play} style={{padding:"7px 14px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:12,fontWeight:600,cursor:"pointer"}}>{playing?"⏸ Pause":"▶ Auto-Play"}</button>
        <button onClick={()=>{pause();setFrame(0);}} style={{padding:"7px 14px",borderRadius:8,border:"1px solid rgba(255,255,255,.09)",background:"transparent",color:"#71717a",fontSize:12,cursor:"pointer"}}>↺ Reset</button>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
        {barFig  && <Card title="Sales Bar"><PlotlyChart figure={barFig} /></Card>}
        {lineFig && <Card title="Sales Line"><PlotlyChart figure={lineFig} /></Card>}
      </div>
      {!history.length && <p style={{color:"#52525b",fontSize:13}}>No history data available yet.</p>}
    </div>
  );
}

function RealDataTab() {
  const [city, setCity]     = useState({name:"",lat:"",lon:"",sales:""});
  const [data, setData]     = useState([]);
  const [syncing, setSyncing]= useState(false);
  const [msg, setMsg]       = useState(null);

  const addCity = () => {
    if(!city.name) return;
    setData(d=>[...d,{...city,sales:Number(city.sales)||0,lat:Number(city.lat)||0,lon:Number(city.lon)||0}]);
    setCity({name:"",lat:"",lon:"",sales:""});
  };

  const syncDataset = async () => {
    setSyncing(true);
    try {
      await api.post("/geo/sync", { cities:data });
      setMsg({ok:true,t:"Dataset synced to geo engine"});
    } catch(e){ setMsg({ok:false,t:e.response?.data?.detail||"Sync failed"}); }
    finally { setSyncing(false); }
  };

  const handleCSV = (e) => {
    const file = e.target.files[0]; if(!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      const lines = ev.target.result.split("\n").filter(Boolean);
      const headers = lines[0].split(",").map(h=>h.trim().toLowerCase());
      const rows = lines.slice(1).map(line=>{ const vals=line.split(","); const obj={}; headers.forEach((h,i)=>obj[h]=vals[i]?.trim()); return obj; });
      const parsed = rows.map(r=>({ name:r.name||r.city||"", lat:Number(r.lat||r.latitude||0), lon:Number(r.lon||r.longitude||0), sales:Number(r.sales||0) })).filter(r=>r.name);
      setData(d=>[...d,...parsed]);
    };
    reader.readAsText(file);
  };

  return (
    <div>
      {msg && <div style={{padding:"9px 13px",borderRadius:8,border:"1px solid",fontSize:13,marginBottom:12,background:msg.ok?"rgba(16,185,129,.08)":"rgba(239,68,68,.08)",borderColor:msg.ok?"rgba(16,185,129,.3)":"rgba(239,68,68,.3)",color:msg.ok?"#34d399":"#f87171"}}>{msg.t}</div>}
      <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"16px",marginBottom:14}}>
        <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:12}}>Manual Entry</div>
        <div style={{display:"flex",gap:10,flexWrap:"wrap",marginBottom:10}}>
          {[["City Name","name","text"],["Latitude","lat","number"],["Longitude","lon","number"],["Sales","sales","number"]].map(([label,key,type])=>(
            <div key={key}>
              <label style={{fontSize:11,color:"#71717a",display:"block",marginBottom:3}}>{label}</label>
              <input type={type} value={city[key]} onChange={e=>setCity(c=>({...c,[key]:e.target.value}))} style={{padding:"7px 10px",borderRadius:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.09)",color:"#f4f4f5",fontSize:12,outline:"none",width:130}} />
            </div>
          ))}
          <div style={{display:"flex",alignItems:"flex-end"}}>
            <button onClick={addCity} style={{padding:"7px 14px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:12,fontWeight:600,cursor:"pointer"}}>+ Add City</button>
          </div>
        </div>
        <div style={{display:"flex",gap:8,alignItems:"center"}}>
          <label style={{padding:"7px 14px",borderRadius:8,border:"1px solid rgba(99,102,241,.3)",background:"transparent",color:"#818cf8",fontSize:12,cursor:"pointer"}}>
            📂 Upload CSV<input type="file" accept=".csv" onChange={handleCSV} style={{display:"none"}} />
          </label>
          <span style={{fontSize:11,color:"#52525b"}}>CSV format: name,lat,lon,sales</span>
        </div>
      </div>

      {data.length>0 && (
        <div>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
            <span style={{fontSize:12,color:"#71717a"}}>{data.length} cities loaded</span>
            <div style={{display:"flex",gap:8}}>
              <button onClick={syncDataset} disabled={syncing} style={{padding:"7px 14px",borderRadius:8,border:"none",background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:12,fontWeight:600,cursor:"pointer"}}>{syncing?"Syncing…":"🔄 Sync Dataset"}</button>
              <button onClick={()=>setData([])} style={{padding:"7px 14px",borderRadius:8,border:"1px solid rgba(239,68,68,.3)",background:"transparent",color:"#f87171",fontSize:12,cursor:"pointer"}}>Clear</button>
            </div>
          </div>
          <div style={{overflowX:"auto",borderRadius:10,border:"1px solid rgba(255,255,255,.06)"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr>{["City","Lat","Lon","Sales"].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
              <tbody>{data.map((c,i)=>(
                <tr key={i}>
                  <td style={S.td}>{c.name}</td>
                  <td style={S.td}>{c.lat}</td>
                  <td style={S.td}>{c.lon}</td>
                  <td style={S.td}>{c.sales.toLocaleString()}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Shared ────────────────────────────────────────────────────────────────────
function Card({title,children,style={}}){
  return <div style={{background:"rgba(24,24,27,.8)",border:"1px solid rgba(255,255,255,.06)",borderRadius:14,padding:"14px 12px 8px",overflow:"hidden",...style}}>{title&&<div style={{fontSize:11,fontWeight:600,color:"#3f3f46",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:6,paddingLeft:4}}>{title}</div>}{children}</div>;
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  td:     { padding:"8px 12px", borderTop:"1px solid rgba(255,255,255,.04)", color:"#a1a1aa" },
};
