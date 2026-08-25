import pytest
import os
import pandas as pd
from ml.preprocess import load_and_preprocess, get_preprocessor
from ml.predict import RiskPredictor

# Placeholder tests for Stage 2

def test_dataset_loading():
    # Only run if raw data exists (skips in CI without data)
    if os.path.exists("data/raw/creditcard.csv"):
        X, y = load_and_preprocess("data/raw/creditcard.csv")
        assert not X.empty
        assert not y.empty
        # Check feature engineering
        assert 'HourOfDay' in X.columns
        assert 'LogAmount' in X.columns
        assert 'Time' not in X.columns

def test_preprocessing():
    if os.path.exists("data/raw/creditcard.csv"):
        X, _ = load_and_preprocess("data/raw/creditcard.csv")
        preprocessor = get_preprocessor()
        X_processed = preprocessor.fit_transform(X)
        
        assert X_processed is not None
        assert X_processed.shape[1] == X.shape[1]

def test_model_prediction_range():
    # Ensure model exists
    if os.path.exists("ml/model/model.joblib"):
        predictor = RiskPredictor()
        
        # Create a dummy transaction
        dummy_tx = {f"V{i}": 0.0 for i in range(1, 29)}
        dummy_tx['Time'] = 3600
        dummy_tx['Amount'] = 100.0
        
        result = predictor.predict_risk(dummy_tx)
        
        # Test ranges
        assert 0.0 <= result['risk_probability'] <= 1.0
        assert 0 <= result['risk_score'] <= 100
        assert isinstance(result['risk_score'], int)
