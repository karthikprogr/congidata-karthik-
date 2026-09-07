import pathlib

f = pathlib.Path('src/pages/Reports.jsx')
content = f.read_text(encoding='utf-8-sig')  # strip BOM

# Find the second ErrorBoundary class (the duplicate/broken one)
first_eb = content.find('class ErrorBoundary')
second_eb = content.find('class ErrorBoundary', first_eb + 10)
print('First EB at:', first_eb, 'Second EB at:', second_eb)

# Remove everything from second_eb up to (but not including) 'const TABS'
tabs_start = content.find('const TABS = [')
print('TABS found at:', tabs_start)

if tabs_start > 0:
    clean_body = content[tabs_start:]
    
    header = '''import { useEffect, useState, useMemo, Component } from "react";
import { api, dataApi } from "../api/client";
import PlotlyChart from "../components/PlotlyChart";
import Table from "../components/Table";

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

'''
    
    final = header + clean_body
    f.write_text(final, encoding='utf-8')
    print('Fixed successfully!')
    print('File size:', len(final))
else:
    print('ERROR: TABS not found in file')
    print('First 300 chars:', repr(content[:300]))
