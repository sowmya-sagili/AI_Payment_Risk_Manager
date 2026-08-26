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
        model_version: str = "1.0",
        customer_id: str = None,
        velocity_score: int = None,
        velocity_level: str = None,
        velocity_metrics: Any = None,
        velocity_signals: list[str] = None,
        graph_score: int = None,
        graph_risk_level: str = None,
        cluster_id: str = None,
        graph_signals: Any = None,
        final_risk_score: int = None
    ) -> RiskAssessmentResponse:
        
        # Determine risk level based on final_risk_score if provided, else ML risk_score
        score_to_evaluate = final_risk_score if final_risk_score is not None else risk_score
        risk_level, recommended_action = self.determine_risk_level_and_action(score_to_evaluate)
        risk_factors = self.determine_risk_factors(risk_probability, score_to_evaluate)
        
        return RiskAssessmentResponse(
            transaction_id=transaction_id,
            customer_id=customer_id,
            risk_probability=risk_probability,
            risk_score=risk_score,
            velocity_score=velocity_score,
            velocity_level=velocity_level,
            velocity_metrics=velocity_metrics,
            velocity_signals=velocity_signals,
            graph_score=graph_score,
            graph_risk_level=graph_risk_level,
            cluster_id=cluster_id,
            graph_signals=graph_signals,
            final_risk_score=final_risk_score,
            risk_level=risk_level,
            recommended_action=recommended_action,
            model_name=model_name,
            model_version=model_version,
            risk_factors=risk_factors
        )
