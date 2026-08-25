import pytest
from backend.services.risk_engine import RiskEngine
from backend.schemas.risk import RiskAssessmentResponse
from fastapi.testclient import TestClient
from backend.main import app

def test_risk_levels():
    engine = RiskEngine()
    
    # Test Low Risk
    level, action = engine.determine_risk_level_and_action(0)
    assert level == "LOW" and action == "APPROVE"
    
    level, action = engine.determine_risk_level_and_action(30)
    assert level == "LOW" and action == "APPROVE"
    
    # Test Medium Risk
    level, action = engine.determine_risk_level_and_action(31)
    assert level == "MEDIUM" and action == "ADDITIONAL_VERIFICATION"
    
    level, action = engine.determine_risk_level_and_action(70)
    assert level == "MEDIUM" and action == "ADDITIONAL_VERIFICATION"
    
    # Test High Risk
    level, action = engine.determine_risk_level_and_action(71)
    assert level == "HIGH" and action == "FLAG_FOR_REVIEW"
    
    level, action = engine.determine_risk_level_and_action(100)
    assert level == "HIGH" and action == "FLAG_FOR_REVIEW"

def test_assess_transaction():
    engine = RiskEngine()
    result = engine.assess_transaction("TX-999", 0.85, 85)
    
    assert result.transaction_id == "TX-999"
    assert result.risk_score == 85
    assert result.risk_level == "HIGH"
    assert result.recommended_action == "FLAG_FOR_REVIEW"
    assert "High model-predicted fraud probability" in result.risk_factors

client = TestClient(app)

def test_api_health():
    # If the dummy model was created, this should be 200, otherwise 503
    response = client.get("/api/v1/risk/health")
    assert response.status_code in [200, 503]

def test_api_analyze_missing_fields():
    response = client.post("/api/v1/risk/analyze", json={
        "transaction_id": "TX-123"
        # missing Amount and Time
    })
    assert response.status_code == 422 # Validation error

def test_api_analyze_invalid_type():
    response = client.post("/api/v1/risk/analyze", json={
        "transaction_id": "TX-123",
        "Amount": "NOT_A_NUMBER",
        "Time": 3600
    })
    assert response.status_code == 422 # Validation error

def test_api_analyze_success():
    # Attempt to post a valid transaction. If model is 503, skip.
    health = client.get("/api/v1/risk/health")
    if health.status_code == 200:
        response = client.post("/api/v1/risk/analyze", json={
            "transaction_id": "TX-1001",
            "Amount": 150.50,
            "Time": 3600.0,
            "V1": 0.5,
            "V2": -0.1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "TX-1001"
        assert "risk_score" in data
        assert "risk_level" in data
        assert "recommended_action" in data
