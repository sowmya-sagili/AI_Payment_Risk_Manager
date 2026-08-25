import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
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
