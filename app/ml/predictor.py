"""
Machine Learning predictor for glucose levels
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from sqlalchemy.orm import Session
from ..models import GlucoseReading, Prediction
from ..config import settings


class GlucosePredictor:
    """
    Predicts future glucose levels using Random Forest Regressor.
    Uses historical data to make predictions.
    """
    
    
    def __init__(self, ml_model_path: str = None):
        self.ml_model_path = ml_model_path or settings.ml_model_path
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.model_version = "1.0.0"
        
        # Try to load existing model
        if os.path.exists(self.ml_model_path):
            self.load_model()
        else:
            # Initialize new model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.scaler = StandardScaler()
    
    def load_model(self):
        """Load trained model from disk"""
        try:
            data = joblib.load(self.ml_model_path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.model_version = data.get('version', '1.0.0')
            print(f"✓ Model loaded from {self.ml_model_path}")
        except Exception as e:
            print(f"⚠ Could not load model: {e}")
            self.model = None
            self.scaler = None
    
    def save_model(self):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(self.ml_model_path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'version': self.model_version
        }, self.ml_model_path)
        print(f"✓ Model saved to {self.ml_model_path}")
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from glucose readings dataframe.
        
        Features:
        - hour_of_day: 0-23
        - day_of_week: 0-6
        - moment_encoded: categorical encoding
        - avg_7d: rolling average last 7 days
        - std_7d: rolling std dev last 7 days
        - prev_reading: previous glucose level
        - time_since_last: hours since last reading
        """
        df = df.copy()
        df = df.sort_values('timestamp')
        
        # Time-based features
        df['hour_of_day'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Moment encoding
        moment_mapping = {
            'En Ayuno': 0,
            'Antes de Desayuno': 1,
            'Después de Desayuno': 2,
            'Antes de Almuerzo': 3,
            'Después de Almuerzo': 4,
            'Antes de Cena': 5,
            'Después de Cena': 6
        }
        df['moment_encoded'] = df['moment_of_day'].map(moment_mapping).fillna(0)
        
        # Rolling statistics (7 days)
        df['avg_7d'] = df['glucose_level'].rolling(window=7, min_periods=1).mean()
        df['std_7d'] = df['glucose_level'].rolling(window=7, min_periods=1).std().fillna(0)
        
        # Previous reading
        df['prev_reading'] = df['glucose_level'].shift(1).fillna(df['glucose_level'].mean())
        
        # Time since last reading (in hours)
        df['time_since_last'] = df['timestamp'].diff().dt.total_seconds() / 3600
        df['time_since_last'] = df['time_since_last'].fillna(24)
        
        return df
    
    def train(self, db: Session, user_id: int = None) -> Dict:
        """
        Train the model with historical data.
        
        Args:
            db: Database session
            user_id: If provided, train only on this user's data (personalized model)
        
        Returns:
            Dictionary with training metrics
        """
        # Fetch historical data
        query = db.query(GlucoseReading)
        if user_id:
            query = query.filter(GlucoseReading.user_id == user_id)
        
        readings = query.order_by(GlucoseReading.timestamp).all()
        
        if len(readings) < settings.min_training_samples:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least {settings.min_training_samples} readings, got {len(readings)}'
            }
        
        # Convert to DataFrame
        data = [{
            'user_id': r.user_id,
            'glucose_level': r.glucose_level,
            'timestamp': r.timestamp,
            'moment_of_day': r.moment_of_day
        } for r in readings]
        
        df = pd.DataFrame(data)
        
        # Prepare features
        df = self.prepare_features(df)
        
        # Feature columns
        feature_cols = [
            'hour_of_day', 'day_of_week', 'moment_encoded',
            'avg_7d', 'std_7d', 'prev_reading', 'time_since_last'
        ]
        
        X = df[feature_cols].values
        y = df['glucose_level'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        
        # Calculate metrics
        train_score = self.model.score(X_scaled, y)
        predictions = self.model.predict(X_scaled)
        mae = np.mean(np.abs(predictions - y))
        
        # Save model
        self.save_model()
        
        return {
            'status': 'success',
            'samples_used': len(df),
            'r2_score': train_score,
            'mae': mae,
            'model_version': self.model_version
        }
    
    def predict_next_hours(
        self, 
        db: Session, 
        user_id: int, 
        hours_ahead: int = 6
    ) -> List[Dict]:
        """
        Predict glucose levels for the next N hours.
        
        Args:
            db: Database session
            user_id: User ID to predict for
            hours_ahead: Number of hours to predict (1-24)
        
        Returns:
            List of predictions with timestamps and confidence scores
        """
        if self.model is None:
            raise ValueError("Model not trained yet. Call train() first.")
        
        # Get recent readings for this user
        recent_readings = db.query(GlucoseReading)\
            .filter(GlucoseReading.user_id == user_id)\
            .order_by(GlucoseReading.timestamp.desc())\
            .limit(30)\
            .all()
        
        if len(recent_readings) < 5:
            raise ValueError(f"Insufficient data for user {user_id}. Need at least 5 readings.")
        
        # Convert to DataFrame
        data = [{
            'user_id': r.user_id,
            'glucose_level': r.glucose_level,
            'timestamp': r.timestamp,
            'moment_of_day': r.moment_of_day
        } for r in reversed(recent_readings)]
        
        df = pd.DataFrame(data)
        df = self.prepare_features(df)
        
        # Get last reading info
        last_reading = df.iloc[-1]
        last_timestamp = last_reading['timestamp']
        last_glucose = last_reading['glucose_level']
        
        # Generate predictions
        predictions = []
        current_glucose = last_glucose
        
        for hour in range(1, hours_ahead + 1):
            future_time = last_timestamp + timedelta(hours=hour)
            
            # Create feature vector
            features = np.array([[
                future_time.hour,  # hour_of_day
                future_time.weekday(),  # day_of_week
                0,  # moment_encoded (unknown)
                df['avg_7d'].iloc[-1],  # avg_7d
                df['std_7d'].iloc[-1],  # std_7d
                current_glucose,  # prev_reading
                1  # time_since_last (1 hour)
            ]])
            
            # Scale and predict
            features_scaled = self.scaler.transform(features)
            predicted_level = self.model.predict(features_scaled)[0]
            
            # Calculate confidence (simplified)
            confidence = max(0.5, 1.0 - (hour * 0.05))  # Decreases with time
            
            predictions.append({
                'timestamp': future_time,
                'predicted_level': round(float(predicted_level), 2),
                'confidence_score': round(confidence, 2)
            })
            
            # Update for next iteration
            current_glucose = predicted_level
        
        # Save predictions to database
        for pred in predictions:
            db_prediction = Prediction(
                user_id=user_id,
                predicted_level=pred['predicted_level'],
                prediction_for_timestamp=pred['timestamp'],
                confidence_score=pred['confidence_score'],
                model_version=self.model_version
            )
            db.add(db_prediction)
        
        db.commit()
        
        return predictions
    
    def assess_risk(self, db: Session, user_id: int) -> Dict:
        """
        Assess current risk level based on recent readings.
        
        Returns:
            Dictionary with risk level, score, and details
        """
        # Get last 30 days of readings
        cutoff_date = datetime.now() - timedelta(days=30)
        
        readings = db.query(GlucoseReading)\
            .filter(
                GlucoseReading.user_id == user_id,
                GlucoseReading.timestamp >= cutoff_date
            )\
            .all()
        
        if len(readings) < 5:
            return {
                'risk_level': 'desconocido',
                'risk_score': 0.0,
                'message': 'Datos insuficientes para evaluación'
            }
        
        levels = [r.glucose_level for r in readings]
        
        # Calculate statistics
        avg_glucose = np.mean(levels)
        std_dev = np.std(levels)
        
        # Count critical events
        hypoglycemia = sum(1 for level in levels if level < 70)
        hyperglycemia = sum(1 for level in levels if level > 180)
        
        # Calculate risk score (0-1)
        risk_score = 0.0
        
        # Factor 1: Average glucose deviation from target (80-130)
        if avg_glucose < 80:
            risk_score += 0.3
        elif avg_glucose > 130:
            risk_score += 0.2 * min((avg_glucose - 130) / 70, 1.0)
        
        # Factor 2: Variability
        if std_dev > 30:
            risk_score += 0.2
        
        # Factor 3: Critical events
        risk_score += min(hypoglycemia * 0.1, 0.3)
        risk_score += min(hyperglycemia * 0.05, 0.2)
        
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score < 0.3:
            risk_level = 'bajo'
        elif risk_score < 0.6:
            risk_level = 'medio'
        else:
            risk_level = 'alto'
        
        return {
            'risk_level': risk_level,
            'risk_score': round(risk_score, 2),
            'avg_glucose_7d': round(avg_glucose, 2),
            'std_deviation_7d': round(std_dev, 2),
            'hypoglycemia_events': hypoglycemia,
            'hyperglycemia_events': hyperglycemia
        }
    
    def get_recommendations(self, db: Session, user_id: int) -> List[str]:
        """
        Generate personalized recommendations based on user's data.
        """
        risk_data = self.assess_risk(db, user_id)
        recommendations = []
        
        # Based on average glucose
        avg = risk_data.get('avg_glucose_7d', 100)
        if avg > 150:
            recommendations.append("Tu promedio de glucosa está elevado. Considera revisar tu plan de alimentación con tu médico.")
        elif avg < 80:
            recommendations.append("Tu promedio de glucosa está bajo. Habla con tu médico sobre ajustar tu medicación.")
        else:
            recommendations.append("Tu promedio de glucosa está en rango objetivo. ¡Excelente trabajo!")
        
        # Based on variability
        std = risk_data.get('std_deviation_7d', 0)
        if std > 30:
            recommendations.append("Tus niveles de glucosa varían mucho. Intenta mantener horarios regulares de comida.")
        
        # Based on critical events
        hypo = risk_data.get('hypoglycemia_events', 0)
        if hypo > 2:
            recommendations.append(f"Has tenido {hypo} episodios de hipoglucemia. Considera tener snacks de emergencia disponibles.")
        
        hyper = risk_data.get('hyperglycemia_events', 0)
        if hyper > 5:
            recommendations.append(f"Has tenido {hyper} episodios de hiperglucemia. Revisa tu plan de tratamiento con tu médico.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Continúa monitoreando tus niveles regularmente.")
        
        recommendations.append("Recuerda: este sistema es de apoyo. Siempre consulta con tu médico.")
        
        return recommendations


# Global predictor instance
predictor = GlucosePredictor()
