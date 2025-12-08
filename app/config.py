"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
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
    
    # CORS Settings
    allowed_origins: list[str] = [
        "http://localhost:8080",
        "http://localhost:3000",
        "https://checkinc.onrender.com"  # Tu dominio de producción
    ]
    
    # ML Model Settings
    model_path: str = "./models/glucose_model.pkl"
    min_training_samples: int = 30  # Mínimo de lecturas para entrenar modelo
    prediction_horizon_hours: int = 24  # Máximo de horas a predecir
    
    # Security
    api_key: Optional[str] = None  # Opcional: para autenticación adicional
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
settings = Settings()
