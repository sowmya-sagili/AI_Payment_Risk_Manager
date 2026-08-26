import joblib
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

def test_model_is_not_dummy():
    model_path = "ml/model/model.joblib"
    assert os.path.exists(model_path), "Model file is missing"
    
    model = joblib.load(model_path)
    model_type = type(model).__name__
    
    assert model_type != "DummyClassifier", "CRITICAL: Model is DummyClassifier!"
    assert model_type in ["XGBClassifier", "LogisticRegression", "RandomForestClassifier"], f"Unexpected model type: {model_type}"

def test_model_prediction_range():
    model = joblib.load("ml/model/model.joblib")
    preprocessor = joblib.load("ml/model/preprocessor.joblib")
    feature_names = joblib.load("ml/model/feature_names.joblib")
    
    # Create a dummy dataframe with all zeros
    df = pd.DataFrame([[0.0] * len(feature_names)], columns=feature_names)
    X = preprocessor.transform(df)
    
    probs = model.predict_proba(X)
    prob_fraud = probs[0, 1]
    
    assert 0.0 <= prob_fraud <= 1.0, f"Probability {prob_fraud} is out of bounds [0, 1]"

def test_integration_analyze_uses_real_model():
    health = client.get("/api/v1/risk/health")
    if health.status_code == 503:
        pytest.skip("Model not loaded, skipping integration test")
        
    payload = {
        "transaction_id": "TX-REGRESSION-1",
        "Amount": 2500.0,
        "Time": 45000.0,
        "V1": -4.5, "V2": 3.2, "V3": -5.5
    }
    
    response = client.post("/api/v1/risk/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "risk_probability" in data
    assert 0.0 <= data["risk_probability"] <= 1.0
    
    # It should not return exactly 0.5 like the dummy did unless by extreme coincidence
    assert data["risk_probability"] != 0.5, "Probability is exactly 0.5, suspecting DummyClassifier fallback"
    assert data["model_name"] == "XGBoost"

def test_history_endpoint():
    response = client.get('/api/v1/risk/history')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    response_limit = client.get('/api/v1/risk/history?limit=1')
    assert response_limit.status_code == 200
    data_limit = response_limit.json()
    assert isinstance(data_limit, list)
    assert len(data_limit) <= 1

def test_analytics_endpoint():
    response = client.get('/api/v1/risk/analytics')
    assert response.status_code == 200
    data = response.json()
    assert 'total_transactions' in data
    assert 'average_amount' in data

import json
def test_demo_transactions():
    health = client.get('/api/v1/risk/health')
    if health.status_code == 503:
        pytest.skip('Model not loaded')
        
    with open('demo_transactions.json', 'r') as f:
        demo_txs = json.load(f)
        
    for expected_level, tx in demo_txs.items():
        for i in range(1, 29):
            assert f'V{i}' in tx, f'V{i} missing in {expected_level} demo transaction'
            
        payload = dict(tx)
        payload['transaction_id'] = f'TX-TEST-{expected_level}'
        if 'Time' not in payload:
            payload['Time'] = 0.0
        
        res = client.post('/api/v1/risk/analyze', json=payload)
        assert res.status_code == 200
        data = res.json()
        
        prob = data['risk_probability']
        assert 0.0 <= prob <= 1.0
        
        assert data['risk_level'] == expected_level, f"Expected {expected_level}, got {data['risk_level']} with prob {prob}"
