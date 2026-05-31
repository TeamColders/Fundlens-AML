import time
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from backend.ml.gnn_model import FraudGAT

app = FastAPI(title="GNN Inference Service")

class SubgraphRequest(BaseModel):
    case_id: str
    subgraph: Dict[str, Any]

# Global state for model
model = None
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

@app.on_event("startup")
async def load_model():
    global model
    model = FraudGAT()
    try:
        model.load_state_dict(torch.load('models/gnn_v1.pt', map_location=device))
        model.to(device)
        model.eval()
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load model weights: {e}")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_version": "gnn_v1",
        "model_loaded": model is not None,
        "device": str(device)
    }

@app.post("/score")
def score_subgraph(request: SubgraphRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    start_time = time.time()
    
    try:
        nodes = request.subgraph.get("nodes", [])
        edges = request.subgraph.get("edges", [])
        
        if not nodes:
            raise ValueError("Graph has no nodes")
            
        node_scores = model.predict_subgraph(nodes, edges)
        
        # Calculate aggregate score (e.g., max node score)
        fraud_probability = max(node_scores.values()) if node_scores else 0.0
        
        inference_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "case_id": request.case_id,
            "fraud_probability": round(fraud_probability, 4),
            "node_scores": {k: round(v, 4) for k, v in node_scores.items()},
            "inference_time_ms": inference_time_ms,
            "model_version": "gnn_v1",
            "threshold_crossed": fraud_probability > 0.70,
            "risk_level": "critical" if fraud_probability > 0.85 else "high" if fraud_probability > 0.70 else "medium"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
