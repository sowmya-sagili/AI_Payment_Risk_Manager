import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    RULE_GRAPH_CRITICAL: int = 70
    RULE_VELOCITY_CRITICAL: int = 80
    RULE_ML_CRITICAL: int = 90
    RULE_COMBO_ML_VEL: int = 60
    RULE_COMBO_ML_GRAPH: int = 50
    RULE_COMBO_VEL_GRAPH: int = 60
    RULE_COMBO_ALL: int = 50
    RULE_VERSION: str = "1.0.0"
    GRAPH_ENABLED: bool = True
    ML_WEIGHT: float = 0.50
    VELOCITY_WEIGHT: float = 0.25
    GRAPH_WEIGHT: float = 0.25

    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = False

    PROJECT_NAME: str = "AI Payment Risk Manager"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Model Path
    MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "model", "model.joblib")
    
    # Risk Thresholds
    RISK_THRESHOLD_LOW_MAX: int = 30
    RISK_THRESHOLD_MEDIUM_MAX: int = 70
    
    # AI Provider settings
    AI_API_KEY: str | None = None
    AI_MODEL: str = "gpt-4o-mini"
    AI_API_BASE: str = "https://api.openai.com/v1"
    
    class Config:
        env_file = ".env"

settings = Settings()
