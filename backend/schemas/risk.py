from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., example="TX-1001")
    customer_id: Optional[str] = Field(None, example="CUST-1001")
    device_id: Optional[str] = Field(None, example="device-abc")
    ip_address: Optional[str] = Field(None, example="192.168.1.10")
    payment_account_id: Optional[str] = Field(None, example="account-xyz")
    Amount: float = Field(..., example=150.50)
    Time: float = Field(..., example=3600.0)
    # Allows additional arbitrary V1-V28 fields, but Pydantic requires explicit or extra allowed
    
    class Config:
        extra = "allow"  # Allow V1-V28 or other features to be passed dynamically

class VelocityMetrics(BaseModel):
    transactions_1m: int = 0
    transactions_5m: int = 0
    transactions_15m: int = 0
    transactions_1h: int = 0
    amount_1m: float = 0.0
    amount_5m: float = 0.0
    amount_15m: float = 0.0
    amount_1h: float = 0.0


class GraphSignal(BaseModel):
    type: str
    severity: str
    description: str

class GraphRiskMetrics(BaseModel):
    graph_risk_score: int
    graph_risk_level: str
    cluster_id: Optional[str] = None
    cluster_size: int = 1
    signals: List[GraphSignal] = []


class TriggeredRule(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    reason: str

class RiskAssessmentResponse(BaseModel):
    transaction_id: str
    customer_id: Optional[str] = None
    risk_probability: float
    risk_score: int
    velocity_score: Optional[int] = None
    velocity_level: Optional[str] = None
    velocity_metrics: Optional[VelocityMetrics] = None
    velocity_signals: Optional[List[str]] = None
    graph_score: Optional[int] = None
    graph_risk_level: Optional[str] = None
    cluster_id: Optional[str] = None
    graph_signals: Optional[List[GraphSignal]] = None
    final_risk_score: Optional[int] = None
    risk_level: str
    recommended_action: str
    
    ml_weight: Optional[float] = None
    velocity_weight: Optional[float] = None
    graph_weight: Optional[float] = None
    
    decision_mode: str = "NORMAL"
    decision_reason: str = ""
    triggered_rules: List[TriggeredRule] = []
    
    rule_version: str = "1.0.0"
    model_name: str
    model_version: str
    risk_factors: List[str]

class RiskFactor(BaseModel):
    feature_name: str
    feature_value: float
    shap_value: float
    contribution: str

class InvestigationRequest(BaseModel):
    transaction_id: str
    transaction_data: Dict[str, Any]
    risk_assessment: RiskAssessmentResponse
    top_risk_factors: Optional[List[RiskFactor]] = None

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


class RiskExplanation(BaseModel):
    transaction_id: str
    risk_probability: float
    risk_score: int
    risk_level: str
    model_name: str
    model_version: str
    top_contributors: List[RiskFactor]

class RiskAssessmentResponseWithFactors(RiskAssessmentResponse):
    top_risk_factors: List[RiskFactor] = []
