# CheckInc ML Service 🧬

Microservicio de Machine Learning para predicción de niveles de glucosa en pacientes diabéticos. Desarrollado con FastAPI, PostgreSQL y Scikit-learn.

## 🚀 Características

- **Predicción de Glucosa**: Predice niveles futuros usando Random Forest
- **Evaluación de Riesgo**: Clasifica riesgo en bajo/medio/alto
- **Recomendaciones Personalizadas**: Genera consejos basados en patrones
- **API REST**: Endpoints bien documentados con Swagger/OpenAPI
- **Sincronización Automática**: Recibe datos desde aplicación Java EE

## 📋 Requisitos

- Python 3.10+
- PostgreSQL 12+
- pip

## ⚙️ Instalación Local

### 1. Clonar el proyecto

```bash
cd Check.Inc/checkinc-ml-service
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

Crear base de datos PostgreSQL:

```sql
CREATE DATABASE checkinc_ml;
CREATE USER checkinc_ml_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE checkinc_ml TO checkinc_ml_user;
```

### 5. Configurar variables de entorno

Copiar `.env.example` a `.env` y ajustar:

```bash
cp .env.example .env
```

Editar `.env`:
```
DATABASE_URL=postgresql://checkinc_ml_user:your_password@localhost:5432/checkinc_ml
```

### 6. Iniciar servidor

```bash
uvicorn app.main:app --reload --port 8000
```

El servicio estará disponible en: `http://localhost:8000`

## 📚 Documentación API

Una vez el servidor esté corriendo:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints Principales

### Predicciones

- `POST /api/v1/predictions/next-hours` - Predecir próximas horas
- `POST /api/v1/predictions/risk-assessment` - Evaluar riesgo
- `GET /api/v1/predictions/recommendations/{user_id}` - Obtener recomendaciones

### Sincronización

- `POST /api/v1/sync/initial` - Carga inicial masiva
- `POST /api/v1/sync/reading` - Sincronizar lectura individual
- `POST /api/v1/sync/batch` - Sincronización por lotes
- `GET /api/v1/sync/status` - Estado de sincronización

### Utilidades

- `GET /health` - Health check
- `GET /stats` - Estadísticas del servicio

## 🎯 Uso desde Java

Ejemplo de sincronización desde Java con OkHttp:

```java
OkHttpClient client = new OkHttpClient();

String json = "{"
    + "\"user_id\": 1,"
    + "\"glucose_level\": 110.5,"
    + "\"timestamp\": \"2025-12-07T14:30:00\","
    + "\"moment_of_day\": \"Después de Almuerzo\""
    + "}";

RequestBody body = RequestBody.create(
    json, 
    MediaType.parse("application/json")
);

Request request = new Request.Builder()
    .url("https://checkinc-ml-service.onrender.com/api/v1/sync/reading")
    .post(body)
    .build();

Response response = client.newCall(request).execute();
```

## 🚢 Despliegue en Render

### 1. Crear cuenta en Render

Visita [render.com](https://render.com) y crea una cuenta gratuita.

### 2. Conectar repositorio

1. Haz push de este código a GitHub
2. En Render dashboard, click "New +"
3. Selecciona "Blueprint" 
4. Conecta tu repositorio
5. Render detectará automáticamente `render.yaml`

### 3. Variables de entorno

Render configurará automáticamente `DATABASE_URL` desde la base de datos PostgreSQL.

Variables adicionales (opcionales):
- `ALLOWED_ORIGINS`: Dominios permitidos para CORS
- `API_KEY`: Clave de autenticación adicional

### 4. Deploy

Click "Apply" y Render desplegará automáticamente:
- Base de datos PostgreSQL
- Web service Python

URL del servicio: `https://checkinc-ml-service.onrender.com`

## 🧪 Testing

### Ejecutar tests

```bash
pytest tests/ -v
```

### Test de salud

```bash
curl http://localhost:8000/health
```

### Test de predicción

```bash
curl -X POST http://localhost:8000/api/v1/predictions/next-hours \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "hours_ahead": 6
  }'
```

## 📊 Modelo de Machine Learning

### Algoritmo

Random Forest Regressor con 100 árboles

### Features utilizadas

1. Hora del día (0-23)
2. Día de la semana (0-6)
3. Momento del día codificado
4. Promedio móvil 7 días
5. Desviación estándar 7 días
6. Lectura anterior
7. Tiempo desde última lectura

### Métricas

- **MAE objetivo**: < 15 mg/dL
- **R² objetivo**: > 0.75

### Re-entrenamiento

El modelo puede reentrenarse mediante:

```bash
curl -X POST http://localhost:8000/api/v1/sync/train-model
```

## 🔒 Seguridad

- **CORS** configurado para dominios específicos
- **API Key** opcional para autenticación
- **Rate Limiting** (próximamente)
- Validación de datos con Pydantic

## 📁 Estructura del Proyecto

```
checkinc-ml-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuración
│   ├── database.py          # Conexión DB
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Schemas Pydantic
│   ├── ml/
│   │   ├── predictor.py     # Modelo ML
│   │   └── trainer.py       # Entrenamiento
│   └── routers/
│       ├── predictions.py   # Endpoints predicción
│       └── sync.py          # Endpoints sincronización
├── models/                  # Modelos ML guardados
├── tests/                   # Tests
├── requirements.txt
├── render.yaml             # Config Render
├── .env.example
└── README.md
```

## 🤝 Integración con Check.Inc

Este microservicio está diseñado para integrarse con la aplicación Java EE Check.Inc mediante:

1. **Sincronización automática** de lecturas de glucosa
2. **Endpoints REST** consumidos desde Java con OkHttp
3. **Vistas JSF** que muestran predicciones y recomendaciones

Ver documentación de integración en el repositorio principal.

## 📝 Licencia

Proyecto privado - Todos los derechos reservados

## 👥 Soporte

Para preguntas o problemas, contactar al equipo de desarrollo de Check.Inc.

---

**CheckInc ML Service** v1.0.0 - Powered by FastAPI & Scikit-learn
