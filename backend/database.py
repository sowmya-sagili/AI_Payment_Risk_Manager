import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "history.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS risk_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount REAL,
            risk_probability REAL,
            risk_score INTEGER,
            risk_level TEXT,
            recommended_action TEXT
        )
    """)
    
    # Safe migrations
    columns = [row[1] for row in cursor.execute("PRAGMA table_info(risk_history)").fetchall()]
    for col in ['customer_id', 'velocity_level', 'velocity_signals', 'decision_mode', 'decision_reason', 'triggered_rules', 'rule_version']:
        if col not in columns:
            cursor.execute(f"ALTER TABLE risk_history ADD COLUMN {col} TEXT")
    
    for col in ['velocity_score', 'final_risk_score', 'velocity_available']:
        if col not in columns:
            cursor.execute(f"ALTER TABLE risk_history ADD COLUMN {col} INTEGER")
            
    for col in ['ml_weight', 'velocity_weight', 'graph_weight', 'graph_score']:
        if col not in columns:
            cursor.execute(f"ALTER TABLE risk_history ADD COLUMN {col} REAL")

    # Graph Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_hash TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_entity TEXT,
            target_entity TEXT,
            relationship_type TEXT,
            transaction_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_entity, target_entity, transaction_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_clusters (
            cluster_id TEXT PRIMARY KEY,
            cluster_size INTEGER,
            graph_risk_score INTEGER,
            graph_risk_level TEXT,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graph_risk_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            customer_id TEXT,
            graph_risk_score INTEGER,
            graph_risk_level TEXT,
            signals TEXT,
            cluster_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
        
    conn.commit()
    conn.close()

def save_transaction(tx_id, amount, prob, score, level, action, 
                     customer_id=None, velocity_score=None, velocity_level=None, 
                     final_risk_score=None, velocity_signals=None, velocity_available=None,
                     graph_score=None, ml_weight=None, velocity_weight=None, graph_weight=None,
                     decision_mode="NORMAL", decision_reason="", triggered_rules=None, rule_version="1.0.0"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    import json
    signals_str = json.dumps(velocity_signals) if velocity_signals else None
    rules_str = json.dumps(triggered_rules) if triggered_rules else None
    
    cursor.execute("""
        INSERT INTO risk_history (
            transaction_id, amount, risk_probability, risk_score, risk_level, recommended_action,
            customer_id, velocity_score, velocity_level, final_risk_score, velocity_signals, velocity_available,
            graph_score, ml_weight, velocity_weight, graph_weight, decision_mode, decision_reason, triggered_rules, rule_version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, amount, prob, score, level, action, customer_id, velocity_score, velocity_level, final_risk_score, signals_str, velocity_available,
            graph_score, ml_weight, velocity_weight, graph_weight, decision_mode, decision_reason, rules_str, rule_version))
    conn.commit()
    conn.close()

def get_history(limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM risk_history ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_analytics():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute('SELECT COUNT(*) as total, AVG(amount) as avg_amt, AVG(risk_score) as avg_score FROM risk_history')
    row = cursor.fetchone()
    stats['total_transactions'] = row['total'] or 0
    stats['average_amount'] = row['avg_amt'] or 0.0
    stats['average_risk_score'] = row['avg_score'] or 0.0
    
    cursor.execute('SELECT risk_level, COUNT(*) as count FROM risk_history GROUP BY risk_level')
    level_counts = cursor.fetchall()
    stats['levels'] = {r['risk_level']: r['count'] for r in level_counts}
    
    conn.close()
    return stats
