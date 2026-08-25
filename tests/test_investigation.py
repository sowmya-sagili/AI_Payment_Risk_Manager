import pytest
from unittest.mock import patch
from backend.services.investigation_service import InvestigationService
from backend.schemas.risk import InvestigationRequest, RiskAssessmentResponse
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture
def dummy_request():
    return InvestigationRequest(
        transaction_id="TX-100",
        transaction_data={"Amount": 100},
        risk_assessment=RiskAssessmentResponse(
            transaction_id="TX-100",
            risk_probability=0.95,
            risk_score=95,
            risk_level="HIGH",
            recommended_action="FLAG_FOR_REVIEW",
            model_name="XGBoost",
            model_version="1.0",
            risk_factors=["High probability"]
        )
    )

def test_investigation_service_fallback_high(dummy_request):
    service = InvestigationService()
    # Force fallback by removing API key
    service.api_key = None
    
    report = service.investigate(dummy_request)
    assert report.transaction_id == "TX-100"
    assert report.risk_level == "HIGH"
    assert "high fraud probability" in report.assessment.lower()
    assert "High probability" in str(report.key_findings)

def test_investigation_service_fallback_low(dummy_request):
    service = InvestigationService()
    service.api_key = None
    dummy_request.risk_assessment.risk_level = "LOW"
    dummy_request.risk_assessment.risk_score = 10
    
    report = service.investigate(dummy_request)
    assert report.risk_level == "LOW"
    assert "fraud probability" in report.assessment.lower()
    assert "low risk" in report.assessment.lower()

@patch("requests.post")
def test_investigation_service_llm_success(mock_post, dummy_request):
    service = InvestigationService()
    service.api_key = "test_key"
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{
            "message": {
                "content": '{"transaction_id": "TX-100", "risk_score": 95, "risk_level": "HIGH", "fraud_probability": 0.95, "assessment": "AI Assessment", "key_findings": ["AI Finding"], "recommended_action": "FLAG_FOR_REVIEW", "confidence_note": "High", "disclaimer": "AI Disclaimer"}'
            }
        }]
    }
    
    report = service.investigate(dummy_request)
    assert report.assessment == "AI Assessment"
    assert report.key_findings == ["AI Finding"]

@patch("requests.post")
def test_investigation_service_llm_failure(mock_post, dummy_request):
    service = InvestigationService()
    service.api_key = "test_key"
    
    mock_post.side_effect = Exception("API Down")
    
    report = service.investigate(dummy_request)
    # Should fallback deterministically
    assert "high fraud probability" in report.assessment.lower()

def test_investigate_api_success():
    health = client.get("/api/v1/risk/health")
    if health.status_code == 200:
        response = client.post("/api/v1/risk/investigate", json={
            "transaction_id": "TX-999",
            "Amount": 150.0,
            "Time": 3600.0,
            "V1": 0.5
        })
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == "TX-999"
        assert "assessment" in data
        assert "key_findings" in data
