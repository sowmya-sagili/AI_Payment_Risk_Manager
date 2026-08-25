# AI Payment Risk Manager

An AI-powered transaction risk assessment platform that combines machine-learning fraud prediction with configurable risk policies and grounded AI investigation. The system analyzes transactions, produces a 0–100 risk score, classifies transactions into LOW, MEDIUM, or HIGH risk, recommends an appropriate action, and provides an explainable investigation summary. 

Designed independently as a prototype for the AI Risk Manager track.

## Problem
Identifying potentially fraudulent transactions in real-time requires balancing complex probabilistic machine learning outputs with definitive business rules, all while maintaining transparency and explainability for compliance and manual review teams.

## Solution
Our system seamlessly integrates:
1. **ML Prediction**: A robust gradient-boosted tree (XGBoost) predicting raw fraud probability based on transaction features.
2. **Risk Engine**: Converts the probability into a 0-100 score and applies policy thresholds (LOW, MEDIUM, HIGH).
3. **AI Investigation**: Grounds the prediction in factual data using deterministic fallback logic or an LLM to explain *why* a transaction was flagged, without hallucinating unsupported claims.

## Features
* FastAPI-based REST API for seamless integration.
* Streamlit Dashboard for real-time transaction analysis and batch analytics.
* Configurable Business Rules / Risk Policy Engine.
* Explanatory AI layer with safe, grounded prompts.
* Local SQLite historical auditing.

## Architecture

![Architecture Diagram](docs/architecture.png)

## Technology Stack
* Python 3.11+
* FastAPI (Backend API)
* Streamlit (Frontend Dashboard)
* XGBoost & Scikit-Learn (ML Pipeline)
* Pandas & Numpy (Data manipulation)
* Plotly (Visualizations)
* SQLite (Local history)

## Machine Learning
* **Dataset:** Anonymized transaction dataset utilizing PCA features (`V1-V28`) alongside `Amount` and `Time`.
* **Preprocessing:** Uses `SimpleImputer` and `RobustScaler` within a `scikit-learn` Pipeline to prevent data leakage. Extracts `HourOfDay` and `LogAmount`.
* **Models Compared:** Dummy baseline vs. Logistic Regression vs. XGBoost.
* **Final Model:** XGBoost Classifier optimized for high-imbalance precision/recall tradeoff.
* **Evaluation Methodology:** Evaluated on a strictly untouched 20% held-out test set.
* **Actual Metrics (from test set):**
  - Accuracy: 0.9996
  - Precision: 0.9412
  - Recall: 0.8250
  - F1-Score: 0.8793
  - ROC-AUC: 0.9845

## Risk Policy
The engine classifies risk deterministically based on probability thresholds:
* **LOW (0 - 30):** → APPROVE
* **MEDIUM (31 - 70):** → ADDITIONAL VERIFICATION
* **HIGH (71 - 100):** → FLAG FOR REVIEW

*(Note: These thresholds are configurable prototype policies and do not represent production fraud rules.)*

## AI Investigation
The AI layer provides a textual explanation of the Risk Engine's decision. It uses strict LLM prompting to prevent hallucinations (e.g., it will not invent "device geolocation" since the dataset only provides abstract PCA features). If the LLM API is unavailable, it gracefully defaults to deterministic fallback logic, ensuring the core risk manager always remains operational.

## API Documentation
The backend exposes the following endpoints (available interactively at `http://localhost:8000/docs`):

* `GET /api/v1/risk/health` - Check model and API readiness.
* `POST /api/v1/risk/analyze` - Submit transaction data and receive a Risk Assessment.
* `POST /api/v1/risk/investigate` - Generate an explainable AI investigation report.
* `GET /api/v1/risk/history` - Retrieve recent transaction logs.
* `GET /api/v1/risk/analytics` - Retrieve aggregate statistics.

## Installation

1. Clone the repository
2. Set up a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
   Add your API keys to `.env` if utilizing LLM explainability.

## Running the Application
Launch both the backend and frontend simultaneously:
```bash
python run.py
```
* **FastAPI:** `http://localhost:8000/docs`
* **Streamlit:** `http://localhost:8501`

## Testing
Run the complete automated test suite:
```bash
pytest
```
*Result: 19 passed.*

## Limitations
* Dataset relies on anonymized PCA features, preventing rich behavioral explanations.
* This prototype is not a production payment gateway and does not perform actual payment authorizations.
* The AI investigation explains the model's logic but does not establish definitive ground-truth fraud.

## Future Improvements
* Real-time Kafka transaction streaming.
* Device fingerprinting and graph-based behavioral detection.
* Integration with explainable ML libraries (e.g., SHAP).
* Model drift detection monitoring.
* Human-in-the-loop review workflow UI.
