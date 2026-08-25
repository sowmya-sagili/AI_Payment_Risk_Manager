import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from ml.preprocess import load_and_preprocess, get_preprocessor
from ml.evaluate import evaluate_model
import time

def train_models():
    # 1. Load and Preprocess Data
    X, y = load_and_preprocess("data/raw/creditcard.csv")
    
    # 2. Train/Test Split
    # We use a 80/20 split and stratify by target 'y' due to extreme class imbalance
    print("Splitting dataset into train and test sets (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 3. Fit Preprocessor only on training data
    print("Fitting preprocessor on training data...")
    preprocessor = get_preprocessor()
    X_train_processed = preprocessor.fit_transform(X_train)
    X_test_processed = preprocessor.transform(X_test)
    
    # 4. Class Imbalance Handling
    # The dataset is highly imbalanced (~0.17% fraud).
    # We will use class weights and scale_pos_weight to handle this naturally within the algorithms.
    class_weight_dict = 'balanced'
    scale_pos_weight_val = (y_train == 0).sum() / (y_train == 1).sum()
    
    # 5. Define Models
    models = {
        "Logistic Regression": LogisticRegression(class_weight=class_weight_dict, max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=50, max_depth=10, class_weight=class_weight_dict, random_state=42, n_jobs=-1),
        "XGBoost": XGBClassifier(scale_pos_weight=scale_pos_weight_val, random_state=42, use_label_encoder=False, eval_metric='logloss')
    }
    
    best_f1 = -1
    best_model_name = ""
    best_model = None
    
    # 6. Train and Evaluate
    print("\n--- Training Models ---")
    results = {}
    for name, model in models.items():
        print(f"Training {name}...")
        start_time = time.time()
        model.fit(X_train_processed, y_train)
        print(f"Training completed in {time.time() - start_time:.2f} seconds.")
        
        print(f"Evaluating {name}...")
        metrics = evaluate_model(name, model, X_test_processed, y_test)
        results[name] = metrics
        
        # We will select the best model primarily based on F1-Score (balancing Precision and Recall)
        # In risk management, a balance is needed so we don't block all transactions (low precision)
        # while catching as much fraud as possible (high recall).
        if metrics['F1-Score'] > best_f1:
            best_f1 = metrics['F1-Score']
            best_model_name = name
            best_model = model
            
    print(f"\n--- Best Model Selected: {best_model_name} ---")
    print("Reason: Achieved the highest F1-score, providing the best balance between Precision (preventing false positives) and Recall (catching true frauds).")
    
    # 7. Save the Final Model and Preprocessor
    os.makedirs("ml/model", exist_ok=True)
    model_path = "ml/model/model.joblib"
    preprocessor_path = "ml/model/preprocessor.joblib"
    
    print(f"Saving the selected model to {model_path}...")
    joblib.dump(best_model, model_path)
    joblib.dump(preprocessor, preprocessor_path)
    print("Model saved successfully.")
    
    # Save feature names for the API
    feature_names = X.columns.tolist()
    joblib.dump(feature_names, "ml/model/feature_names.joblib")
    
if __name__ == "__main__":
    train_models()
