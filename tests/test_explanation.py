import pytest
from fastapi.testclient import TestClient
from backend.main import app
import json
import joblib
import os

client = TestClient(app)

def test_explanation_service_loads():
    from backend.services.explanation_service import explanation_service
    assert explanation_service.model is not None
    assert type(explanation_service.model).__name__ == "XGBClassifier"

def test_explain_endpoint_valid_input():
    health = client.get("/api/v1/risk/health")
    if health.status_code == 503:
        pytest.skip("Model not loaded")
        
    payload = {
        "transaction_id": "TX-EXPLAIN",
        "Amount": 100.0,
        "Time": 3600.0,
        "V1": -1.0
    }
    
    # Check that analyze works
    res_analyze = client.post("/api/v1/risk/analyze", json=payload)
    assert res_analyze.status_code == 200
    prob_analyze = res_analyze.json()["risk_probability"]
    
    # Check that explain works
    res_explain = client.post("/api/v1/risk/explain", json=payload)
    assert res_explain.status_code == 200
    data = res_explain.json()
    
    # 12. SHAP does not modify original risk probability
    assert abs(data["risk_probability"] - prob_analyze) < 1e-6
    
    # 5. Every contributor has correct fields
    contributors = data["top_contributors"]
    assert len(contributors) > 0
    for c in contributors:
        assert "feature_name" in c
        assert "feature_value" in c
        assert "shap_value" in c
        assert "contribution" in c
        
    # 4. Sorted by absolute SHAP magnitude descending
    magnitudes = [abs(c["shap_value"]) for c in contributors]
    assert all(magnitudes[i] >= magnitudes[i+1] for i in range(len(magnitudes)-1))

def test_explain_endpoint_missing_fields():
    payload = {
        "transaction_id": "TX-MISSING",
        "Amount": 100.0
        # Time missing
    }
    res = client.post("/api/v1/risk/explain", json=payload)
    assert res.status_code == 422

def test_explain_endpoint_invalid_input():
    payload = {
        "transaction_id": "TX-INVALID",
        "Amount": "INVALID_AMOUNT",
        "Time": 3600.0
    }
    res = client.post("/api/v1/risk/explain", json=payload)
    assert res.status_code == 422

def test_demo_transactions_explain():
    health = client.get("/api/v1/risk/health")
    if health.status_code == 503:
        pytest.skip("Model not loaded")
        
    with open("demo_transactions.json", "r") as f:
        demo_txs = json.load(f)
        
    for level, tx in demo_txs.items():
        payload = dict(tx)
        payload["transaction_id"] = f"TX-DEMO-{level}"
        if "Time" not in payload:
            payload["Time"] = 0.0
            
        res = client.post("/api/v1/risk/explain", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["risk_level"] == level
