import networkx as nx
import sqlite3
import hashlib
import json
import uuid
from backend.config import settings
from backend.database import DB_PATH
from backend.schemas.risk import GraphRiskMetrics, GraphSignal
from typing import Tuple, List, Dict, Any, Optional

class GraphEngine:
    def __init__(self):
        self.enabled = getattr(settings, 'GRAPH_ENABLED', True)
        self.G = nx.Graph()
        self._load_graph_from_db()

    def _load_graph_from_db(self):
        if not self.enabled:
            return
            
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Load entities
            cursor.execute("SELECT entity_hash, entity_type FROM graph_entities")
            for e_hash, e_type in cursor.fetchall():
                self.G.add_node(e_hash, type=e_type)
                
            # Load relationships
            cursor.execute("SELECT source_entity, target_entity, relationship_type FROM graph_relationships")
            for src, tgt, rel in cursor.fetchall():
                self.G.add_edge(src, tgt, type=rel)
                
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to load graph from DB: {e}")

    def _hash(self, value: str) -> str:
        if not value:
            return ""
        return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]

    def add_transaction_relationships(self, tx_id: str, cust_id: str, device_id: str = None, ip_address: str = None, payment_acct: str = None):
        if not self.enabled:
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        tx_node = f"TX_{tx_id}"
        cust_node = f"CUST_{cust_id}"
        
        entities = [
            (tx_node, "TRANSACTION"),
            (cust_node, "CUSTOMER")
        ]
        
        edges = [
            (cust_node, tx_node, "CUSTOMER->TRANSACTION")
        ]
        
        if device_id:
            dev_node = f"DEV_{self._hash(device_id)}"
            entities.append((dev_node, "DEVICE"))
            edges.append((cust_node, dev_node, "CUSTOMER->DEVICE"))
            edges.append((tx_node, dev_node, "TRANSACTION->DEVICE"))
            
        if ip_address:
            ip_node = f"IP_{self._hash(ip_address)}"
            entities.append((ip_node, "IP"))
            edges.append((cust_node, ip_node, "CUSTOMER->IP"))
            edges.append((tx_node, ip_node, "TRANSACTION->IP"))
            
        if payment_acct:
            pay_node = f"PAY_{self._hash(payment_acct)}"
            entities.append((pay_node, "PAYMENT_ACCOUNT"))
            edges.append((cust_node, pay_node, "CUSTOMER->PAYMENT_ACCOUNT"))
            edges.append((tx_node, pay_node, "TRANSACTION->PAYMENT_ACCOUNT"))
            
        # Insert into graph
        for e_hash, e_type in entities:
            self.G.add_node(e_hash, type=e_type)
            try:
                cursor.execute("INSERT OR IGNORE INTO graph_entities (entity_type, entity_hash) VALUES (?, ?)", (e_type, e_hash))
            except Exception:
                pass
                
        for src, tgt, rel in edges:
            self.G.add_edge(src, tgt, type=rel)
            try:
                cursor.execute("INSERT OR IGNORE INTO graph_relationships (source_entity, target_entity, relationship_type, transaction_id) VALUES (?, ?, ?, ?)", (src, tgt, rel, tx_id))
            except Exception:
                pass
                
        conn.commit()
        conn.close()

    def get_connected_component(self, cust_node: str) -> set:
        if cust_node not in self.G:
            return set()
        return nx.node_connected_component(self.G, cust_node)

    def calculate_graph_risk(self, cust_id: str, device_id: str = None, ip_address: str = None, payment_acct: str = None) -> Tuple[bool, GraphRiskMetrics]:
        if not self.enabled:
            return False, GraphRiskMetrics(graph_risk_score=0, graph_risk_level="UNKNOWN")
            
        if not device_id and not ip_address and not payment_acct:
            return False, GraphRiskMetrics(graph_risk_score=0, graph_risk_level="UNKNOWN")
            
        cust_node = f"CUST_{cust_id}"
        if cust_node not in self.G:
            return True, GraphRiskMetrics(graph_risk_score=0, graph_risk_level="LOW")
            
        component = self.get_connected_component(cust_node)
        
        # Analyze component
        customers_in_cluster = [n for n in component if self.G.nodes[n].get("type") == "CUSTOMER"]
        devices_in_cluster = [n for n in component if self.G.nodes[n].get("type") == "DEVICE"]
        ips_in_cluster = [n for n in component if self.G.nodes[n].get("type") == "IP"]
        
        score = 0
        signals = []
        
        if len(customers_in_cluster) > 1:
            # Check what they share
            shared_devices = []
            shared_ips = []
            shared_pays = []
            
            for n in component:
                if self.G.nodes[n].get("type") == "DEVICE":
                    linked_custs = [nbr for nbr in self.G.neighbors(n) if self.G.nodes[nbr].get("type") == "CUSTOMER"]
                    if len(linked_custs) > 1:
                        shared_devices.append(n)
                elif self.G.nodes[n].get("type") == "IP":
                    linked_custs = [nbr for nbr in self.G.neighbors(n) if self.G.nodes[nbr].get("type") == "CUSTOMER"]
                    if len(linked_custs) > 1:
                        shared_ips.append(n)
                elif self.G.nodes[n].get("type") == "PAYMENT_ACCOUNT":
                    linked_custs = [nbr for nbr in self.G.neighbors(n) if self.G.nodes[nbr].get("type") == "CUSTOMER"]
                    if len(linked_custs) > 1:
                        shared_pays.append(n)
                        
            if shared_devices:
                score += 30 * len(shared_devices)
                signals.append(GraphSignal(type="SHARED_DEVICE", severity="HIGH", description=f"Customer shares device(s) with {len(customers_in_cluster)-1} other customers"))
            if shared_ips:
                score += 20 * len(shared_ips)
                signals.append(GraphSignal(type="SHARED_IP", severity="MEDIUM", description=f"Customer shares IP(s) with {len(customers_in_cluster)-1} other customers"))
            if shared_pays:
                score += 40 * len(shared_pays)
                signals.append(GraphSignal(type="SHARED_PAYMENT", severity="HIGH", description=f"Customer shares payment account(s) with {len(customers_in_cluster)-1} other customers"))
                
            if len(customers_in_cluster) >= 3:
                score += 20
                signals.append(GraphSignal(type="LARGE_CLUSTER", severity="HIGH", description=f"Suspicious connected cluster of {len(customers_in_cluster)} customers detected"))
                
        # Cap score
        score = min(100, score)
        
        if score <= 30:
            level = "LOW"
        elif score <= 70:
            level = "MEDIUM"
        else:
            level = "HIGH"
            
        cluster_id = None
        if score > 0:
            # Hash the sorted list of customer nodes to get a stable cluster ID
            cluster_id = "CLUSTER-" + hashlib.sha256(",".join(sorted(customers_in_cluster)).encode('utf-8')).hexdigest()[:8]
            
        metrics = GraphRiskMetrics(
            graph_risk_score=score,
            graph_risk_level=level,
            cluster_id=cluster_id,
            cluster_size=len(customers_in_cluster),
            signals=signals
        )
        
        return True, metrics

    def get_customer_network(self, cust_id: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"error": "Graph engine disabled"}
            
        cust_node = f"CUST_{cust_id}"
        if cust_node not in self.G:
            return {"customer_id": cust_id, "nodes": [], "edges": []}
            
        comp = self.get_connected_component(cust_node)
        subgraph = self.G.subgraph(comp)
        
        nodes = []
        for n in subgraph.nodes():
            nodes.append({
                "id": n,
                "label": n.split("_")[0], # Type prefix
                "type": subgraph.nodes[n].get("type")
            })
            
        edges = []
        for u, v in subgraph.edges():
            edges.append({
                "source": u,
                "target": v,
                "type": subgraph.edges[u, v].get("type")
            })
            
        return {
            "customer_id": cust_id,
            "nodes": nodes,
            "edges": edges,
            "cluster_size": len([n for n in nodes if n["type"] == "CUSTOMER"])
        }

graph_engine = GraphEngine()
