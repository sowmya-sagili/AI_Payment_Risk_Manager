import joblib
import pandas as pd
import numpy as np
import os

class RiskPredictor:
    def __init__(self, model_dir="ml/model"):
        model_path = os.path.join(model_dir, "model.joblib")
        preprocessor_path = os.path.join(model_dir, "preprocessor.joblib")
        feature_names_path = os.path.join(model_dir, "feature_names.joblib")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Train the model first.")
            
        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)
        self.feature_names = joblib.load(feature_names_path)
        
    def preprocess_transaction(self, transaction_dict):
        # Convert to DataFrame
        df = pd.DataFrame([transaction_dict])
        
        # Ensure all required features are present
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0 # Default/imputed value if missing
                
        # Reorder columns to match training
        df = df[self.feature_names]
        
        # Preprocess
        X_processed = self.preprocessor.transform(df)
        return X_processed

    def predict_risk(self, transaction_dict):
        """
        Takes a transaction dictionary and returns risk probability and risk score.
        """
        # We need to simulate the feature engineering step if raw data is provided
        if 'Time' in transaction_dict and 'HourOfDay' not in transaction_dict:
            transaction_dict['HourOfDay'] = (transaction_dict['Time'] // 3600) % 24
        
        if 'Amount' in transaction_dict and 'LogAmount' not in transaction_dict:
            transaction_dict['LogAmount'] = np.log1p(transaction_dict['Amount'])
            
        X_processed = self.preprocess_transaction(transaction_dict)
        
        # Get probability of class 1 (Fraud)
        if hasattr(self.model, "predict_proba"):
            risk_probability = self.model.predict_proba(X_processed)[0, 1]
        else:
            # Fallback if model doesn't support predict_proba
            risk_probability = float(self.model.predict(X_processed)[0])
            
        # Convert to 0-100 score
        risk_score = int(round(risk_probability * 100))
        
        return {
            "risk_probability": float(risk_probability),
            "risk_score": risk_score
        }

if __name__ == "__main__":
    predictor = RiskPredictor()
    # Dummy transaction
    dummy_tx = {f"V{i}": 0.0 for i in range(1, 29)}
    dummy_tx['Time'] = 3600
    dummy_tx['Amount'] = 100.0
    
    result = predictor.predict_risk(dummy_tx)
    print("Prediction Result:", result)
