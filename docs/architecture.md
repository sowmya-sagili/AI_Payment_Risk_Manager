# Architecture Documentation

## System Flow

User
↓
Streamlit Dashboard
↓
FastAPI REST API
↓
Risk Engine
↓
Risk Predictor
↓
XGBoost Model
↓
Risk Assessment
↓
AI Investigation
↓
SQLite History

## Components

### 1. Streamlit Dashboard (Frontend)
Provides a clean, professional fintech interface. Allows the user to input transaction details, view the ML Risk Assessment, explore overall system analytics, check the model's held-out test performance, and view transaction history.

### 2. FastAPI REST API (Backend)
Serves as the robust integration layer. Exposes RESTful JSON endpoints (`/health`, `/analyze`, `/investigate`, `/history`, `/analytics`). Handles input validation using Pydantic schemas.

### 3. Risk Engine
Takes the raw probabilistic output from the ML model and translates it into a business decision. Applies configured risk policy thresholds (LOW, MEDIUM, HIGH) and determines the recommended action (APPROVE, ADDITIONAL VERIFICATION, FLAG FOR REVIEW).

### 4. Stage 2 ML Pipeline & Predictor
*   **Data Processing:** Uses `scikit-learn` Pipelines (RobustScaler, SimpleImputer) to handle PCA-transformed numerical features (`V1-V28`), and standardizes feature engineering (`LogAmount`, `HourOfDay`).
*   **XGBoost Model:** A gradient-boosted decision tree classifier trained on highly imbalanced transaction data. Outputs a raw fraud probability between 0 and 1.
*   **RiskPredictor:** The runtime inference class that loads `.joblib` artifacts and executes the prediction synchronously.

### 5. AI Investigation
Provides an explainable, grounded analysis of the Risk Engine's output. If an LLM is configured (`AI_API_KEY`), it safely grounds the model with strict prompts to prevent hallucination of non-existent features (e.g., location, merchant history). Defaults to deterministic Python logic if an LLM is unavailable.

### 6. SQLite Database
A lightweight local persistence layer used to track analyzed transactions for analytics and historical auditing. Does not store sensitive API keys or credentials.
