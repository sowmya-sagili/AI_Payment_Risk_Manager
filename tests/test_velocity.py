import pytest
from fastapi.testclient import TestClient
from backend.main import app
import time
import pytest
from fastapi.testclient import TestClient
from backend.main import app
import time
import json

client = TestClient(app)
import fakeredis
from backend.services.velocity_engine import velocity_engine

@pytest.fixture(autouse=True)
def mock_redis():
    old_enabled = velocity_engine.enabled
    old_client = velocity_engine.redis_client
    
    velocity_engine.enabled = True
    velocity_engine.redis_client = fakeredis.FakeRedis(decode_responses=True)
    velocity_engine.redis_client.flushdb()
    
    yield
    
    velocity_engine.enabled = old_enabled
    velocity_engine.redis_client = old_client



def get_base_tx(tx_id, cust_id="CUST-TEST", amount=100.0):
    return {
        "transaction_id": tx_id,
        "customer_id": cust_id,
        "Amount": amount,
        "Time": 3600.0,
        "V1": -1.0
    }

def test_no_previous_transactions():
    payload = get_base_tx("TX-V1")
    res = client.post("/api/v1/risk/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    if velocity_engine.enabled:
        assert data["velocity_level"] == "LOW"
        assert data["velocity_metrics"]["transactions_1m"] == 1

def test_multiple_transactions_1m():
    if not velocity_engine.enabled: pytest.skip("Redis disabled")
    for i in range(6):
        payload = get_base_tx(f"TX-1M-{i}", "CUST-1M")
        res = client.post("/api/v1/risk/analyze", json=payload)
    
    data = res.json()
    assert data["velocity_metrics"]["transactions_1m"] == 6
    assert data["velocity_score"] > 30 # high or elevated

def test_duplicate_transaction_id():
    if not velocity_engine.enabled: pytest.skip("Redis disabled")
    payload = get_base_tx("TX-DUP", "CUST-DUP")
    client.post("/api/v1/risk/analyze", json=payload)
    res2 = client.post("/api/v1/risk/analyze", json=payload)
    data = res2.json()
    assert data["velocity_metrics"]["transactions_1m"] == 1 # still 1 because of idempotency

def test_redis_unavailable(monkeypatch):
    monkeypatch.setattr(velocity_engine, "enabled", False)
    payload = get_base_tx("TX-OFF")
    res = client.post("/api/v1/risk/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["velocity_score"] is None
    assert data["final_risk_score"] == data["risk_score"]

def test_missing_customer_id():
    payload = {
        "transaction_id": "TX-NOCUST",
        "Amount": 150.0,
        "Time": 0.0,
        "V1": -1.0
    }
    res = client.post("/api/v1/risk/analyze", json=payload)
    assert res.status_code == 200
    data = res.json()
    if velocity_engine.enabled:
        assert data["velocity_level"] == "LOW"

def test_aggregation():
    if not velocity_engine.enabled: pytest.skip("Redis disabled")
    # For a high velocity, the final risk should be a combination of ML and Velocity
    for i in range(15):
        payload = get_base_tx(f"TX-AGG-{i}", "CUST-AGG")
        client.post("/api/v1/risk/analyze", json=payload)
    
    res = client.post("/api/v1/risk/analyze", json=get_base_tx("TX-AGG-FINAL", "CUST-AGG"))
    data = res.json()
    ml_score = data["risk_score"]
    v_score = data["velocity_score"]
    f_score = data["final_risk_score"]
    
    # It should trigger circuit breaker!
    assert f_score >= 85
    assert data["decision_mode"] in ["CIRCUIT_BREAKER", "RULE_OVERRIDE"]
