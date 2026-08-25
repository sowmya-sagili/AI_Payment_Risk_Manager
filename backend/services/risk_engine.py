from backend.config import settings
from backend.schemas.risk import RiskAssessmentResponse
from typing import Dict, Any

class RiskEngine:
    def __init__(self):
        self.low_max = settings.RISK_THRESHOLD_LOW_MAX
        self.medium_max = settings.RISK_THRESHOLD_MEDIUM_MAX

    def determine_risk_level_and_action(self, risk_score: int) -> tuple[str, str]:
        if risk_score <= self.low_max:
            return "LOW", "APPROVE"
        elif risk_score <= self.medium_max:
            return "MEDIUM", "ADDITIONAL_VERIFICATION"
        else:
            return "HIGH", "FLAG_FOR_REVIEW"

    def determine_risk_factors(self, risk_probability: float, risk_score: int) -> list[str]:
        factors = []
        if risk_score > self.medium_max:
            factors.append("High model-predicted fraud probability")
            factors.append("Risk score above configured threshold")
        
        # We add basic technical risk factors
        factors.append(f"Model confidence/probability: {risk_probability:.4f}")
        return factors

    def assess_transaction(
        self, 
        transaction_id: str, 
        risk_probability: float, 
        risk_score: int, 
        model_name: str = "XGBoost", 
        model_version: str = "1.0"
    ) -> RiskAssessmentResponse:
        
        risk_level, recommended_action = self.determine_risk_level_and_action(risk_score)
        risk_factors = self.determine_risk_factors(risk_probability, risk_score)
        
        return RiskAssessmentResponse(
            transaction_id=transaction_id,
            risk_probability=risk_probability,
            risk_score=risk_score,
            risk_level=risk_level,
            recommended_action=recommended_action,
            model_name=model_name,
            model_version=model_version,
            risk_factors=risk_factors
        )
