# Guía de Despliegue del Microservicio ML en Render

Esta guía te ayudará a desplegar el microservicio Python de Machine Learning en Render.

## ✅ Prerrequisitos

1. Cuenta en [Render.com](https://render.com) (plan gratuito disponible)
2. Cuenta de GitHub con el código subido
3. Proyecto `checkinc-ml-service` en tu repositorio

## 📋 Paso 1: Preparar el Repositorio

### 1.1 Inicializar Git en el proyecto

```bash
cd Check.Inc/checkinc-ml-service
git init
```

### 1.2 Crear `.gitignore` (ya está creado)

Verifica que `.gitignore` excluya archivos sensibles:
- `.env`
- `__pycache__/`
- `models/*.pkl`

### 1.3 Commit y Push

```bash
git add .
git commit -m "Initial commit: ML microservice for Check.Inc"

# Si es repositorio existente Check.Inc:
cd ..
git add checkinc-ml-service/
git commit -m "Add ML microservice"
git push origin main
```

## 🚀 Paso 2: Crear Servicios en Render

### 2.1 Acceder a Render Dashboard

1. Ve a https://dashboard.render.com/
2. Haz clic en **"New +"** → **"Blueprint"**

### 2.2 Conectar Repositorio

1. Selecciona **"Connect a repository"**
2. Busca tu repositorio de Check.Inc
3. Render detectará automáticamente `render.yaml`

### 2.3 Configurar Blueprint

Render creará automáticamente:
- ✅ **Web Service**: `checkinc-ml-service` (Python)
- ✅ **PostgreSQL Database**: `checkinc-ml-db`

Click **"Apply"** para desplegar.

## ⚙️ Paso 3: Configuración Avanzada (Opcional)

### 3.1 Variables de Entorno

Render configurará automáticamente `DATABASE_URL`. Variables opcionales:

| Variable | Descripción | Valor Sugerido |
|----------|-------------|----------------|
| `ALLOWED_ORIGINS` | Dominios para CORS | Tu dominio Java |
| `API_KEY` | Autenticación adicional | (opcional) |
| `LOG_LEVEL` | Nivel de logs | `INFO` |

Para añadirlas:
1. Ve a tu service → **Environment** tab
2. Click **"Add Environment Variable"**

### 3.2 Actualizar Dominios CORS

En `app/config.py`, actualiza `allowed_origins`:

```python
allowed_origins: list[str] = [
    "http://localhost:8080",
    "https://tu-dominio-java.com",  # Cambiar
    "https://checkinc-ml-service.onrender.com"
]
```

## 🗄️ Paso 4: Verificar Base de Datos

### 4.1 Conexión a DB (Opcional)

Render provee `DATABASE_URL` automáticamente. Para conectarte manualmente:

1. Ve a **Database** → **Info** tab
2. Copia las credenciales
3. Usa un cliente como pgAdmin o DBeaver

### 4.2 Datos de Conexión

```
Host: <db-host>.render.com
Database: checkinc_ml
User: checkinc_ml_user
Password: <auto-generado>
Port: 5432
```

## ✅ Paso 5: Verificar Despliegue

### 5.1 Esperar Despliegue

El primer deploy toma ~5-10 minutos:
- ⏳ Building...
- ⏳ Deploying...
- ✅ **Live**

### 5.2 Verificar Health Check

Una vez desplegado, verifica:

```bash
curl https://checkinc-ml-service.onrender.com/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "model_loaded": false,
  "timestamp": "2025-12-07T..."
}
```

> **Nota**: `model_loaded: false` es normal al inicio (no hay datos).

### 5.3 Verificar Documentación API

Accede a:
```
https://checkinc-ml-service.onrender.com/docs
```

Deberías ver la documentación Swagger interactiva.

## 🔗 Paso 6: Integrar con Aplicación Java

### 6.1 Actualizar URL en Java

En `ServicioPrediccionML.java`, cambia:

```java
private static final String ML_SERVICE_URL = "https://checkinc-ml-service.onrender.com";
```

### 6.2 Recompilar Aplicación Java

```bash
cd Check.Inc
mvn clean package
```

### 6.3 Redesplegar en GlassFish

Redespliega el WAR con la nueva configuración.

## 📊 Paso 7: Sincronización Inicial de Datos

### 7.1 Crear Endpoint Temporal (Opcional)

En tu aplicación Java, crea un endpoint para carga inicial:

```java
@WebServlet("/admin/sync-ml-initial")
public class SyncMLServlet extends HttpServlet {
    @EJB
    private GlucosaFacadeLocal glucosaFacade;
    
    @EJB
    private ServicioPrediccionML servicioML;
    
    protected void doPost(HttpServletRequest request, HttpServletResponse response) {
        // Obtener todas las glucosas
        List<Glucosa> todasGlucosas = glucosaFacade.findAll();
        
        // Preparar JSON para batch sync
        // ... código de serialización ...
        
        // Llamar a /api/v1/sync/initial
    }
}
```

### 7.2 Ejecutar Sincronización

**Opción A - Manual con cURL:**

```bash
curl -X POST https://checkinc-ml-service.onrender.com/api/v1/sync/initial \
  -H "Content-Type:application/json" \
  -d '{
    "readings": [
      {
        "user_id": 1,
        "glucose_level": 110.5,
        "timestamp": "2025-12-07T08:00:00",
        "moment_of_day": "En Ayuno"
      },
      ...
    ]
  }'
```

**Opción B - Desde Java:**

Ejecuta el servlet temporal una vez.

### 7.3 Entrenar Modelo

Una vez sincronizados los datos:

```bash
curl -X POST https://checkinc-ml-service.onrender.com/api/v1/sync/train-model
```

Respuesta esperada:
```json
{
  "status": "success",
  "samples_used": 150,
  "r2_score": 0.82,
  "mae": 12.5,
  "model_version": "1.0.0"
}
```

## 🧪 Paso 8: Pruebas

### 8.1 Registrar Nueva Glucosa

Desde tu app Java, registra una nueva lectura de glucosa. Verifica en logs que se sincroniza automáticamente.

### 8.2 Solicitar Predicción

En tu aplicación, navega a la nueva vista de Predicciones ML y verifica que se muestran correctamente.

### 8.3 Evaluar Riesgo

Prueba el endpoint de evaluación de riesgo:

```bash
curl -X POST https://checkinc-ml-service.onrender.com/api/v1/predictions/risk-assessment \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

## 📊 Monitoreo

### Ver Logs en Tiempo Real

En Render Dashboard:
1. Ve a tu service
2. Click en **"Logs"** tab
3. Logs en tiempo real

### Métricas

En **"Metrics"** tab puedes ver:
- CPU usage
- Memory usage
- Request count
- Response times

## ⚠️ Consideraciones del Plan Gratuito

**Limitaciones**:
- ⏰ El servicio "duerme" después de 15 min de inactividad
- ⚡ Primera request después de dormir toma ~30s (cold start)
- 💾 PostgreSQL: 1 GB storage

**Soluciones**:
1. **Ping periódico**: Crear tarea cron que haga ping cada 10 min
2. **Upgrade a plan pagado**: $7/mes web service + $7/mes DB

### Crear Ping Auto (Opcional)

En tu servidor Java, crea tarea programada:

```java
@Schedule(hour = "*", minute = "*/10")
public void pingMLService() {
    try {
        servicioML.verificarDisponibilidad();
    } catch (Exception e) {
        // Ignorar
    }
}
```

## 🔒 Seguridad

### Recomendaciones

1. **HTTPS**: Render provee HTTPS automáticamente ✅
2. **API Key**: Considera añadir autenticación por API key
3. **Rate Limiting**: Implementar límite de requests (futuro)
4. **CORS**: Mantener lista de dominios permitidos actualizada

### Añadir API Key (Opcional)

En Render, añade variable:
```
API_KEY=tu-clave-secreta-aqui
```

En Java, añade header:
```java
request.addHeader("X-API-Key", "tu-clave-secreta-aqui");
```

## 🛠️ Troubleshooting

### Problema: "Database not found"

**Solución**: Verifica que la DB se creó correctamente en Render Dashboard.

### Problema: "Model not loaded"

**Solución**: Entrena el modelo llamando a `/api/v1/sync/train-model`.

### Problema: "CORS error"

**Solución**: Añade tu dominio a `allowed_origins` en `config.py`.

### Problema: "Cold start muy lento"

**Solución**: Upgrade a plan pagado o implementa ping automático.

## 🎉 ¡Listo!

Tu microservicio ML está desplegado y funcionando. Ahora puedes:

✅ Obtener predicciones de glucosa  
✅ Evaluar riesgos automáticamente  
✅ Recibir recomendaciones personalizadas  
✅ Analizar patrones con Machine Learning  

---

**Next Steps**:
- Monitorear métricas y ajustar modelo
- Añadir más features al modelo ML
- Implementar notificaciones basadas en predicciones
- Crear dashboard de análisis avanzado
