from typing import List, Optional
from pydantic import BaseModel
from backend.config import settings

class RiskRule(BaseModel):
    rule_id: str
    rule_name: str
    description: str
    enabled: bool = True
    severity: str
    action: str
    
def get_all_rules() -> List[RiskRule]:
    return [
        RiskRule(
            rule_id="GRAPH_CRITICAL",
            rule_name="Critical Fraud Network Risk",
            description="Graph risk score exceeded critical threshold.",
            severity="HIGH",
            action="FLAG_FOR_REVIEW"
        ),
        RiskRule(
            rule_id="VELOCITY_CRITICAL",
            rule_name="Critical Velocity Risk",
            description="Velocity risk score exceeded critical threshold.",
            severity="HIGH",
            action="ADDITIONAL_VERIFICATION"
        ),
        RiskRule(
            rule_id="ML_CRITICAL",
            rule_name="Critical ML Risk",
            description="Machine learning fraud probability exceeded critical threshold.",
            severity="HIGH",
            action="FLAG_FOR_REVIEW"
        ),
        RiskRule(
            rule_id="ML_VELOCITY_COMBINATION",
            rule_name="Combined ML and Velocity Risk",
            description="Both ML and velocity signals are elevated, indicating coordinated attack.",
            severity="HIGH",
            action="FLAG_FOR_REVIEW"
        ),
        RiskRule(
            rule_id="ML_GRAPH_COMBINATION",
            rule_name="Combined ML and Graph Risk",
            description="Both ML and network signals are elevated, indicating a sophisticated fraud ring.",
            severity="HIGH",
            action="FLAG_FOR_REVIEW"
        ),
        RiskRule(
            rule_id="VELOCITY_GRAPH_COMBINATION",
            rule_name="Combined Velocity and Graph Risk",
            description="Both velocity and network signals are elevated, indicating an active coordinated attack.",
            severity="HIGH",
            action="FLAG_FOR_REVIEW"
        ),
        RiskRule(
            rule_id="ALL_SIGNAL_COMBINATION",
            rule_name="Severe Multi-Vector Attack",
            description="All three risk vectors (ML, Velocity, Graph) are elevated simultaneously.",
            severity="HIGH",
            action="FLAG_FOR_REVIEW"
        )
    ]

def get_rule_by_id(rule_id: str) -> Optional[RiskRule]:
    for rule in get_all_rules():
        if rule.rule_id == rule_id:
            return rule
    return None
