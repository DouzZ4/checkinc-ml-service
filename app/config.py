"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/checkinc_ml")
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "CheckInc ML Service"
    version: str = "1.0.0"
    
    # CORS Settings - Recibimos string crudo para evitar errores de JSON
    allowed_origins_raw: str = "*"

    @property
    def allowed_origins(self) -> list[str]:
        if self.allowed_origins_raw == "*":
            return ["*"]
        if self.allowed_origins_raw.startswith("["):
            try:
                import json
                return json.loads(self.allowed_origins_raw)
            except:
                pass
        return [url.strip() for url in self.allowed_origins_raw.split(",") if url.strip()]
    
    # ML Model Settings - Renombrado para evitar conflicto con Pydantic
    ml_model_path: str = "./models/glucose_model.pkl"
    min_training_samples: int = 30
    prediction_horizon_hours: int = 24
    
    # Security
    api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
        "protected_namespaces": ('settings_',) 
    }


# Singleton instance
settings = Settings()
