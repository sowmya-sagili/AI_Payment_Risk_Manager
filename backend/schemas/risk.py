from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., example="TX-1001")
    Amount: float = Field(..., example=150.50)
    Time: float = Field(..., example=3600.0)
    # Allows additional arbitrary V1-V28 fields, but Pydantic requires explicit or extra allowed
    
    class Config:
        extra = "allow"  # Allow V1-V28 or other features to be passed dynamically

class RiskAssessmentResponse(BaseModel):
    transaction_id: str
    risk_probability: float
    risk_score: int
    risk_level: str
    recommended_action: str
    model_name: str
    model_version: str
    risk_factors: List[str]

class InvestigationRequest(BaseModel):
    transaction_id: str
    transaction_data: Dict[str, Any]
    risk_assessment: RiskAssessmentResponse

class InvestigationReport(BaseModel):
    transaction_id: str
    risk_score: int
    risk_level: str
    fraud_probability: float
    assessment: str
    key_findings: List[str]
    recommended_action: str
    confidence_note: str
    disclaimer: str
