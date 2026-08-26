import joblib
import pandas as pd
import numpy as np
import json
import sys
import os

def main():
    model_dir = "ml/model"
    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    preprocessor = joblib.load(os.path.join(model_dir, "preprocessor.joblib"))
    features = joblib.load(os.path.join(model_dir, "feature_names.joblib"))
    
    with open("demo_transactions.json", "r") as f:
        demo_txs = json.load(f)
        
    failed = False
    
    for level, tx in demo_txs.items():
        df = pd.DataFrame([tx])
        if 'Time' in df.columns:
            df['HourOfDay'] = (df['Time'] // 3600) % 24
        else:
            df['HourOfDay'] = 0
            
        if 'Amount' in df.columns:
            df['LogAmount'] = np.log1p(df['Amount'])
            
        for f in features:
            if f not in df.columns:
                df[f] = 0
                
        df = df[features]
        X = preprocessor.transform(df)
        prob = float(model.predict_proba(X)[0, 1])
        score = int(round(prob * 100))
        
        if score <= 30:
            actual_level = "LOW"
            action = "APPROVE"
        elif score <= 70:
            actual_level = "MEDIUM"
            action = "ADDITIONAL_VERIFICATION"
        else:
            actual_level = "HIGH"
            action = "FLAG_FOR_REVIEW"
            
        print(f"{level}")
        print(f"Probability: {prob:.6f}")
        print(f"Score: {score}")
        print(f"Risk Level: {actual_level}")
        print(f"Action: {action}")
        
        if actual_level != level:
            print("FAIL")
            failed = True
        else:
            print("PASS")
        print()
        
    if failed:
        print("Validation FAILED: One or more demo transactions resulted in an incorrect category.")
        sys.exit(1)
    else:
        print("Validation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
