"""
Synchronization endpoints for data transfer from Java application
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime

from ..database import get_db
from ..schemas import (
    SyncSingleRequest, SyncBatchRequest, SyncResponse,
    GlucoseReadingCreate
)
from ..models import GlucoseReading, SyncLog

router = APIRouter(
    prefix="/sync",
    tags=["synchronization"]
)


@router.post("/initial", response_model=SyncResponse)
async def initial_sync(
    request: SyncBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Initial bulk synchronization of historical data from Java app.
    
    This should be called only once when setting up the ML service.
    Uploads all historical glucose readings to PostgreSQL.
    """
    sync_log = SyncLog(
        sync_type="initial",
        records_count=0,
        status="in_progress"
    )
    db.add(sync_log)
    db.commit()
    
    try:
        synced = 0
        errors = []
        
        for reading_data in request.readings:
            try:
                # Check if reading already exists (avoid duplicates)
                existing = db.query(GlucoseReading).filter(
                    GlucoseReading.user_id == reading_data.user_id,
                    GlucoseReading.timestamp == reading_data.timestamp
                ).first()
                
                if existing:
                    continue  # Skip duplicates
                
                # Create new reading
                db_reading = GlucoseReading(
                    user_id=reading_data.user_id,
                    glucose_level=reading_data.glucose_level,
                    timestamp=reading_data.timestamp,
                    moment_of_day=reading_data.moment_of_day
                )
                db.add(db_reading)
                synced += 1
                
                # Commit in batches of 100
                if synced % 100 == 0:
                    db.commit()
                    
            except Exception as e:
                errors.append(f"Error on reading: {str(e)}")
                continue
        
        # Final commit
        db.commit()
        
        # Update sync log
        sync_log.records_count = synced
        sync_log.status = "success" if not errors else "partial"
        sync_log.completed_at = datetime.now()
        if errors:
            sync_log.error_message = "; ".join(errors[:5])  # First 5 errors
        db.commit()
        
        return SyncResponse(
            status=sync_log.status,
            records_synced=synced,
            errors=errors if errors else None,
            sync_id=sync_log.id,
            message=f"Successfully synced {synced} readings"
        )
        
    except Exception as e:
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        sync_log.completed_at = datetime.now()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/reading", response_model=SyncResponse)
async def sync_single_reading(
    request: SyncSingleRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronize a single new glucose reading from Java app.
    
    Called automatically after each new reading is saved in Java application.
    """
    try:
        # Check for duplicate
        existing = db.query(GlucoseReading).filter(
            GlucoseReading.user_id == request.user_id,
            GlucoseReading.timestamp == request.timestamp
        ).first()
        
        if existing:
            return SyncResponse(
                status="duplicate",
                records_synced=0,
                message="Reading already exists"
            )
        
        # Create new reading
        db_reading = GlucoseReading(
            user_id=request.user_id,
            glucose_level=request.glucose_level,
            timestamp=request.timestamp,
            moment_of_day=request.moment_of_day
        )
        db.add(db_reading)
        db.commit()
        db.refresh(db_reading)
        
        return SyncResponse(
            status="success",
            records_synced=1,
            message=f"Reading synced successfully (ID: {db_reading.id})"
        )
        
    except IntegrityError:
        db.rollback()
        return SyncResponse(
            status="duplicate",
            records_synced=0,
            message="Reading already exists (integrity constraint)"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/batch", response_model=SyncResponse)
async def sync_batch_readings(
    request: SyncBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronize multiple readings at once.
    
    Useful for periodic batch synchronization or catch-up operations.
    """
    sync_log = SyncLog(
        sync_type="batch",
        records_count=0,
        status="in_progress"
    )
    db.add(sync_log)
    db.commit()
    
    try:
        synced = 0
        errors = []
        
        for reading_data in request.readings:
            try:
                # Check for duplicate
                existing = db.query(GlucoseReading).filter(
                    GlucoseReading.user_id == reading_data.user_id,
                    GlucoseReading.timestamp == reading_data.timestamp
                ).first()
                
                if existing:
                    continue
                
                db_reading = GlucoseReading(
                    user_id=reading_data.user_id,
                    glucose_level=reading_data.glucose_level,
                    timestamp=reading_data.timestamp,
                    moment_of_day=reading_data.moment_of_day
                )
                db.add(db_reading)
                synced += 1
                
            except Exception as e:
                errors.append(str(e))
                continue
        
        db.commit()
        
        # Update sync log
        sync_log.records_count = synced
        sync_log.status = "success"
        sync_log.completed_at = datetime.now()
        db.commit()
        
        return SyncResponse(
            status="success",
            records_synced=synced,
            errors=errors if errors else None,
            sync_id=sync_log.id,
            message=f"Batch sync completed: {synced} readings"
        )
        
    except Exception as e:
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        sync_log.completed_at = datetime.now()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch sync failed: {str(e)}"
        )


@router.get("/status")
async def get_sync_status(db: Session = Depends(get_db)):
    """
    Get status of recent synchronization operations.
    """
    recent_syncs = db.query(SyncLog)\
        .order_by(SyncLog.started_at.desc())\
        .limit(10)\
        .all()
    
    total_readings = db.query(GlucoseReading).count()
    
    return {
        'total_readings_stored': total_readings,
        'recent_syncs': [
            {
                'id': log.id,
                'type': log.sync_type,
                'records': log.records_count,
                'status': log.status,
                'started_at': log.started_at,
                'completed_at': log.completed_at
            }
            for log in recent_syncs
        ]
    }


@router.post("/train-model")
async def trigger_model_training(
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """
    Manually trigger model training.
    
    - **user_id**: Optional. If provided, trains personalized model for this user.
    
    This can be called periodically to retrain the model with new data.
    """
    from ..ml.predictor import predictor
    
    try:
        result = predictor.train(db=db, user_id=user_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Training failed: {str(e)}"
        )
