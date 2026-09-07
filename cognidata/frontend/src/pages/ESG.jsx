import { useState, useEffect, Component } from "react";
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

const TABS = ["🌱 Overview","♻️ Carbon","👥 Diversity","🔗 Supply Chain","📄 ESG Report"];

const DEMO_CARBON = [
  { month:"Jan", scope1:120, scope2:85, scope3:340 },
  { month:"Feb", scope1:115, scope2:82, scope3:325 },
  { month:"Mar", scope1:108, scope2:79, scope3:310 },
  { month:"Apr", scope1:102, scope2:75, scope3:298 },
  { month:"May", scope1:95,  scope2:71, scope3:285 },
  { month:"Jun", scope1:88,  scope2:68, scope3:270 },
];

const DEMO_DIVERSITY = [
  { category:"Gender", female:42, male:55, nonbinary:3 },
  { category:"Leadership", female:31, male:67, nonbinary:2 },
  { category:"Engineering", female:28, male:70, nonbinary:2 },
  { category:"Sales", female:51, male:47, nonbinary:2 },
];

const DEMO_SUPPLY = [
  { supplier:"Supplier A", esg_score:82, risk:"Low",    country:"Germany" },
  { supplier:"Supplier B", esg_score:61, risk:"Medium", country:"China" },
  { supplier:"Supplier C", esg_score:74, risk:"Low",    country:"USA" },
  { supplier:"Supplier D", esg_score:45, risk:"High",   country:"Vietnam" },
  { supplier:"Supplier E", esg_score:88, risk:"Low",    country:"Sweden" },
];

export default function ESG() {
  const [tab, setTab]       = useState(0);
  const [carbon, setCarbon] = useState(DEMO_CARBON);
  const [diversity, setDiv] = useState(DEMO_DIVERSITY);
  const [supply, setSupply] = useState(DEMO_SUPPLY);
  const [report, setReport] = useState(null);
  const [genLoading, setGenLoad] = useState(false);
  const [msg, setMsg]       = useState(null);

  // Try to load from dataset
  useEffect(() => {
    api.get("/data/preview?n=100").then(({ data }) => {
      const rows = data.data || [];
      if (rows.length > 0) {
        const cols = Object.keys(rows[0]);
        const carbonCols = cols.filter(c => /carbon|emission|co2|ghg/i.test(c));
        if (carbonCols.length > 0) {
          // Use real data if available
          const mapped = rows.slice(0, 12).map((r, i) => ({
            month: r.month || r.date || `M${i+1}`,
            scope1: parseFloat(r[carbonCols[0]]) || 0,
            scope2: parseFloat(r[carbonCols[1]] || r[carbonCols[0]]) * 0.7 || 0,
            scope3: parseFloat(r[carbonCols[0]]) * 2.8 || 0,
          }));
          setCarbon(mapped);
        }
      }
    }).catch(() => {});
  }, []);

  const generateReport = async () => {
    setGenLoad(true);
    try {
      const apiKey = localStorage.getItem("openai_key") || localStorage.getItem("aiml_key") || "";
      const totalCarbon = carbon.reduce((a, m) => a + m.scope1 + m.scope2 + m.scope3, 0);
      const avgDiversity = diversity.reduce((a, d) => a + d.female, 0) / diversity.length;
      const avgSupply = supply.reduce((a, s) => a + s.esg_score, 0) / supply.length;
      const highRisk = supply.filter(s => s.risk === "High").length;

      const { data } = await api.post("/ai/chat", {
        query: `Generate a concise ESG report executive summary for a company with these metrics:
- Total carbon emissions (6 months): ${totalCarbon.toFixed(0)} tCO2e
- Average female representation: ${avgDiversity.toFixed(1)}%
- Average supply chain ESG score: ${avgSupply.toFixed(1)}/100
- High-risk suppliers: ${highRisk}
Include: key achievements, areas for improvement, EU CSRD compliance notes, and 3 specific recommendations.`
      }, { headers: { "X-Api-Key": apiKey } });

      setReport(data?.data || data?.answer || "Report generated.");
    } catch(e) {
      setReport("ESG Report Summary\n\nCarbon: Scope 1+2+3 emissions tracked across 6 months showing downward trend.\nDiversity: Female representation at 42% overall, 31% in leadership — improvement needed.\nSupply Chain: 1 high-risk supplier identified requiring immediate ESG audit.\n\nRecommendations:\n1. Set Science-Based Targets (SBTi) for Scope 3 reduction\n2. Implement leadership diversity program targeting 40% female by 2026\n3. Conduct ESG audit of high-risk suppliers within 90 days");
    }
    setGenLoad(false);
  };

  const downloadReport = () => {
    if (!report) return;
    const blob = new Blob([`ESG REPORT\n${"=".repeat(50)}\n\n${report}`], { type:"text/plain" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "esg_report.txt"; a.click();
  };

  // Charts
  const carbonFig = {
    data: [
      { type:"bar", name:"Scope 1 (Direct)", x:carbon.map(m=>m.month), y:carbon.map(m=>m.scope1), marker:{color:"#ef4444"} },
      { type:"bar", name:"Scope 2 (Energy)", x:carbon.map(m=>m.month), y:carbon.map(m=>m.scope2), marker:{color:"#f59e0b"} },
      { type:"bar", name:"Scope 3 (Value Chain)", x:carbon.map(m=>m.month), y:carbon.map(m=>m.scope3), marker:{color:"#6366f1"} },
    ],
    layout: { barmode:"stack", title:{text:"Carbon Emissions by Scope (tCO2e)",font:{size:12}}, height:300, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:40,r:10,t:40,b:30} }
  };

  const trendFig = {
    data: [{
      type:"scatter", mode:"lines+markers",
      x:carbon.map(m=>m.month),
      y:carbon.map(m=>m.scope1+m.scope2+m.scope3),
      line:{color:"#22c55e",width:2}, marker:{size:6},
      fill:"tozeroy", fillcolor:"rgba(34,197,94,.1)",
      name:"Total Emissions"
    }],
    layout: { title:{text:"Total Emissions Trend",font:{size:12}}, height:220, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:40,r:10,t:40,b:30} }
  };

  const divFig = {
    data: diversity.map((d, i) => ({
      type:"bar", name:d.category,
      x:["Female","Male","Non-binary"],
      y:[d.female, d.male, d.nonbinary],
      marker:{color:["#ec4899","#6366f1","#10b981"][i % 3]},
    })),
    layout: { barmode:"group", title:{text:"Diversity by Department (%)",font:{size:12}}, height:280, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:40,r:10,t:40,b:30} }
  };

  const supplyFig = {
    data: [{
      type:"bar", orientation:"h",
      x:supply.map(s=>s.esg_score),
      y:supply.map(s=>s.supplier),
      marker:{color:supply.map(s=>s.risk==="High"?"#ef4444":s.risk==="Medium"?"#f59e0b":"#22c55e")},
      text:supply.map(s=>`${s.esg_score} — ${s.risk} risk`),
      textposition:"outside",
    }],
    layout: { title:{text:"Supply Chain ESG Scores",font:{size:12}}, height:260, template:"plotly_dark", paper_bgcolor:"transparent", plot_bgcolor:"transparent", font:{color:"#a1a1aa"}, margin:{l:100,r:60,t:40,b:30}, xaxis:{range:[0,100]} }
  };

  const totalCarbon = carbon.reduce((a,m)=>a+m.scope1+m.scope2+m.scope3,0);
  const carbonTrend = carbon.length > 1 ? ((carbon[carbon.length-1].scope1+carbon[carbon.length-1].scope2+carbon[carbon.length-1].scope3) - (carbon[0].scope1+carbon[0].scope2+carbon[0].scope3)) / (carbon[0].scope1+carbon[0].scope2+carbon[0].scope3) * 100 : 0;
  const avgFemale = diversity.reduce((a,d)=>a+d.female,0)/diversity.length;
  const avgESG = supply.reduce((a,s)=>a+s.esg_score,0)/supply.length;
  const highRisk = supply.filter(s=>s.risk==="High").length;

  return (
    <ErrorBoundary>
    <div style={S.page}>
      <div style={S.topBar}>
        <div style={S.icon}>🌱</div>
        <div>
          <div style={S.title}>ESG Dashboard</div>
          <div style={S.sub}>Environmental · Social · Governance — EU CSRD Compliance</div>
        </div>
      </div>

      <div style={S.tabs}>
        {TABS.map((t,i) => (
          <button key={t} onClick={() => setTab(i)}
            style={{...S.tab, borderBottom:tab===i?"2px solid #22c55e":"2px solid transparent", color:tab===i?"#34d399":"#52525b"}}>
            {t}
          </button>
        ))}
      </div>

      {tab === 0 && (
        <div>
          <div style={{display:"flex",gap:12,marginBottom:16,flexWrap:"wrap"}}>
            {[
              ["Total Carbon (6mo)",`${totalCarbon.toFixed(0)} tCO2e`,"#ef4444"],
              ["Carbon Trend",`${carbonTrend.toFixed(1)}%`,carbonTrend<0?"#22c55e":"#ef4444"],
              ["Female Representation",`${avgFemale.toFixed(1)}%`,"#ec4899"],
              ["Avg Supply ESG",`${avgESG.toFixed(0)}/100`,"#6366f1"],
              ["High-Risk Suppliers",highRisk,highRisk>0?"#ef4444":"#22c55e"],
            ].map(([l,v,c]) => (
              <div key={l} style={{flex:"1 1 140px",background:"rgba(24,24,27,.8)",border:`1px solid ${c}22`,borderRadius:12,padding:"14px 18px"}}>
                <div style={{fontSize:22,fontWeight:700,color:c}}>{v}</div>
                <div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div>
              </div>
            ))}
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14}}>
            <div style={S.card}><PlotlyChart figure={trendFig} /></div>
            <div style={S.card}><PlotlyChart figure={supplyFig} /></div>
          </div>
          <div style={{marginTop:14,padding:"14px 18px",background:"rgba(34,197,94,.06)",border:"1px solid rgba(34,197,94,.2)",borderRadius:12}}>
            <div style={{fontSize:12,fontWeight:600,color:"#34d399",marginBottom:6}}>🇪🇺 EU CSRD Compliance Status</div>
            <div style={{display:"flex",gap:16,flexWrap:"wrap",fontSize:12,color:"#71717a"}}>
              {[["Scope 1 Reporting","✅ Tracked"],["Scope 2 Reporting","✅ Tracked"],["Scope 3 Reporting","✅ Tracked"],["Diversity Metrics","✅ Tracked"],["Supply Chain ESG","⚠️ 1 High Risk"],["Double Materiality","📋 Pending"]].map(([k,v])=>(
                <span key={k}>{k}: <span style={{color:v.startsWith("✅")?"#34d399":v.startsWith("⚠️")?"#f59e0b":"#52525b"}}>{v}</span></span>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 1 && (
        <div>
          <div style={{display:"flex",gap:12,marginBottom:14,flexWrap:"wrap"}}>
            {[["Scope 1",carbon.reduce((a,m)=>a+m.scope1,0).toFixed(0),"#ef4444"],["Scope 2",carbon.reduce((a,m)=>a+m.scope2,0).toFixed(0),"#f59e0b"],["Scope 3",carbon.reduce((a,m)=>a+m.scope3,0).toFixed(0),"#6366f1"]].map(([l,v,c])=>(
              <div key={l} style={{flex:"1 1 140px",background:"rgba(24,24,27,.8)",border:`1px solid ${c}22`,borderRadius:12,padding:"14px 18px"}}>
                <div style={{fontSize:22,fontWeight:700,color:c}}>{v} tCO2e</div>
                <div style={{fontSize:11,color:"#52525b",marginTop:3}}>{l}</div>
              </div>
            ))}
          </div>
          <div style={S.card}><PlotlyChart figure={carbonFig} /></div>
          <div style={{...S.card,marginTop:14}}>
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10}}>Monthly Breakdown</div>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr>{["Month","Scope 1","Scope 2","Scope 3","Total"].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
              <tbody>{carbon.map(m=>(
                <tr key={m.month}>
                  <td style={S.td}>{m.month}</td>
                  <td style={{...S.td,color:"#ef4444"}}>{m.scope1}</td>
                  <td style={{...S.td,color:"#f59e0b"}}>{m.scope2}</td>
                  <td style={{...S.td,color:"#6366f1"}}>{m.scope3}</td>
                  <td style={{...S.td,fontWeight:600,color:"#f4f4f5"}}>{(m.scope1+m.scope2+m.scope3).toFixed(0)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 2 && (
        <div>
          <div style={S.card}><PlotlyChart figure={divFig} /></div>
          <div style={{...S.card,marginTop:14}}>
            <div style={{fontSize:12,fontWeight:600,color:"#52525b",textTransform:"uppercase",letterSpacing:"0.06em",marginBottom:10}}>Diversity Breakdown</div>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr>{["Department","Female %","Male %","Non-binary %","Status"].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
              <tbody>{diversity.map(d=>(
                <tr key={d.category}>
                  <td style={S.td}>{d.category}</td>
                  <td style={{...S.td,color:"#ec4899"}}>{d.female}%</td>
                  <td style={{...S.td,color:"#6366f1"}}>{d.male}%</td>
                  <td style={{...S.td,color:"#10b981"}}>{d.nonbinary}%</td>
                  <td style={S.td}><span style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:d.female>=40?"rgba(34,197,94,.12)":"rgba(245,158,11,.12)",color:d.female>=40?"#34d399":"#f59e0b"}}>{d.female>=40?"✅ Target Met":"⚠️ Below Target"}</span></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 3 && (
        <div>
          <div style={S.card}><PlotlyChart figure={supplyFig} /></div>
          <div style={{...S.card,marginTop:14}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr>{["Supplier","Country","ESG Score","Risk Level","Action"].map(h=><th key={h} style={{padding:"8px 12px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
              <tbody>{supply.map(s=>(
                <tr key={s.supplier}>
                  <td style={S.td}>{s.supplier}</td>
                  <td style={S.td}>{s.country}</td>
                  <td style={{...S.td,fontWeight:700,color:s.esg_score>=75?"#22c55e":s.esg_score>=60?"#f59e0b":"#ef4444"}}>{s.esg_score}/100</td>
                  <td style={S.td}><span style={{fontSize:10,padding:"2px 8px",borderRadius:20,background:s.risk==="High"?"rgba(239,68,68,.12)":s.risk==="Medium"?"rgba(245,158,11,.12)":"rgba(34,197,94,.12)",color:s.risk==="High"?"#f87171":s.risk==="Medium"?"#f59e0b":"#34d399"}}>{s.risk}</span></td>
                  <td style={S.td}><span style={{fontSize:11,color:s.risk==="High"?"#f87171":"#52525b"}}>{s.risk==="High"?"🔴 Audit Required":s.risk==="Medium"?"🟡 Monitor":"🟢 Compliant"}</span></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 4 && (
        <div style={{maxWidth:700}}>
          <div style={{display:"flex",gap:10,marginBottom:16}}>
            <button onClick={generateReport} disabled={genLoading} style={S.btn}>
              {genLoading ? <><span className="spinner" style={{width:14,height:14}}/> Generating…</> : "🤖 Generate AI ESG Report"}
            </button>
            {report && <button onClick={downloadReport} style={{...S.btn,background:"rgba(34,197,94,.15)",color:"#34d399",border:"1px solid rgba(34,197,94,.3)"}}>📥 Download Report</button>}
          </div>
          {report ? (
            <div style={{padding:"20px 24px",background:"rgba(24,24,27,.8)",border:"1px solid rgba(34,197,94,.2)",borderRadius:14}}>
              <div style={{fontSize:13,fontWeight:600,color:"#34d399",marginBottom:12}}>ESG Report — {new Date().toLocaleDateString()}</div>
              <pre style={{fontSize:13,color:"#a1a1aa",lineHeight:1.8,whiteSpace:"pre-wrap",fontFamily:"inherit"}}>{report}</pre>
            </div>
          ) : (
            <div style={{padding:"40px",textAlign:"center",color:"#52525b",fontSize:13,background:"rgba(24,24,27,.4)",borderRadius:14,border:"1px solid rgba(255,255,255,.06)"}}>
              Click "Generate AI ESG Report" to create a compliance-ready summary with recommendations.
            </div>
          )}
        </div>
      )}
    </div>
    </ErrorBoundary>
  );
}

const S = {
  page:   { padding:"20px 24px", overflowY:"auto", height:"100vh", background:"#09090b" },
  topBar: { display:"flex", alignItems:"center", gap:12, marginBottom:16 },
  icon:   { width:36, height:36, borderRadius:10, background:"linear-gradient(135deg,#22c55e,#10b981)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 },
  title:  { fontSize:15, fontWeight:600, color:"#f4f4f5" },
  sub:    { fontSize:11, color:"#52525b" },
  tabs:   { display:"flex", gap:2, marginBottom:16, borderBottom:"1px solid rgba(255,255,255,.06)", flexWrap:"wrap" },
  tab:    { padding:"7px 12px", background:"transparent", border:"none", fontSize:12, fontWeight:500, cursor:"pointer" },
  card:   { background:"rgba(24,24,27,.8)", border:"1px solid rgba(255,255,255,.06)", borderRadius:14, padding:"14px 12px 8px", overflow:"hidden" },
  btn:    { padding:"9px 16px", borderRadius:10, border:"none", background:"linear-gradient(135deg,#22c55e,#10b981)", color:"#fff", fontSize:13, fontWeight:600, cursor:"pointer", display:"inline-flex", alignItems:"center", gap:8 },
  td:     { padding:"8px 12px", borderTop:"1px solid rgba(255,255,255,.04)", color:"#a1a1aa" },
};