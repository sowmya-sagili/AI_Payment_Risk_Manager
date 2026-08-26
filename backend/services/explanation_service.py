import joblib
import os
import shap
import pandas as pd
import numpy as np
from typing import List, Dict, Any

class RiskExplanationService:
    def __init__(self, model_dir: str = "ml/model"):
        self.model = joblib.load(os.path.join(model_dir, "model.joblib"))
        self.preprocessor = joblib.load(os.path.join(model_dir, "preprocessor.joblib"))
        self.features = joblib.load(os.path.join(model_dir, "feature_names.joblib"))
        
        # Initialize SHAP explainer
        # TreeExplainer is best for XGBoost
        self.explainer = shap.TreeExplainer(self.model)
        
    def explain(self, preprocessed_X: np.ndarray, original_features_df: pd.DataFrame) -> List[Dict[str, Any]]:
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(preprocessed_X)
        
        # If it's a binary classification, shap_values might be a list of arrays (one per class)
        # For XGBoost, it's usually just an array of shape (n_samples, n_features) for the positive class
        # Let's handle both gracefully
        if isinstance(shap_values, list):
            # Take the positive class
            shap_values = shap_values[1]
            
        # We only expect 1 sample
        shap_vals = shap_values[0]
        
        feature_names = self.features
        
        # Retrieve the original feature values for the output
        feature_values = original_features_df.iloc[0].to_dict()
        
        contributors = []
        for i, fname in enumerate(feature_names):
            val = shap_vals[i]
            # determine contribution
            contribution = "INCREASED_RISK" if val > 0 else "DECREASED_RISK"
            contributors.append({
                "feature_name": fname,
                "feature_value": float(feature_values.get(fname, 0.0)),
                "shap_value": float(val),
                "contribution": contribution
            })
            
        # Sort by absolute SHAP magnitude descending
        contributors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        
        # Return top 5
        return contributors[:5]

# Singleton instance
explanation_service = RiskExplanationService()
