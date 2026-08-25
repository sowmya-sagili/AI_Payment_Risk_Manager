import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "history.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
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
    ''')
    conn.commit()
    conn.close()

def save_transaction(tx_id, amount, prob, score, level, action):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO risk_history (transaction_id, amount, risk_probability, risk_score, risk_level, recommended_action)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (tx_id, amount, prob, score, level, action))
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
