from backend.config import settings
from backend.services.risk_rules import get_rule_by_id, RiskRule
from typing import Tuple, List, Dict, Any, Optional

class DecisionEngine:
    def __init__(self):
        self.ml_base_weight = getattr(settings, 'ML_WEIGHT', 0.50)
        self.vel_base_weight = getattr(settings, 'VELOCITY_WEIGHT', 0.25)
        self.grph_base_weight = getattr(settings, 'GRAPH_WEIGHT', 0.25)
        
        self.rule_graph_crit = getattr(settings, 'RULE_GRAPH_CRITICAL', 70)
        self.rule_vel_crit = getattr(settings, 'RULE_VELOCITY_CRITICAL', 80)
        self.rule_ml_crit = getattr(settings, 'RULE_ML_CRITICAL', 90)
        
        self.rule_combo_ml_vel = getattr(settings, 'RULE_COMBO_ML_VEL', 60)
        self.rule_combo_ml_graph = getattr(settings, 'RULE_COMBO_ML_GRAPH', 50)
        self.rule_combo_vel_graph = getattr(settings, 'RULE_COMBO_VEL_GRAPH', 60)
        self.rule_combo_all = getattr(settings, 'RULE_COMBO_ALL', 50)
        
        self.low_max = getattr(settings, 'RISK_THRESHOLD_LOW_MAX', 30)
        self.medium_max = getattr(settings, 'RISK_THRESHOLD_MEDIUM_MAX', 70)

    def evaluate(self, 
                 ml_score: int, 
                 velocity_score: int, velocity_available: bool, 
                 graph_score: int, graph_available: bool) -> Tuple[int, str, str, str, List[Dict], str, float, float, float]:
        
        # 1. Adaptive Weighting
        w_ml = self.ml_base_weight
        w_vel = self.vel_base_weight if velocity_available else 0.0
        w_grph = self.grph_base_weight if graph_available else 0.0
        
        total_w = w_ml + w_vel + w_grph
        w_ml /= total_w
        w_vel /= total_w
        w_grph /= total_w
        
        # Safe actual values (0 if unavailable)
        v_s = velocity_score if velocity_available else 0
        g_s = graph_score if graph_available else 0
        
        # 2. Normal Weighted Decision
        base_final_score = int(round((ml_score * w_ml) + (v_s * w_vel) + (g_s * w_grph)))
        base_final_score = max(0, min(100, base_final_score))
        
        if base_final_score <= self.low_max:
            base_level = "LOW"
            base_action = "APPROVE"
        elif base_final_score <= self.medium_max:
            base_level = "MEDIUM"
            base_action = "ADDITIONAL_VERIFICATION"
        else:
            base_level = "HIGH"
            base_action = "FLAG_FOR_REVIEW"
            
        triggered_rules = []
        final_score = base_final_score
        final_risk_level = base_level
        recommended_action = base_action
        decision_mode = "NORMAL"
        decision_reason = f"Transaction received a final risk score of {final_score} based on ML, velocity and graph signals. No critical rules were triggered."

        # Helper to format rule output
        def build_rule_out(r: RiskRule, reason: str):
            return {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "severity": r.severity,
                "reason": reason
            }

        # Priority 1: Circuit Breakers (evaluated sequentially to find highest priority)
        if graph_available and g_s >= self.rule_graph_crit:
            rule = get_rule_by_id("GRAPH_CRITICAL")
            if rule and rule.enabled:
                triggered_rules.append(build_rule_out(rule, "Graph risk score exceeded critical threshold"))
                
        if velocity_available and v_s >= self.rule_vel_crit:
            rule = get_rule_by_id("VELOCITY_CRITICAL")
            if rule and rule.enabled:
                triggered_rules.append(build_rule_out(rule, "Velocity risk score exceeded critical threshold"))
                
        if ml_score >= self.rule_ml_crit:
            rule = get_rule_by_id("ML_CRITICAL")
            if rule and rule.enabled:
                triggered_rules.append(build_rule_out(rule, "ML risk score exceeded critical threshold"))
                
        # Priority 2: Combination Rules (only check if no circuit breakers hit)
        if not triggered_rules:
            # Check ALL
            if velocity_available and graph_available and ml_score >= self.rule_combo_all and v_s >= self.rule_combo_all and g_s >= self.rule_combo_all:
                rule = get_rule_by_id("ALL_SIGNAL_COMBINATION")
                if rule and rule.enabled:
                    triggered_rules.append(build_rule_out(rule, "All three risk signals exceeded combination threshold"))
            # Check pairs
            elif velocity_available and ml_score >= self.rule_combo_ml_vel and v_s >= self.rule_combo_ml_vel:
                rule = get_rule_by_id("ML_VELOCITY_COMBINATION")
                if rule and rule.enabled:
                    triggered_rules.append(build_rule_out(rule, "Both ML and Velocity signals exceeded combination threshold"))
            elif graph_available and ml_score >= self.rule_combo_ml_graph and g_s >= self.rule_combo_ml_graph:
                rule = get_rule_by_id("ML_GRAPH_COMBINATION")
                if rule and rule.enabled:
                    triggered_rules.append(build_rule_out(rule, "Both ML and Graph signals exceeded combination threshold"))
            elif velocity_available and graph_available and v_s >= self.rule_combo_vel_graph and g_s >= self.rule_combo_vel_graph:
                rule = get_rule_by_id("VELOCITY_GRAPH_COMBINATION")
                if rule and rule.enabled:
                    triggered_rules.append(build_rule_out(rule, "Both Velocity and Graph signals exceeded combination threshold"))

        # Apply highest priority overrides
        if triggered_rules:
            # If any rule is triggered, find the maximum required action and severity
            # For simplicity, since all our critical/combo rules output HIGH / FLAG_FOR_REVIEW, we can enforce it.
            # But let's check the first triggered rule for its configured action
            first_rule = get_rule_by_id(triggered_rules[0]["rule_id"])
            if first_rule:
                final_risk_level = first_rule.severity
                recommended_action = first_rule.action
                
                if "CRITICAL" in first_rule.rule_id:
                    decision_mode = "CIRCUIT_BREAKER"
                    final_score = max(final_score, 85) # Ensure it has a high numerical value if overridden
                    # Build specific reason string
                    decision_reason = f"Transaction was classified as {final_risk_level} because the {first_rule.rule_id.split('_')[0].lower()} risk score exceeded the configured critical threshold. The weighted score was overridden by the {first_rule.rule_id} rule."
                else:
                    decision_mode = "RULE_OVERRIDE"
                    final_score = max(final_score, 75)
                    decision_reason = f"Transaction was classified as {final_risk_level} because multiple risk signals exceeded their combined-risk thresholds ({first_rule.rule_id})."
                    
        return final_score, final_risk_level, recommended_action, decision_mode, triggered_rules, decision_reason, w_ml, w_vel, w_grph

decision_engine = DecisionEngine()
