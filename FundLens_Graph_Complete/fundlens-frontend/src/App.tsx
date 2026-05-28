// frontend/src/App.tsx
import { useState } from "react";
import GraphVisualization from "./components/GraphVisualization";

export default function App() {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  return (
    <div style={{ width:"100vw", height:"100vh", background:"#060C1E", display:"flex", flexDirection:"column", fontFamily:"DM Sans, sans-serif" }}>
      <div style={{ height:48, background:"#0A142F", borderBottom:"1px solid #12244E", display:"flex", alignItems:"center", padding:"0 20px", gap:12 }}>
        <div style={{ width:32, height:32, background:"#00C9A7", borderRadius:7, display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700, fontSize:13, color:"#0A142F" }}>FL</div>
        <span style={{ color:"#F0F4F8", fontWeight:600, fontSize:15 }}>FundLens</span>
        <span style={{ color:"#8899AA", fontSize:12, borderLeft:"1px solid #12244E", paddingLeft:12 }}>Graph View — CASE-2847</span>
        {selectedNode && <span style={{ marginLeft:"auto", background:"rgba(0,201,167,0.12)", border:"1px solid #00C9A7", color:"#00C9A7", fontSize:11, padding:"3px 12px", borderRadius:20 }}>Selected: {selectedNode}</span>}
      </div>
      <div style={{ flex:1, padding:12 }}>
        <GraphVisualization caseId="CASE-2847" onNodeClick={(n) => { setSelectedNode(n); console.log("clicked:", n); }} />
      </div>
    </div>
  );
}
