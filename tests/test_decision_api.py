import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_decision_circuit_breaker():
    # We will trigger the graph critical circuit breaker
    payload = {
        "transaction_id": "TX-C-BREAK-1",
        "customer_id": "CUS-C-BREAK-1",
        "device_id": "DEV-BREAK",
        "ip_address": "IP-BREAK",
        "payment_account_id": "PAY-BREAK",
        "Amount": 100.0,
        "Time": 0.0,
        "V1": 0.0
    }
    
    # Send 3 to build a graph cluster
    for i in range(3):
        payload["transaction_id"] = f"TX-C-BREAK-{i}"
        payload["customer_id"] = f"CUS-C-BREAK-{i}"
        res = client.post("/api/v1/risk/analyze", json=payload)
        
    data = res.json()
    assert data["decision_mode"] == "CIRCUIT_BREAKER"
    assert data["risk_level"] == "HIGH"
    assert "GRAPH_CRITICAL" in [r["rule_id"] for r in data["triggered_rules"]]
    
def test_api_decision_missing_graph():
    payload = {
        "transaction_id": "TX-MISS-G",
        "customer_id": "CUS-MISS-G",
        "Amount": 100.0,
        "Time": 0.0,
        "V1": 0.0
    }
    res = client.post("/api/v1/risk/analyze", json=payload)
    data = res.json()
    assert data["graph_weight"] == 0.0
    assert data["ml_weight"] > 0.5 # Should be 0.67
    
