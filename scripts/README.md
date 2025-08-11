# Scripts Directory

## 📋 Scripts Esenciales

### 🐳 Docker & Infrastructure

#### `docker-build-optimized.ps1`
**Propósito**: Build optimizado de servicios Docker con cache y paralelización
**Uso**:
```powershell
# Build todos los servicios
.\scripts\docker-build-optimized.ps1

# Build servicio específico
.\scripts\docker-build-optimized.ps1 -Service auth-service

# Build paralelo sin cache
.\scripts\docker-build-optimized.ps1 -Parallel -NoCache
```

#### `docker-health-monitor.ps1`
**Propósito**: Monitoreo continuo de salud de contenedores con reinicio automático
**Uso**:
```powershell
# Monitoreo continuo
.\scripts\docker-health-monitor.ps1 -Continuous

# Monitoreo con reinicio automático
.\scripts\docker-health-monitor.ps1 -Continuous -RestartUnhealthy
```

#### `wait-for-services.py`
**Propósito**: Script Python para esperar dependencias antes de iniciar servicios
**Uso**: Se ejecuta automáticamente en los Dockerfiles
```bash
# Ejemplo de uso interno
python3 wait-for-services.py postgres:tcp://postgres:5432 redis:tcp://redis:6379 --timeout 60
```

### 🧪 Testing & Validation

#### `test-api-gateway.ps1`
**Propósito**: Testing completo del API Gateway y todos los endpoints
**Uso**:
```powershell
# Test básico
.\scripts\test-api-gateway.ps1

# Test con salida detallada
.\scripts\test-api-gateway.ps1 -Verbose

# Test con timeout personalizado
.\scripts\test-api-gateway.ps1 -TimeoutSec 30
```

#### `test-service-dependencies.ps1`
**Propósito**: Verificación de dependencias de servicios (TCP/HTTP)
**Uso**:
```powershell
# Test dependencias de un servicio específico
.\scripts\test-service-dependencies.ps1 -Service auth-service

# Test todas las dependencias
.\scripts\test-service-dependencies.ps1

# Test con timeout personalizado
.\scripts\test-service-dependencies.ps1 -Service ai-engine-service -TimeoutSec 120
```

### 🗄️ Database

#### `init-db.sql`
**Propósito**: Script de inicialización de base de datos PostgreSQL
**Uso**: Se ejecuta automáticamente al iniciar PostgreSQL por primera vez

## 🚀 Flujo de Trabajo Recomendado

### Desarrollo Local
```powershell
# 1. Build servicios
.\scripts\docker-build-optimized.ps1 -Parallel

# 2. Iniciar servicios
docker-compose up -d

# 3. Verificar dependencias
.\scripts\test-service-dependencies.ps1

# 4. Test API Gateway
.\scripts\test-api-gateway.ps1

# 5. Monitoreo continuo (opcional)
.\scripts\docker-health-monitor.ps1 -Continuous
```

### Troubleshooting
```powershell
# Si hay problemas de build
.\scripts\docker-build-optimized.ps1 -NoCache

# Si hay problemas de salud
.\scripts\docker-health-monitor.ps1 -RestartUnhealthy

# Si hay problemas de dependencias
.\scripts\test-service-dependencies.ps1 -Service <service-name> -TimeoutSec 300
```

## 📝 Notas

- **Todos los scripts están optimizados** para el entorno Windows con PowerShell
- **Los scripts de Python** (`wait-for-services.py`) funcionan en cualquier plataforma
- **Los timeouts son configurables** según las necesidades del entorno
- **El monitoreo es opcional** pero recomendado para desarrollo activo

## 🧹 Scripts Eliminados (Deuda Técnica Reducida)

Los siguientes scripts fueron eliminados por ser redundantes o prematuros:
- `bootstrap-system.sh` - Docker hace esto innecesario
- `setup-dev.*` - Docker Compose es suficiente
- `install-redis-deps.*` - Docker maneja dependencias
- `validate-env.*` - Docker Compose valida variables
- `run-migrations.*` - No implementado aún
- `vault-init.sh` - No hay Vault implementado
- `load-secrets.*` - No hay sistema de secretos
- `analyze-logs.sh` - Docker logs es suficiente
- `test-fixes.ps1` - Redundante con test-api-gateway.ps1