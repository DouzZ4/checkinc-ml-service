"""
SQLAlchemy ORM models for PostgreSQL database
"""
from sqlalchemy import Column, Integer, Float, DateTime, String, Index
from sqlalchemy.sql import func
from .database import Base


class GlucoseReading(Base):
    """
    Mirror of the 'glucosa' table from MySQL.
    Stores historical glucose readings synchronized from Java app.
    """
    __tablename__ = "glucose_readings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    glucose_level = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    moment_of_day = Column(String(50), nullable=True)  # 'En Ayuno', 'Después de Desayuno', etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<GlucoseReading(user={self.user_id}, level={self.glucose_level}, time={self.timestamp})>"


class Prediction(Base):
    """
    Stores ML predictions made by the service.
    Useful for tracking accuracy and historical predictions.
    """
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Prediction data
    predicted_level = Column(Float, nullable=False)
    prediction_for_timestamp = Column(DateTime(timezone=True), nullable=False)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Model metadata
    model_version = Column(String(50), nullable=True)
    features_used = Column(String(500), nullable=True)  # JSON string of features
    
    # Actual value (filled in later for accuracy tracking)
    actual_level = Column(Float, nullable=True)
    error_margin = Column(Float, nullable=True)  # |predicted - actual|
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_user_prediction_time', 'user_id', 'prediction_for_timestamp'),
    )
    
    def __repr__(self):
        return f"<Prediction(user={self.user_id}, predicted={self.predicted_level}, for={self.prediction_for_timestamp})>"


class SyncLog(Base):
    """
    Logs synchronization events from Java application.
    Helps track data flow and debug sync issues.
    """
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sync_type = Column(String(50), nullable=False)  # 'initial', 'single', 'batch'
    records_count = Column(Integer, default=0)
    status = Column(String(20), nullable=False)  # 'success', 'partial', 'failed'
    error_message = Column(String(500), nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<SyncLog(type={self.sync_type}, count={self.records_count}, status={self.status})>"
