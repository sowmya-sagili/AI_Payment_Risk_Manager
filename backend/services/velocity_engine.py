import redis
import time
from backend.config import settings
from backend.schemas.risk import VelocityMetrics
from typing import Tuple, List

class VelocityEngine:
    def __init__(self):
        self.enabled = getattr(settings, 'REDIS_ENABLED', False)
        self.redis_client = None
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=getattr(settings, 'REDIS_HOST', 'localhost'),
                    port=getattr(settings, 'REDIS_PORT', 6379),
                    db=getattr(settings, 'REDIS_DB', 0),
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed. Velocity engine will operate in degraded mode. {e}")
                self.redis_client = None

    def check_velocity(self, customer_id: str, transaction_id: str, amount: float) -> Tuple[bool, int, str, VelocityMetrics, List[str]]:
        if not self.enabled or self.redis_client is None:
            return False, 0, "UNKNOWN", VelocityMetrics(), []
            
        current_time = time.time()
        
        # 1. Idempotency Check
        idemp_key = f"velocity:processed:{transaction_id}"
        if self.redis_client.get(idemp_key):
            # Already processed this exact transaction (maybe retry). Return cached or 0 impact.
            # We'll calculate current metrics without adding it again.
            return self._calculate_current_velocity(customer_id, current_time)
            
        # 2. Add transaction to ZSET
        zset_key = f"velocity:customer:{customer_id}:txs"
        member = f"{transaction_id}:{amount}"
        
        pipeline = self.redis_client.pipeline()
        pipeline.set(idemp_key, "1", ex=3600, nx=True) # Expiry 1 hour
        pipeline.zadd(zset_key, {member: current_time})
        pipeline.zremrangebyscore(zset_key, "-inf", current_time - 3600) # cleanup older than 1h
        pipeline.expire(zset_key, 3600)
        pipeline.execute()
        
        # 3. Calculate Velocity
        return self._calculate_current_velocity(customer_id, current_time)
        
    def _calculate_current_velocity(self, customer_id: str, current_time: float) -> Tuple[bool, int, str, VelocityMetrics, List[str]]:
        zset_key = f"velocity:customer:{customer_id}:txs"
        
        try:
            txs = self.redis_client.zrangebyscore(zset_key, current_time - 3600, current_time)
        except Exception:
            return False, 0, "UNKNOWN", VelocityMetrics(), []
            
        metrics = VelocityMetrics()
        
        for tx in txs:
            try:
                tx_id, amt_str = tx.split(":")
                amt = float(amt_str)
            except ValueError:
                continue
                
            tx_time = self.redis_client.zscore(zset_key, tx)
            if tx_time is None:
                continue
                
            diff = current_time - tx_time
            
            # 1 hour
            if diff <= 3600:
                metrics.transactions_1h += 1
                metrics.amount_1h += amt
            # 15 mins
            if diff <= 900:
                metrics.transactions_15m += 1
                metrics.amount_15m += amt
            # 5 mins
            if diff <= 300:
                metrics.transactions_5m += 1
                metrics.amount_5m += amt
            # 1 min
            if diff <= 60:
                metrics.transactions_1m += 1
                metrics.amount_1m += amt
                
        # Calculate score
        score = 0
        signals = []
        
        # 1-minute rules
        if metrics.transactions_1m >= 5:
            score += 40
            signals.append(f"Suspiciously high transaction frequency in the last 1 minute ({metrics.transactions_1m} txs)")
        elif metrics.transactions_1m >= 3:
            score += 20
            signals.append(f"Elevated transaction frequency in the last 1 minute ({metrics.transactions_1m} txs)")
            
        # 5-minute rules
        if metrics.transactions_5m >= 11:
            score += 30
            signals.append(f"Suspicious transaction volume in the last 5 minutes ({metrics.transactions_5m} txs)")
        elif metrics.transactions_5m >= 6:
            score += 15
            signals.append(f"Elevated transaction volume in the last 5 minutes ({metrics.transactions_5m} txs)")
            
        # 15-minute rules
        if metrics.transactions_15m >= 21:
            score += 20
            signals.append(f"Suspicious transaction volume in the last 15 minutes ({metrics.transactions_15m} txs)")
        elif metrics.transactions_15m >= 11:
            score += 10
            signals.append(f"Elevated transaction volume in the last 15 minutes ({metrics.transactions_15m} txs)")
            
        # Amount rules
        if metrics.amount_1h > 50000:
            score += 30
            signals.append(f"Unusually high transaction amount total in the last 1 hour ({metrics.amount_1h})")
        elif metrics.amount_1h > 10000:
            score += 10
            signals.append(f"Elevated transaction amount total in the last 1 hour ({metrics.amount_1h})")
            
        # Cap score at 100
        score = min(100, score)
        
        # Level
        if score <= 30:
            level = "LOW"
        elif score <= 70:
            level = "MEDIUM"
        else:
            level = "HIGH"
            
        return True, score, level, metrics, signals

velocity_engine = VelocityEngine()
