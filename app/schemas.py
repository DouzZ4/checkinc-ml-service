"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


# ============== Glucose Reading Schemas ==============

class GlucoseReadingBase(BaseModel):
    """Base schema for glucose reading"""
    user_id: int = Field(..., gt=0, description="User ID from Java application")
    glucose_level: float = Field(..., gt=0, lt=1000, description="Glucose level in mg/dL")
    timestamp: datetime = Field(..., description="When the reading was taken")
    moment_of_day: Optional[str] = Field(None, max_length=50, description="Context: 'En Ayuno', etc.")


class GlucoseReadingCreate(GlucoseReadingBase):
    """Schema for creating a new glucose reading"""
    pass


class GlucoseReadingResponse(GlucoseReadingBase):
    """Schema for glucose reading response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== Prediction Schemas ==============

class PredictionRequest(BaseModel):
    """Request schema for getting predictions"""
    user_id: int = Field(..., gt=0)
    hours_ahead: int = Field(6, ge=1, le=24, description="How many hours to predict (1-24)")
    
    @validator('hours_ahead')
    def validate_hours(cls, v):
        if v < 1 or v > 24:
            raise ValueError('hours_ahead must be between 1 and 24')
        return v


class PredictionPoint(BaseModel):
    """Single prediction point"""
    timestamp: datetime
    predicted_level: float
    confidence_score: Optional[float] = None


class PredictionResponse(BaseModel):
    """Response with multiple prediction points"""
    user_id: int
    predictions: List[PredictionPoint]
    model_version: str
    generated_at: datetime
    message: Optional[str] = None


# ============== Risk Assessment Schemas ==============

class RiskAssessmentRequest(BaseModel):
    """Request schema for risk assessment"""
    user_id: int = Field(..., gt=0)


class RiskAssessmentResponse(BaseModel):
    """Response with risk level and details"""
    user_id: int
    risk_level: str = Field(..., description="'bajo', 'medio', 'alto'")
    risk_score: float = Field(..., ge=0, le=1, description="Risk score 0-1")
    
    # Details
    avg_glucose_7d: Optional[float] = None
    std_deviation_7d: Optional[float] = None
    hypoglycemia_events: int = 0
    hyperglycemia_events: int = 0
    
    # Recommendations
    recommendations: List[str] = []
    
    generated_at: datetime


# ============== Recommendations Schemas ==============

class RecommendationResponse(BaseModel):
    """Response with personalized recommendations"""
    user_id: int
    recommendations: List[str]
    based_on_readings: int
    generated_at: datetime


# ============== Sync Schemas ==============

class SyncSingleRequest(BaseModel):
    """Sync a single glucose reading"""
    user_id: int
    glucose_level: float
    timestamp: datetime
    moment_of_day: Optional[str] = None


class SyncBatchRequest(BaseModel):
    """Sync multiple readings at once"""
    readings: List[GlucoseReadingCreate] = Field(..., min_length=1, max_length=1000)


class SyncResponse(BaseModel):
    """Response after sync operation"""
    status: str
    records_synced: int
    errors: Optional[List[str]] = None
    sync_id: Optional[int] = None
    message: str


# ============== Health Check Schema ==============

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    database: str
    model_loaded: bool
    timestamp: datetime
