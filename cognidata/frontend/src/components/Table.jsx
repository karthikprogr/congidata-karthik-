export default function Table({ data }) {
  if (!data?.length) return <p style={{ color:"#52525b",fontSize:13 }}>No data.</p>;
  const keys = Object.keys(data[0]);
  return (
    <div style={{ overflowX:"auto",borderRadius:10,border:"1px solid rgba(255,255,255,.06)",marginTop:6 }}>
      <table style={{ width:"100%",borderCollapse:"collapse",fontSize:12 }}>
        <thead>
          <tr>{keys.map(k => <th key={k} style={{ padding:"9px 14px",background:"rgba(9,9,11,.9)",color:"#52525b",textAlign:"left",fontWeight:600,whiteSpace:"nowrap",fontSize:11,textTransform:"uppercase",letterSpacing:"0.04em" }}>{k}</th>)}</tr>
        </thead>
        <tbody>
          {data.map((row,i) => (
            <tr key={i} style={{ background: i%2===0?"transparent":"rgba(255,255,255,.01)" }}>
              {keys.map(k => <td key={k} style={{ padding:"8px 14px",borderTop:"1px solid rgba(255,255,255,.04)",color:"#a1a1aa" }}>{row[k]==null?"—":String(row[k])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
