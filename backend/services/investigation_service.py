import json
import requests
from backend.config import settings
from backend.schemas.risk import InvestigationRequest, InvestigationReport

class InvestigationService:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.api_base = settings.AI_API_BASE
        self.model = settings.AI_MODEL

    def _deterministic_fallback(self, request: InvestigationRequest) -> InvestigationReport:
        assessment = request.risk_assessment
        
        findings = []
        if assessment.risk_level == "HIGH":
            eval_text = f"The trained model assigned a high fraud probability of {assessment.risk_probability*100:.0f}%. Based on the configured risk policy, the transaction is classified as HIGH risk and recommended for manual review."
            findings.append("Model probability exceeds the configured high-risk threshold.")
            findings.append("The transaction has been classified as HIGH risk.")
        elif assessment.risk_level == "MEDIUM":
            eval_text = f"The trained model assigned a fraud probability of {assessment.risk_probability*100:.0f}%. Based on the configured thresholds, the transaction is classified as MEDIUM risk and recommended for additional verification."
            findings.append("Model probability falls in the medium-risk threshold range.")
        else:
            eval_text = f"The trained model assigned a fraud probability of {assessment.risk_probability*100:.0f}%. Based on the configured thresholds, the transaction is classified as LOW risk and recommended for approval."
            findings.append("Model probability is within the normal low-risk threshold.")
            
        # Add risk factors as findings
        for factor in assessment.risk_factors:
            findings.append(f"Model factor: {factor}")
            
        return InvestigationReport(
            transaction_id=assessment.transaction_id,
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level,
            fraud_probability=assessment.risk_probability,
            assessment=eval_text,
            key_findings=findings,
            recommended_action=assessment.recommended_action,
            confidence_note="This assessment is based deterministically on the trained ML model and available transaction features.",
            disclaimer="This is a risk-assessment recommendation and not a definitive fraud determination."
        )

    def _call_llm(self, request: InvestigationRequest) -> InvestigationReport:
        prompt = f"""
You are a financial risk investigation assistant. Explain the supplied ML risk assessment using ONLY the provided information. 
Do NOT invent customer history, device information, location, merchant behavior, payment method, or other unavailable facts. 
Clearly distinguish MODEL PREDICTION from BUSINESS RISK DECISION and AI EXPLANATION.
Never call the prediction "confirmed fraud." Use language like "high-risk prediction".

Input Data:
Transaction Data: {json.dumps(request.transaction_data)}
Risk Level: {request.risk_assessment.risk_level}
Risk Score: {request.risk_assessment.risk_score}
Fraud Probability: {request.risk_assessment.risk_probability}
Recommended Action: {request.risk_assessment.recommended_action}
Risk Factors: {json.dumps(request.risk_assessment.risk_factors)}

Return a JSON object matching this schema exactly:
{{
    "transaction_id": "{request.transaction_id}",
    "risk_score": {request.risk_assessment.risk_score},
    "risk_level": "{request.risk_assessment.risk_level}",
    "fraud_probability": {request.risk_assessment.risk_probability},
    "assessment": "String describing the overall assessment",
    "key_findings": ["String finding 1", "String finding 2"],
    "recommended_action": "{request.risk_assessment.recommended_action}",
    "confidence_note": "String describing confidence",
    "disclaimer": "This is a risk-assessment recommendation and not a definitive fraud determination."
}}
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful JSON-producing assistant."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        response = requests.post(f"{self.api_base}/chat/completions", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        parsed_json = json.loads(content)
        return InvestigationReport(**parsed_json)

    def investigate(self, request: InvestigationRequest) -> InvestigationReport:
        if not self.api_key:
            return self._deterministic_fallback(request)
            
        try:
            return self._call_llm(request)
        except Exception as e:
            print(f"LLM API Failed: {e}. Using fallback.")
            return self._deterministic_fallback(request)
