import pytest
from backend.services.graph_engine import GraphEngine

@pytest.fixture
def graph():
    g = GraphEngine()
    g.G.clear() # Clear in-memory graph
    return g

def test_add_transaction_relationships(graph):
    graph.add_transaction_relationships("TX-1", "CUS-1", "DEV-1", "IP-1", "PAY-1")
    
    assert f"CUST_CUS-1" in graph.G
    assert f"TX_TX-1" in graph.G
    
    # 5 nodes total (Cust, Tx, Dev, IP, Pay)
    assert len(graph.G.nodes) == 5

def test_calculate_graph_risk_no_shared(graph):
    graph.add_transaction_relationships("TX-1", "CUS-1", "DEV-1")
    avail, metrics = graph.calculate_graph_risk("CUS-1", "DEV-1")
    assert avail is True
    assert metrics.graph_risk_score == 0
    assert metrics.graph_risk_level == "LOW"
    assert metrics.cluster_size == 1

def test_calculate_graph_risk_shared_device(graph):
    graph.add_transaction_relationships("TX-1", "CUS-1", "DEV-1")
    graph.add_transaction_relationships("TX-2", "CUS-2", "DEV-1")
    
    avail, metrics = graph.calculate_graph_risk("CUS-1", "DEV-1")
    assert avail is True
    assert metrics.cluster_size == 2
    assert metrics.graph_risk_score >= 30 # At least 30 for shared device
    assert metrics.graph_risk_level in ["LOW", "MEDIUM"]

def test_calculate_graph_risk_fraud_ring(graph):
    graph.add_transaction_relationships("TX-1", "CUS-1", "DEV-1", "IP-1")
    graph.add_transaction_relationships("TX-2", "CUS-2", "DEV-1", "IP-1")
    graph.add_transaction_relationships("TX-3", "CUS-3", "DEV-1", "IP-1")
    
    avail, metrics = graph.calculate_graph_risk("CUS-1", "DEV-1", "IP-1")
    assert avail is True
    assert metrics.cluster_size == 3
    # Shared device (30) + Shared IP (20) + Large Cluster (20) = 70
    assert metrics.graph_risk_score >= 70
    assert metrics.graph_risk_level in ["MEDIUM", "HIGH"]
    assert metrics.cluster_id is not None
