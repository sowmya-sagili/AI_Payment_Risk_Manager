import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_graph_health():
    res = client.get("/api/v1/risk/graph/health")
    assert res.status_code == 200
    assert "status" in res.json()

def test_analyze_with_graph_missing_identifiers():
    payload = {
        "transaction_id": "TX-GRAPH-NO-ID",
        "customer_id": "CUS-NO-ID",
        "Amount": 100.0,
        "Time": 0.0,
        "V1": 0.0
    }
    res = client.post("/api/v1/risk/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["graph_score"] is None
    assert data["graph_risk_level"] is None

def test_analyze_with_graph_fraud_ring():
    # Send 2 transactions with same device
    for i in range(2):
        payload = {
            "transaction_id": f"TX-RING-{i}",
            "customer_id": f"CUS-RING-{i}",
            "device_id": "DEV-RING",
            "ip_address": "10.0.0.1",
            "Amount": 100.0,
            "Time": 0.0,
            "V1": 0.0
        }
        res = client.post("/api/v1/risk/analyze", json=payload)
        
    data = res.json()
    assert data["graph_score"] > 0
    assert data["cluster_id"] is not None
    assert len(data["graph_signals"]) > 0
    
    # Test customer network endpoint
    net_res = client.get("/api/v1/risk/graph/customer/CUS-RING-1")
    assert net_res.status_code == 200
    net_data = net_res.json()
    assert net_data["customer_id"] == "CUS-RING-1"
    assert len(net_data["nodes"]) >= 3
