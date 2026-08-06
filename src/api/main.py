import os
import torch
import redis
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from torch_geometric.data import Data
from src.graph.gnn_model import FraudGNN
from src.rag.sar_generator import SARGenerator

app = FastAPI(title="Financial Fraud Detection API")

# Initialize Redis client (using same config as consumer.py)
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

def get_redis_client():
    try:
        # Get the host from the environment, default to localhost
        redis_host = os.getenv("REDIS_HOST", "localhost")
        
        # Connect to Redis
        r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"[-] Redis connection failed in API: {e}")

r_client = get_redis_client()

# Initialize the GNN model
model = FraudGNN()
model.eval()

class PredictRequest(BaseModel):
    transaction_id: str

@app.post("/predict")
async def predict(request: PredictRequest):
    if not r_client:
        raise HTTPException(status_code=500, detail="Redis connection not available")

    tx_id = request.transaction_id
    
    # 1. Retrieve transaction details from Redis
    tx_key = f"tx:{tx_id}"
    tx_data = r_client.hgetall(tx_key)
    
    if not tx_data:
        raise HTTPException(status_code=404, detail="Transaction not found")

    try:
        card_id = tx_data["card_id"]
        ip_address = tx_data["ip_address"]
        amount = float(tx_data["amount"])
    except KeyError as e:
        raise HTTPException(status_code=500, detail=f"Incomplete transaction data in Redis: missing {e}")

    # 2. Retrieve 1-hop graph metrics
    merchant_count = r_client.scard(f"card:{card_id}:merchants")
    ip_shared_cards = r_client.scard(f"ip:{ip_address}:cards")

    # 3. Format into a PyTorch Geometric Data object
    # Using features: [amount, merchant_count, ip_shared_cards]
    x = torch.tensor([[amount, float(merchant_count), float(ip_shared_cards)]], dtype=torch.float)
    
    # Simple setup: a single node graph containing the transaction context
    edge_index = torch.empty((2, 0), dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)

    # 4. Pass it through the FraudGNN model
    with torch.no_grad():
        output = model(data)
        risk_score = output.item()
        #risk_score = 0.99
        is_flagged = bool(risk_score > 0.75)

    sar_report = None
    if is_flagged:
        generator = SARGenerator()
        sar_report = generator.generate_sar(
            transaction_id=tx_id,
            merchant_count=int(merchant_count),
            shared_ips=int(ip_shared_cards),
            gnn_risk_score=risk_score
        )

    # 5. Return JSON response
    return {
        "transaction_id": tx_id,
        "risk_score": risk_score,
        "is_flagged": is_flagged,
        "sar_report": sar_report
    }

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
