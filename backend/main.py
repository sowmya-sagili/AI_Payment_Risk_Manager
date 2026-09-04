# Terminal 1 — Backend (FastAPI)
# cd D:\Razorpay\ai-payment-risk-manager
# .\venv\Scripts\Activate.ps1
# python -m uvicorn backend.main:app --reload --port 8000

# Backend:

# API → http://localhost:8000
# Swagger → http://localhost:8000/docs
# Health → http://localhost:8000/api/v1/risk/health
# Terminal 2 — Frontend (Streamlit)

# Open a NEW PowerShell terminal, then:
# Frontend

# cd D:\Razorpay\ai-payment-risk-manager
# .\venv\Scripts\Activate.ps1
# python -m streamlit run frontend/app.py --server.port 8501

# Frontend:

# http://localhost:8501
# 🧪 Optional — Run all tests
# cd D:\Razorpay\ai-payment-risk-manager
# .\venv\Scripts\Activate.ps1
# $env:PYTHONPATH = (Get-Location).Path
# python -m pytest -q

# Expected:

# 53 passed

from fastapi import FastAPI, HTTPException
import os
import sys

# Ensure project root is in path for ml imports to work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schemas.risk import TransactionRequest, RiskAssessmentResponse, InvestigationRequest, InvestigationReport, RiskExplanation
from backend.services.risk_engine import RiskEngine
from backend.services.investigation_service import InvestigationService
from backend.services.velocity_engine import velocity_engine
from backend.services.graph_engine import graph_engine
from backend.services.decision_engine import decision_engine
from backend.database import init_db
from ml.predict import RiskPredictor

app = FastAPI(
    title="AI Payment Risk Manager API",
    description="Backend API for the AI-powered payment risk management system.",
    version="1.0.0"
)

# Initialize database
init_db()

# Initialize services
try:
    predictor = RiskPredictor()
except Exception as e:
    print(f"Warning: Could not load ML model: {e}")
    predictor = None

risk_engine = RiskEngine()
investigation_service = InvestigationService()

@app.get("/health")
async def health_check():
    """
    Basic health-check endpoint.
    """
    return {
        "status": "healthy",
        "service": "AI Payment Risk Manager"
    }

@app.get("/api/v1/risk/health")
async def risk_health_check():
    """
    Check if the ML model and risk engine are ready.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded. Train the model first.")
    return {"status": "ready"}

@app.post("/api/v1/risk/analyze", response_model=RiskAssessmentResponse)
async def analyze_transaction(transaction: TransactionRequest):
    """
    Analyze a transaction and return a risk assessment.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded. Train the model first.")
        
    try:
        # Convert request to dict, including extra fields (like V1-V28)
        tx_dict = transaction.model_dump()
        
        # Predict risk using ML model
        prediction_result = predictor.predict_risk(tx_dict)
        
        # Velocity Engine
        tx_id = tx_dict.get("transaction_id", "UNKNOWN")
        customer_id = tx_dict.get("customer_id")
        if not customer_id:
            customer_id = f"anonymous:{tx_id}"
            
        vel_avail, vel_score, vel_level, vel_metrics, vel_signals = velocity_engine.check_velocity(
            customer_id=customer_id,
            transaction_id=tx_id,
            amount=tx_dict.get("Amount", 0.0)
        )
        
        device_id = tx_dict.get("device_id")
        ip_address = tx_dict.get("ip_address")
        payment_account_id = tx_dict.get("payment_account_id")
        
        graph_engine.add_transaction_relationships(tx_id, customer_id, device_id, ip_address, payment_account_id)
        graph_avail, graph_metrics = graph_engine.calculate_graph_risk(customer_id, device_id, ip_address, payment_account_id)
        
        
        g_s = graph_metrics.graph_risk_score if graph_avail else 0
        
        # Run Decision Engine
        final_score, final_level, action, mode, rules, reason, w_ml, w_vel, w_grph = decision_engine.evaluate(
            ml_score=prediction_result["risk_score"],
            velocity_score=vel_score,
            velocity_available=vel_avail,
            graph_score=g_s,
            graph_available=graph_avail
        )
        
        from backend.schemas.risk import RiskAssessmentResponse
        assessment = RiskAssessmentResponse(
            transaction_id=tx_id,
            customer_id=customer_id,
            risk_probability=prediction_result["risk_probability"],
            risk_score=prediction_result["risk_score"],
            velocity_score=vel_score if vel_avail else None,
            velocity_level=vel_level if vel_avail else None,
            velocity_metrics=vel_metrics if vel_avail else None,
            velocity_signals=vel_signals if vel_avail else None,
            graph_score=g_s if graph_avail else None,
            graph_risk_level=graph_metrics.graph_risk_level if graph_avail else None,
            cluster_id=graph_metrics.cluster_id if graph_avail else None,
            graph_signals=graph_metrics.signals if graph_avail else None,
            final_risk_score=final_score,
            risk_level=final_level,
            recommended_action=action,
            ml_weight=w_ml,
            velocity_weight=w_vel,
            graph_weight=w_grph,
            decision_mode=mode,
            decision_reason=reason,
            triggered_rules=rules,
            model_name="XGBoost",
            model_version="1.0",
            risk_factors=risk_engine.determine_risk_factors(prediction_result["risk_probability"], final_score)
        )
        
        # Save to database
        from backend.database import save_transaction
        save_transaction(
            tx_id=assessment.transaction_id,
            amount=tx_dict.get("Amount", 0.0),
            prob=assessment.risk_probability,
            score=assessment.risk_score,
            level=assessment.risk_level,
            action=assessment.recommended_action,
            customer_id=assessment.customer_id,
            velocity_score=assessment.velocity_score,
            velocity_level=assessment.velocity_level,
            final_risk_score=assessment.final_risk_score,
            velocity_signals=assessment.velocity_signals,
            velocity_available=1 if vel_avail else 0,
            graph_score=assessment.graph_score,
            ml_weight=assessment.ml_weight,
            velocity_weight=assessment.velocity_weight,
            graph_weight=assessment.graph_weight,
            decision_mode=assessment.decision_mode,
            decision_reason=assessment.decision_reason,
            triggered_rules=[r.model_dump() for r in assessment.triggered_rules] if assessment.triggered_rules else []
        )
        
        return assessment
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Prediction error occurred.")


@app.post("/api/v1/risk/explain", response_model=RiskExplanation)
async def explain_transaction(transaction: TransactionRequest):
    if predictor is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded.")
    try:
        from backend.services.explanation_service import explanation_service
        import pandas as pd
        
        tx_dict = transaction.model_dump()
        prediction_result = predictor.predict_risk(tx_dict)
        
                # Velocity Engine
        tx_id = tx_dict.get("transaction_id", "UNKNOWN")
        customer_id = tx_dict.get("customer_id")
        if not customer_id:
            customer_id = f"anonymous:{tx_id}"
            
        vel_avail, vel_score, vel_level, vel_metrics, vel_signals = velocity_engine.check_velocity(
            customer_id=customer_id,
            transaction_id=tx_id,
            amount=tx_dict.get("Amount", 0.0)
        )
        
        device_id = tx_dict.get("device_id")
        ip_address = tx_dict.get("ip_address")
        payment_account_id = tx_dict.get("payment_account_id")
        
        graph_engine.add_transaction_relationships(tx_id, customer_id, device_id, ip_address, payment_account_id)
        graph_avail, graph_metrics = graph_engine.calculate_graph_risk(customer_id, device_id, ip_address, payment_account_id)
        
        
        g_s = graph_metrics.graph_risk_score if graph_avail else 0
        
        # Run Decision Engine
        final_score, final_level, action, mode, rules, reason, w_ml, w_vel, w_grph = decision_engine.evaluate(
            ml_score=prediction_result["risk_score"],
            velocity_score=vel_score,
            velocity_available=vel_avail,
            graph_score=g_s,
            graph_available=graph_avail
        )
        
        from backend.schemas.risk import RiskAssessmentResponse
        assessment = RiskAssessmentResponse(
            transaction_id=tx_id,
            customer_id=customer_id,
            risk_probability=prediction_result["risk_probability"],
            risk_score=prediction_result["risk_score"],
            velocity_score=vel_score if vel_avail else None,
            velocity_level=vel_level if vel_avail else None,
            velocity_metrics=vel_metrics if vel_avail else None,
            velocity_signals=vel_signals if vel_avail else None,
            graph_score=g_s if graph_avail else None,
            graph_risk_level=graph_metrics.graph_risk_level if graph_avail else None,
            cluster_id=graph_metrics.cluster_id if graph_avail else None,
            graph_signals=graph_metrics.signals if graph_avail else None,
            final_risk_score=final_score,
            risk_level=final_level,
            recommended_action=action,
            ml_weight=w_ml,
            velocity_weight=w_vel,
            graph_weight=w_grph,
            decision_mode=mode,
            decision_reason=reason,
            triggered_rules=rules,
            model_name="XGBoost",
            model_version="1.0",
            risk_factors=risk_engine.determine_risk_factors(prediction_result["risk_probability"], final_score)
        )
        
        preprocessed_X = predictor.last_X
        original_df = predictor.last_df
        
        top_factors = explanation_service.explain(preprocessed_X, original_df)
        
        from backend.schemas.risk import RiskExplanation, RiskFactor
        factors = [RiskFactor(**f) for f in top_factors]
        
        return RiskExplanation(
            transaction_id=assessment.transaction_id,
            risk_probability=assessment.risk_probability,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level,
            model_name=assessment.model_name,
            model_version=assessment.model_version,
            top_contributors=factors
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Explanation error occurred.")

@app.get("/api/v1/risk/history")
async def get_risk_history(limit: int = 50):
    from backend.database import get_history
    return get_history(limit=limit)

@app.get("/api/v1/risk/analytics")
async def get_risk_analytics():
    from backend.database import get_analytics
    return get_analytics()

@app.post("/api/v1/risk/investigate", response_model=InvestigationReport)
async def investigate_transaction(transaction: TransactionRequest):
    """
    Run the risk assessment and generate a detailed AI investigation report.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="ML model is not loaded. Train the model first.")
        
    try:
        tx_dict = transaction.model_dump()
        prediction_result = predictor.predict_risk(tx_dict)
        
                # Velocity Engine
        tx_id = tx_dict.get("transaction_id", "UNKNOWN")
        customer_id = tx_dict.get("customer_id")
        if not customer_id:
            customer_id = f"anonymous:{tx_id}"
            
        vel_avail, vel_score, vel_level, vel_metrics, vel_signals = velocity_engine.check_velocity(
            customer_id=customer_id,
            transaction_id=tx_id,
            amount=tx_dict.get("Amount", 0.0)
        )
        
        device_id = tx_dict.get("device_id")
        ip_address = tx_dict.get("ip_address")
        payment_account_id = tx_dict.get("payment_account_id")
        
        graph_engine.add_transaction_relationships(tx_id, customer_id, device_id, ip_address, payment_account_id)
        graph_avail, graph_metrics = graph_engine.calculate_graph_risk(customer_id, device_id, ip_address, payment_account_id)
        
        
        g_s = graph_metrics.graph_risk_score if graph_avail else 0
        
        # Run Decision Engine
        final_score, final_level, action, mode, rules, reason, w_ml, w_vel, w_grph = decision_engine.evaluate(
            ml_score=prediction_result["risk_score"],
            velocity_score=vel_score,
            velocity_available=vel_avail,
            graph_score=g_s,
            graph_available=graph_avail
        )
        
        from backend.schemas.risk import RiskAssessmentResponse
        assessment = RiskAssessmentResponse(
            transaction_id=tx_id,
            customer_id=customer_id,
            risk_probability=prediction_result["risk_probability"],
            risk_score=prediction_result["risk_score"],
            velocity_score=vel_score if vel_avail else None,
            velocity_level=vel_level if vel_avail else None,
            velocity_metrics=vel_metrics if vel_avail else None,
            velocity_signals=vel_signals if vel_avail else None,
            graph_score=g_s if graph_avail else None,
            graph_risk_level=graph_metrics.graph_risk_level if graph_avail else None,
            cluster_id=graph_metrics.cluster_id if graph_avail else None,
            graph_signals=graph_metrics.signals if graph_avail else None,
            final_risk_score=final_score,
            risk_level=final_level,
            recommended_action=action,
            ml_weight=w_ml,
            velocity_weight=w_vel,
            graph_weight=w_grph,
            decision_mode=mode,
            decision_reason=reason,
            triggered_rules=rules,
            model_name="XGBoost",
            model_version="1.0",
            risk_factors=risk_engine.determine_risk_factors(prediction_result["risk_probability"], final_score)
        )
        
        # We don't necessarily need to save to DB here again if it was saved by analyze, 
        # but since investigate is a standalone POST, we'll save it or update it.
        # For this prototype, we'll just log it.
        from backend.database import save_transaction
        save_transaction(
            tx_id=assessment.transaction_id,
            amount=tx_dict.get("Amount", 0.0),
            prob=assessment.risk_probability,
            score=assessment.risk_score,
            level=assessment.risk_level,
            action=assessment.recommended_action,
            customer_id=assessment.customer_id,
            velocity_score=assessment.velocity_score,
            velocity_level=assessment.velocity_level,
            final_risk_score=assessment.final_risk_score,
            velocity_signals=assessment.velocity_signals,
            velocity_available=1 if vel_avail else 0,
            graph_score=assessment.graph_score,
            ml_weight=assessment.ml_weight,
            velocity_weight=assessment.velocity_weight,
            graph_weight=assessment.graph_weight,
            decision_mode=assessment.decision_mode,
            decision_reason=assessment.decision_reason,
            triggered_rules=[r.model_dump() for r in assessment.triggered_rules] if assessment.triggered_rules else []
        )
        
        # Calculate SHAP factors to enrich the AI investigation
        from backend.services.explanation_service import explanation_service
        preprocessed_X = predictor.last_X
        original_df = predictor.last_df
        top_factors = explanation_service.explain(preprocessed_X, original_df)
        
        from backend.schemas.risk import RiskFactor
        factors = [RiskFactor(**f) for f in top_factors]
        inv_req = InvestigationRequest(
            transaction_id=assessment.transaction_id,
            transaction_data=tx_dict,
            risk_assessment=assessment,
            top_risk_factors=factors
        )
        
        report = investigation_service.investigate(inv_req)
        return report
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        raise HTTPException(status_code=500, detail="Investigation error occurred.")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Payment Risk Manager API"}



@app.get("/api/v1/risk/graph/health")
async def graph_health_check():
    return {"status": "ready" if graph_engine.enabled else "disabled"}

@app.get("/api/v1/risk/graph/customer/{customer_id}")
async def get_customer_graph(customer_id: str):
    if not graph_engine.enabled:
        raise HTTPException(status_code=503, detail="Graph engine is disabled")
    return graph_engine.get_customer_network(customer_id)

@app.get("/api/v1/risk/graph/clusters")
async def get_clusters():
    # Helper to get all clusters
    if not graph_engine.enabled:
        raise HTTPException(status_code=503, detail="Graph engine is disabled")
    import sqlite3
    from backend.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM fraud_clusters ORDER BY detected_at DESC LIMIT 50")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        return []
    finally:
        conn.close()
        
@app.get("/api/v1/risk/graph/cluster/{cluster_id}")
async def get_cluster(cluster_id: str):
    if not graph_engine.enabled:
        raise HTTPException(status_code=503, detail="Graph engine is disabled")
    import sqlite3
    from backend.database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM fraud_clusters WHERE cluster_id = ?", (cluster_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Cluster not found")
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
