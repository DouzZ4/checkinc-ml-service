# Despliegue en SaveInCloud 🚀

Guía para desplegar el servicio ML de Check.Inc en SaveInCloud.

## 📋 Requisitos de SaveInCloud

Tu entorno de SaveInCloud tiene:
- **Apache 2.4.65** con mod_wsgi
- **Python 3.14.1**
- **PostgreSQL** (servicio separado)

## 📁 Estructura de archivos

Sube estos archivos a tu contenedor:

```
/var/www/webroot/ROOT/
├── wsgi.py                 # Punto de entrada WSGI
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── predictor.py
│   │   └── trainer.py
│   └── routers/
│       ├── __init__.py
│       ├── predictions.py
│       └── sync.py
└── models/                 # Directorio para modelos ML (crear vacío)
```

## ⚙️ Paso 1: Crear base de datos PostgreSQL

En SaveInCloud, crea una base de datos PostgreSQL y ejecuta:

```sql
CREATE DATABASE checkinc_ml;
```

Anota los datos de conexión:
- Host
- Puerto
- Usuario
- Contraseña

## 🔧 Paso 2: Variables de entorno

Configura estas variables en SaveInCloud:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `DATABASE_URL` | `postgresql://usuario:pass@host:5432/checkinc_ml` | Conexión PostgreSQL |
| `ALLOWED_ORIGINS` | `https://tu-app-java.saveincloud.com` | CORS para tu app Java |
| `SECRET_KEY` | `tu_clave_secreta_larga` | Clave de seguridad |

### Ejemplo de DATABASE_URL:
```
postgresql://postgres:mi_password@postgresql-checkinc.saveincloud.com:5432/checkinc_ml
```

## 📦 Paso 3: Instalar dependencias

Conéctate por SSH a tu contenedor y ejecuta:

```bash
cd /var/www/webroot/ROOT
pip install -r requirements.txt
```

## 🔄 Paso 4: Reiniciar Apache

Después de subir los archivos:

```bash
# Si tienes acceso SSH
sudo apachectl restart

# O desde el panel de SaveInCloud, reinicia el contenedor
```

## ✅ Paso 5: Verificar funcionamiento

Accede a:
- **Health check**: `https://tu-servicio-ml.saveincloud.com/health`
- **Documentación**: `https://tu-servicio-ml.saveincloud.com/docs`

Deberías ver:
```json
{"status": "healthy", "database": "connected"}
```

## 🔗 Paso 6: Actualizar aplicación Java

En tu aplicación Java, actualiza la URL del servicio ML:

**Archivo**: `src/main/java/com/mycompany/checkinc/services/ServicioPrediccionML.java`

```java
// Línea 38 - cambiar URL
private static final String ML_SERVICE_URL = "https://tu-servicio-ml.saveincloud.com";
```

## 🔒 Configuración de CORS

Si tienes problemas de CORS, asegúrate de que `ALLOWED_ORIGINS` incluya tu dominio:

```env
ALLOWED_ORIGINS=https://tu-app-java.saveincloud.com,https://localhost:8080
```

## 🐛 Troubleshooting

### Error: "No module named 'app'"
```bash
# Verificar estructura de directorios
ls -la /var/www/webroot/ROOT/
ls -la /var/www/webroot/ROOT/app/
```

### Error: "Connection refused" a PostgreSQL
1. Verificar que PostgreSQL esté corriendo
2. Verificar credenciales en DATABASE_URL
3. Verificar que el firewall permita conexión

### Error: "Database does not exist"
```sql
CREATE DATABASE checkinc_ml;
```

### Ver logs de Apache
```bash
tail -f /var/log/apache2/error.log
```

## 📊 Endpoints disponibles

Una vez desplegado, tendrás estos endpoints:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Verificar estado |
| GET | `/docs` | Documentación Swagger |
| POST | `/api/v1/sync/reading` | Sincronizar lectura |
| POST | `/api/v1/sync/batch` | Sincronización masiva |
| POST | `/api/v1/predictions/next-hours` | Predicciones |
| POST | `/api/v1/predictions/risk-assessment` | Evaluación de riesgo |
| GET | `/api/v1/predictions/recommendations/{user_id}` | Recomendaciones |

---

**Nota**: SaveInCloud usa Apache + mod_wsgi, por eso usamos el archivo `wsgi.py` con el adaptador `a2wsgi` para convertir ASGI (FastAPI) a WSGI.
