"""
CheckInc ML Service - FastAPI Main Application
Microservicio de Machine Learning para predicción de niveles de glucosa
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from .config import settings
from .database import get_db, create_tables
from .schemas import HealthResponse
from .routers import predictions, sync

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="""
    ## 🧬 CheckInc ML Service
    
    Microservicio de Machine Learning para predicción de niveles de glucosa en pacientes diabéticos.
    
    ### Funcionalidades principales:
    
    * **Predicciones**: Predice niveles de glucosa para las próximas horas
    * **Evaluación de Riesgo**: Analiza el riesgo actual basado en lecturas recientes
    * **Recomendaciones**: Genera consejos personalizados para cada paciente
    * **Sincronización**: Recibe datos desde la aplicación Java EE
    
    ### Tecnologías:
    
    * FastAPI + Python 3.10+
    * PostgreSQL Database
    * Scikit-learn (Random Forest)
    * SQLAlchemy ORM
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router, prefix=settings.api_v1_prefix)
app.include_router(sync.router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info("🚀 Starting CheckInc ML Service...")
    
    # Create database tables if they don't exist
    try:
        create_tables()
        logger.info("✓ Database tables verified/created")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
    
    # Try to load ML model
    from .ml.predictor import predictor
    if predictor.model is not None:
        logger.info(f"✓ ML model loaded (version {predictor.model_version})")
    else:
        logger.warning("⚠ ML model not found - will need training")
    
    logger.info(f"✓ Service ready at {settings.api_v1_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    logger.info("Shutting down CheckInc ML Service...")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": settings.project_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
        "message": "CheckInc ML Service - Glucose Prediction API"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring.
    
    Verifies:
    - Service is running
    - Database connection is working
    - ML model is loaded
    """
    from .ml.predictor import predictor
    
    # Test database connection
    db_status = "connected"
    try:
        db.execute("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Check if model is loaded
    model_loaded = predictor.model is not None
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version=settings.version,
        database=db_status,
        model_loaded=model_loaded,
        timestamp=datetime.now()
    )


@app.get("/stats", tags=["statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get general statistics about the service.
    """
    from .models import GlucoseReading, Prediction, SyncLog
    
    total_readings = db.query(GlucoseReading).count()
    total_predictions = db.query(Prediction).count()
    total_users = db.query(GlucoseReading.user_id).distinct().count()
    recent_syncs = db.query(SyncLog).count()
    
    return {
        "total_glucose_readings": total_readings,
        "total_predictions_made": total_predictions,
        "unique_users": total_users,
        "sync_operations": recent_syncs,
        "model_version": "1.0.0"
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": str(request.url)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred. Please try again later."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
