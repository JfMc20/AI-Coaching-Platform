# Robust Database Management System

## Production-Ready Migration System

El proyecto incluye un sistema robusto de migraciones que elimina los problemas comunes de base de datos en desarrollo y producción.

## Essential Database Commands

```bash
# 🔍 Verificar estado de la base de datos
make db-status              # Estado completo: conexión, migraciones, tablas

# 🚀 Inicialización segura
make db-init                # Inicializar DB con migraciones apropiadas

# 🔄 Migraciones con validación
make db-migrate             # Ejecutar migraciones con validación automática

# ✅ Validación antes de aplicar
make db-validate            # Verificar seguridad antes de migrar

# 💾 Backup (solo desarrollo)
make db-backup              # Crear backup antes de cambios importantes

# 📝 Crear nueva migración
make db-create-migration    # Crear migración con auto-generación
```

## Multi-Tenant Security

### Row Level Security (RLS) Automático
- Todas las tablas incluyen políticas RLS
- Aislamiento automático por `creator_id`
- Validación de contexto de tenant
- Protección contra data leaks

### Implemented Tables
- ✅ `creators` - Gestión de usuarios/creadores
- ✅ `documents` - Knowledge base con metadatos
- ✅ `widget_configurations` - Configuración de widgets
- ✅ `conversations` - Historial de conversaciones
- ✅ `refresh_tokens`, `jwt_blacklist` - Seguridad JWT
- ✅ `audit_logs` - Auditoría completa

## For Developers

### SQLAlchemy Models Synchronized
```python
# Todos los modelos en shared/models/database.py
from shared.models.database import Document, Creator, WidgetConfiguration

# Auto-relaciones con RLS
document = Document(creator_id=creator_id, title="Test")
# RLS automáticamente filtra por creator_id
```

### Development Commands
```bash
# Estado rápido
make db-status

# Reinicio completo (cuidado!)
make db-reset               # Solo desarrollo

# Acceso directo
make db-shell               # PostgreSQL shell
make redis-shell            # Redis shell
```

## For Production

### Automatic Validations
- ❌ Rollbacks bloqueados en producción
- ✅ Validación de conexión antes de migrar
- ✅ Detección de migraciones pendientes
- ✅ Verificación de integridad de datos

### Robust Migration Script
```bash
# En contenedor
python /app/scripts/db-migration-manager.py status
python /app/scripts/db-migration-manager.py migrate --env production
```

## Common Issues Resolution

### Error: "Multiple heads detected"
- ✅ **Solved**: Sistema ahora maneja branches automáticamente

### Error: "Table already exists"
- ✅ **Solved**: Auto-detección de estado actual y stamping inteligente

### Error: "Migration timeout"
- ✅ **Solved**: Timeouts configurables y rollback automático

### Error: "RLS policy conflicts"
- ✅ **Solved**: Políticas consistentes auto-aplicadas

## Recommended Workflow

```bash
# 1. Verificar estado antes de cambios
make db-status

# 2. Crear backup si es necesario
make db-backup

# 3. Aplicar migraciones
make db-migrate

# 4. Verificar resultado
make db-status

# 5. Si hay problemas, logs detallados
docker-compose logs auth-service | grep migration
```

## Migration Best Practices

### Creating Migrations
```bash
# 1. Create migration
poetry run alembic revision --autogenerate -m "description"

# 2. Review generated migration in alembic/versions/
# 3. Apply migration
make db-migrate

# 4. Test with multi-tenant data
make test-unit tests/shared/test_database.py
```

### Migration Safety
- **Always review** auto-generated migrations
- **Test migrations** in development first
- **Backup production** before applying
- **Verify RLS policies** are maintained
- **Check performance** impact on large tables