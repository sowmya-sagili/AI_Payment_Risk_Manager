import pytest
from fastapi.testclient import TestClient
from backend.main import app
import json

client = TestClient(app)

def test_decision_regression():
    health = client.get("/api/v1/risk/health")
    if health.status_code == 503:
        pytest.skip("Model not loaded")

    with open("demo_transactions.json", "r") as f:
        demo_txs = json.load(f)

    for expected_level, tx in demo_txs.items():
        payload = dict(tx)
        payload["transaction_id"] = f"TX-DEC-REG-{expected_level}"
        if "Time" not in payload:
            payload["Time"] = 0.0
            
        # We purposely omit device_id and ip_address so graph_available=False
        # Redis is disabled by default in test config, so velocity_available=False
        
        res = client.post("/api/v1/risk/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        
        # Verify ML properties remain intact
        assert data["risk_probability"] >= 0.0
        
        # Ensure fallback to purely ML
        assert data["ml_weight"] == 1.0
        assert data["velocity_weight"] == 0.0
        assert data["graph_weight"] == 0.0
        
        # Check risk level maps correctly
        assert data["risk_level"] == expected_level
