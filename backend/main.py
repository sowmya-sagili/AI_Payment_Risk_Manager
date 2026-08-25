from fastapi import FastAPI, HTTPException
import os
import sys

# Ensure project root is in path for ml imports to work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schemas.risk import TransactionRequest, RiskAssessmentResponse, InvestigationRequest, InvestigationReport
from backend.services.risk_engine import RiskEngine
from backend.services.investigation_service import InvestigationService
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
        
        # Assess risk using Risk Engine
        assessment = risk_engine.assess_transaction(
            transaction_id=tx_dict.get("transaction_id", "UNKNOWN"),
            risk_probability=prediction_result["risk_probability"],
            risk_score=prediction_result["risk_score"]
        )
        
        # Save to database
        from backend.database import save_transaction
        save_transaction(
            tx_id=assessment.transaction_id,
            amount=tx_dict.get("Amount", 0.0),
            prob=assessment.risk_probability,
            score=assessment.risk_score,
            level=assessment.risk_level,
            action=assessment.recommended_action
        )
        
        return assessment
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Prediction error occurred.")

@app.get("/api/v1/risk/history")
async def get_risk_history():
    from backend.database import get_history
    return get_history()

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
        
        assessment = risk_engine.assess_transaction(
            transaction_id=tx_dict.get("transaction_id", "UNKNOWN"),
            risk_probability=prediction_result["risk_probability"],
            risk_score=prediction_result["risk_score"]
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
            action=assessment.recommended_action
        )
        
        inv_req = InvestigationRequest(
            transaction_id=assessment.transaction_id,
            transaction_data=tx_dict,
            risk_assessment=assessment
        )
        
        report = investigation_service.investigate(inv_req)
        return report
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        raise HTTPException(status_code=500, detail="Investigation error occurred.")

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Payment Risk Manager API"}

