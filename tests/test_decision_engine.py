import pytest
from backend.services.decision_engine import DecisionEngine

def test_decision_engine_normal_weighted():
    engine = DecisionEngine()
    final_score, level, action, mode, rules, reason, w_ml, w_v, w_g = engine.evaluate(
        ml_score=20, velocity_score=20, velocity_available=True, graph_score=20, graph_available=True
    )
    
    assert mode == "NORMAL"
    assert len(rules) == 0
    assert final_score == 20
    assert level == "LOW"
    assert action == "APPROVE"

def test_decision_engine_adaptive_weights():
    engine = DecisionEngine()
    
    # Graph unavailable
    final_score, _, _, mode, _, _, w_ml, w_v, w_g = engine.evaluate(
        ml_score=100, velocity_score=0, velocity_available=True, graph_score=0, graph_available=False
    )
    
    # Expect ML to be ~0.66, Vel to be ~0.33
    assert w_g == 0.0
    assert round(w_ml, 2) == 0.67
    assert round(w_v, 2) == 0.33
    assert final_score == 85 # 100 * 0.67 + 0 * 0.33 = 67
    assert mode == "CIRCUIT_BREAKER" # because ML is 100 which triggers ML_CRITICAL (wait, we check score, yes ML=100)

def test_decision_engine_circuit_breaker():
    engine = DecisionEngine()
    final_score, level, action, mode, rules, reason, _, _, _ = engine.evaluate(
        ml_score=0, velocity_score=0, velocity_available=True, graph_score=80, graph_available=True
    )
    
    assert mode == "CIRCUIT_BREAKER"
    assert level == "HIGH"
    assert action == "FLAG_FOR_REVIEW"
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "GRAPH_CRITICAL"
    assert final_score >= 85 # ensure minimum override score

def test_decision_engine_combination():
    engine = DecisionEngine()
    final_score, level, action, mode, rules, reason, _, _, _ = engine.evaluate(
        ml_score=65, velocity_score=65, velocity_available=True, graph_score=0, graph_available=True
    )
    
    assert mode == "RULE_OVERRIDE"
    assert level == "HIGH"
    assert action == "FLAG_FOR_REVIEW"
    assert len(rules) == 1
    assert rules[0]["rule_id"] == "ML_VELOCITY_COMBINATION"
    assert final_score >= 75
