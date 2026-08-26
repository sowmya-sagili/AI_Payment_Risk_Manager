from backend.config import settings

class RiskAggregator:
    def __init__(self):
        self.ml_weight = getattr(settings, 'ML_WEIGHT', 0.50)
        self.velocity_weight = getattr(settings, 'VELOCITY_WEIGHT', 0.25)
        self.graph_weight = getattr(settings, 'GRAPH_WEIGHT', 0.25)

    def aggregate(self, ml_score: int, velocity_score: int = None, velocity_available: bool = False, graph_score: int = None, graph_available: bool = False) -> int:
        w_ml = self.ml_weight
        w_vel = self.velocity_weight if velocity_available else 0.0
        w_grph = self.graph_weight if graph_available else 0.0
        
        total_w = w_ml + w_vel + w_grph
        if total_w == 0:
            return ml_score
            
        w_ml /= total_w
        w_vel /= total_w
        w_grph /= total_w
        
        v_score = velocity_score if velocity_available and velocity_score is not None else 0
        g_score = graph_score if graph_available and graph_score is not None else 0
        
        final_score = (ml_score * w_ml) + (v_score * w_vel) + (g_score * w_grph)
        return int(round(final_score))

risk_aggregator = RiskAggregator()
