# Fly.io Deployment Guide for CheckInc ML Service

## 📋 Prerequisites

1. Cuenta en Fly.io (gratis): https://fly.io/app/sign-up
2. Tarjeta de crédito (solo para verificación, no se cobra en plan gratuito)

## 🔧 Step 1: Install Fly.io CLI

### Windows (PowerShell como Administrador):

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

### Verificar instalación:

```bash
fly version
```

## 🔐 Step 2: Login

```bash
fly auth login
```

Esto abrirá tu navegador para autenticarte.

## 🗄️ Step 3: Crear PostgreSQL Database

```bash
cd /c/xampp/htdocs/Check.Inc/checkinc-ml-service

# Crear app PostgreSQL
fly postgres create --name checkinc-ml-db --region mia

# Configuración sugerida:
# - Development (512MB RAM, 1GB storage) - GRATIS
# - Region: mia (Miami)
```

**Guarda la información de conexión** que te muestre.

## 🚀 Step 4: Lanzar Aplicación

```bash
# Crear y desplegar app
fly launch

# Respuestas sugeridas:
# - App name: checkinc-ml-service (o el que prefieras)
# - Region: mia (Miami - más cercano)
# - Setup PostgreSQL: No (ya lo creaste)
# - Deploy now: Yes
```

## 🔗 Step 5: Conectar Database

```bash
# Attachar la base de datos
fly postgres attach checkinc-ml-db

# Esto configura automáticamente DATABASE_URL
```

## ⚙️ Step 6: Configurar Variables de Entorno

```bash
# Configurar CORS (tu dominio Java)
fly secrets set ALLOWED_ORIGINS="http://localhost:8080,https://tu-dominio.com"

# Otras variables opcionales
fly secrets set LOG_LEVEL="INFO"
```

## 📊 Step 7: Verificar Despliegue

```bash
# Ver status
fly status

# Ver logs en tiempo real
fly logs

# Abrir en navegador
fly open
```

## ✅ Step 8: Probar API

```bash
# Health check
curl https://checkinc-ml-service.fly.dev/health

# Ver documentación
# https://checkinc-ml-service.fly.dev/docs
```

## 🔄 Step 9: Actualizar Java

En `ServicioPrediccionML.java`:

```java
private static final String ML_SERVICE_URL = "https://checkinc-ml-service.fly.dev";
```

## 📈 Comandos Útiles

```bash
# Ver apps
fly apps list

# Ver databases
fly postgres list

# Escalar (si necesitas más recursos)
fly scale memory 1024  # 1GB RAM

# Redeploy después de cambios
git push  # Fly detecta cambios automáticamente
# O manualmente:
fly deploy

# Ver configuración actual
fly config show

# SSH a la máquina (para debugging)
fly ssh console

# Ver métricas
fly dashboard
```

## 💰 Plan Gratuito Fly.io

**Incluye**:
- ✅ 3 apps
- ✅ 3 PostgreSQL databases (512MB cada una)
- ✅ 160GB bandwidth/mes
- ✅ Auto-sleep después de inactividad (free tier)

**Límites**:
- Apps duermen después de inactividad
- Primera request post-sleep toma ~5-10s (cold start)

## 🐛 Troubleshooting

### Error: "Could not find App"
```bash
fly apps create checkinc-ml-service
```

### Error: Database connection
```bash
# Ver variables de entorno
fly secrets list

# Verificar DATABASE_URL está configurado
fly ssh console -C "env | grep DATABASE"
```

### Error: Build failed
```bash
# Ver logs detallados
fly logs --app checkinc-ml-service
```

### App no responde
```bash
# Verificar que está corriendo
fly status

# Restart
fly apps restart checkinc-ml-service
```

## 🔄 Actualizar Código

```bash
# Desde la carpeta del proyecto
cd /c/xampp/htdocs/Check.Inc/checkinc-ml-service

# Hacer cambios en tu código
git add .
git commit -m "Update ML service"

# Desplegar cambios
fly deploy
```

## 📱 Monitoreo

Dashboard: https://fly.io/dashboard

- Ver métricas de CPU/RAM
- Logs en tiempo real
- Historia de deploys
- Costos (debe ser $0)

---

**¡Listo!** Tu API estará en:
```
https://checkinc-ml-service.fly.dev
```
