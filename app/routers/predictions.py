"""
Prediction endpoints for glucose level forecasting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..schemas import (
    PredictionRequest, PredictionResponse, PredictionPoint,
    RiskAssessmentRequest, RiskAssessmentResponse,
    RecommendationResponse
)
from ..ml.predictor import predictor
from ..models import GlucoseReading

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"]
)


@router.post("/next-hours", response_model=PredictionResponse)
async def predict_next_hours(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """
    Predict glucose levels for the next N hours.
    
    - **user_id**: ID del usuario
    - **hours_ahead**: Número de horas a predecir (1-24)
    
    Returns predictions with timestamps and confidence scores.
    """
    try:
        predictions = predictor.predict_next_hours(
            db=db,
            user_id=request.user_id,
            hours_ahead=request.hours_ahead
        )
        
        prediction_points = [
            PredictionPoint(**pred) for pred in predictions
        ]
        
        return PredictionResponse(
            user_id=request.user_id,
            predictions=prediction_points,
            model_version=predictor.model_version,
            generated_at=datetime.now()
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating predictions: {str(e)}"
        )


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_risk(
    request: RiskAssessmentRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate current risk level based on recent glucose readings.
    
    - **user_id**: ID del usuario
    
    Returns risk level (bajo/medio/alto), statistics, and event counts.
    """
    try:
        risk_data = predictor.assess_risk(db=db, user_id=request.user_id)
        
        # Get recommendations
        recommendations = predictor.get_recommendations(db=db, user_id=request.user_id)
        
        return RiskAssessmentResponse(
            user_id=request.user_id,
            risk_level=risk_data['risk_level'],
            risk_score=risk_data['risk_score'],
            avg_glucose_7d=risk_data.get('avg_glucose_7d'),
            std_deviation_7d=risk_data.get('std_deviation_7d'),
            hypoglycemia_events=risk_data.get('hypoglycemia_events', 0),
            hyperglycemia_events=risk_data.get('hyperglycemia_events', 0),
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assessing risk: {str(e)}"
        )


@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations for a user.
    
    - **user_id**: ID del usuario
    """
    try:
        # Count readings used
        count = db.query(GlucoseReading)\
            .filter(GlucoseReading.user_id == user_id)\
            .count()
        
        recommendations = predictor.get_recommendations(db=db, user_id=user_id)
        
        return RecommendationResponse(
            user_id=user_id,
            recommendations=recommendations,
            based_on_readings=count,
            generated_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/history/{user_id}")
async def get_prediction_history(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get historical predictions for a user.
    
    - **user_id**: ID del usuario
    - **limit**: Number of predictions to return (default 50)
    """
    from ..models import Prediction
    
    predictions = db.query(Prediction)\
        .filter(Prediction.user_id == user_id)\
        .order_by(Prediction.created_at.desc())\
        .limit(limit)\
        .all()
    
    return {
        'user_id': user_id,
        'count': len(predictions),
        'predictions': [
            {
                'id': p.id,
                'predicted_level': p.predicted_level,
                'prediction_for': p.prediction_for_timestamp,
                'confidence': p.confidence_score,
                'actual_level': p.actual_level,
                'created_at': p.created_at
            }
            for p in predictions
        ]
    }
