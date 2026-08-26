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
            
        if getattr(assessment, 'velocity_score', None) is not None:
            findings.append(f"Velocity Score: {assessment.velocity_score} (Level: {assessment.velocity_level})")
            if assessment.velocity_signals:
                for sig in assessment.velocity_signals:
                    findings.append(f"Velocity Signal: {sig}")
                    
        if getattr(assessment, 'graph_score', None) is not None:
            findings.append(f"Graph Score: {assessment.graph_score} (Level: {assessment.graph_risk_level})")
            if assessment.cluster_id:
                findings.append(f"Part of Fraud Cluster: {assessment.cluster_id}")
            if assessment.graph_signals:
                for sig in assessment.graph_signals:
                    findings.append(f"Graph Signal [{sig.severity}]: {sig.description}")
                    
        if getattr(assessment, 'final_risk_score', None) is not None:
            findings.append(f"Final Aggregated Risk Score: {assessment.final_risk_score}")
            
        if request.top_risk_factors:
            for factor in request.top_risk_factors:
                findings.append(f"SHAP Explainer: {factor.feature_name} {factor.contribution.replace('_', ' ').lower()} (SHAP: {factor.shap_value:.2f})")
            
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
        shap_str = ""
        if request.top_risk_factors:
            shap_str = "\nTop model contributors:\n"
            for f in request.top_risk_factors:
                effect = "increased" if f.shap_value > 0 else "decreased"
                shap_str += f"- {f.feature_name} {effect} model risk (SHAP: {f.shap_value:.2f})\n"

        prompt = f"""
You are a financial risk investigation assistant. Explain the supplied ML risk assessment using ONLY the provided information. 
Do NOT invent customer history, device information, location, merchant behavior, payment method, or other unavailable facts. 
Clearly distinguish MODEL PREDICTION from BUSINESS RISK DECISION and AI EXPLANATION.
Never call the prediction "confirmed fraud." Use language like "high-risk prediction".
IMPORTANT: V1-V28 are anonymized PCA-transformed features. You MUST NOT invent real-world meanings for them. Say "{{"V14 was one of the strongest model contributors"}}" instead of "The customer's location caused the fraud."

Input Data:
Transaction Data: {json.dumps(request.transaction_data)}
Risk Level: {request.risk_assessment.risk_level}
Risk Score: {request.risk_assessment.risk_score}
Fraud Probability: {request.risk_assessment.risk_probability}
Recommended Action: {request.risk_assessment.recommended_action}
Risk Factors: {json.dumps(request.risk_assessment.risk_factors)}
{shap_str}

Velocity Score: {request.risk_assessment.velocity_score}
Velocity Level: {request.risk_assessment.velocity_level}
Velocity Signals: {json.dumps(request.risk_assessment.velocity_signals) if request.risk_assessment.velocity_signals else "[]"}
Velocity Metrics: {request.risk_assessment.velocity_metrics.model_dump_json() if request.risk_assessment.velocity_metrics else "{}"}

Graph Risk Score: {request.risk_assessment.graph_score}
Graph Risk Level: {request.risk_assessment.graph_risk_level}
Cluster ID: {request.risk_assessment.cluster_id}
Graph Signals: {json.dumps([sig.model_dump() for sig in request.risk_assessment.graph_signals]) if request.risk_assessment.graph_signals else "[]"}

Final Risk Score: {request.risk_assessment.final_risk_score}
Final Risk Level: {request.risk_assessment.risk_level}
Decision Mode: {request.risk_assessment.decision_mode}
Decision Reason: {request.risk_assessment.decision_reason}
Triggered Rules: {json.dumps([r.model_dump() for r in request.risk_assessment.triggered_rules]) if request.risk_assessment.triggered_rules else "[]"}

CRITICAL INSTRUCTION:
The deterministic Decision Engine is the source of truth. Do not change the risk decision. You must explain the decision based on the provided decision_reason and triggered_rules. Never invent facts not supplied by the system.

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
