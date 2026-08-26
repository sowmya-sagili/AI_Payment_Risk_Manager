from backend.services.risk_rules import get_all_rules, get_rule_by_id

def test_get_all_rules():
    rules = get_all_rules()
    assert len(rules) >= 7

def test_get_rule_by_id():
    rule = get_rule_by_id("GRAPH_CRITICAL")
    assert rule is not None
    assert rule.severity == "HIGH"
    
    rule = get_rule_by_id("NONEXISTENT")
    assert rule is None
