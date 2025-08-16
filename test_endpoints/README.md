# Test Endpoints - Automated Testing Collections

Esta carpeta contiene colecciones de tests automatizados para todos los endpoints implementados en la plataforma MVP Coaching AI.

## Estructura de Tests

```
test_endpoints/
├── README.md                           # Este archivo
├── postman/                           # Colecciones Postman
│   ├── auth-service.postman_collection.json
│   ├── creator-hub.postman_collection.json
│   ├── ai-engine.postman_collection.json
│   └── channel-service.postman_collection.json
├── insomnia/                          # Colecciones Insomnia
│   ├── auth-service.insomnia.json
│   ├── creator-hub.insomnia.json
│   ├── ai-engine.insomnia.json
│   └── channel-service.insomnia.json
├── curl/                              # Scripts cURL
│   ├── auth-service.sh
│   ├── creator-hub.sh
│   ├── ai-engine.sh
│   └── channel-service.sh
├── python/                            # Tests Python con pytest
│   ├── conftest.py
│   ├── test_auth_service.py
│   ├── test_creator_hub.py
│   ├── test_ai_engine.py
│   └── test_channel_service.py
└── environments/                      # Variables de entorno
    ├── local.json
    ├── development.json
    └── production.json
```

## Configuración de Entornos

### Local Development
- Auth Service: `http://localhost:8001`
- Creator Hub: `http://localhost:8002`
- AI Engine: `http://localhost:8003`
- Channel Service: `http://localhost:8004`

### Variables de Entorno Requeridas
```json
{
  "base_url_auth": "http://localhost:8001",
  "base_url_creator": "http://localhost:8002", 
  "base_url_ai": "http://localhost:8003",
  "base_url_channel": "http://localhost:8004",
  "test_email": "test@example.com",
  "test_password": "TestPassword123!",
  "jwt_token": "{{access_token}}",
  "creator_id": "{{creator_id}}"
}
```

## Uso de las Colecciones

### Postman
1. Importar colección desde `postman/`
2. Importar environment desde `environments/local.json`
3. Ejecutar colección completa o tests individuales

### Insomnia
1. Importar workspace desde `insomnia/`
2. Configurar variables de entorno
3. Ejecutar requests individuales o en secuencia

### cURL Scripts
```bash
# Hacer ejecutables los scripts
chmod +x curl/*.sh

# Ejecutar tests de auth service
./curl/auth-service.sh

# Ejecutar todos los tests
for script in curl/*.sh; do
  echo "Running $script"
  $script
done
```

### Python Tests
```bash
# Instalar dependencias
pip install pytest httpx asyncio

# Ejecutar todos los tests
pytest python/ -v

# Ejecutar tests específicos
pytest python/test_auth_service.py -v
```

## Flujo de Tests Recomendado

### 1. Health Checks
Verificar que todos los servicios estén funcionando:
- `GET /health` en todos los servicios
- `GET /ready` en todos los servicios

### 2. Authentication Flow
1. Registrar nuevo creador
2. Login con credenciales
3. Obtener perfil actual
4. Refresh token
5. Logout

### 3. AI Engine Tests
1. Verificar estado de modelos
2. Procesar documento de prueba
3. Realizar búsqueda semántica
4. Procesar conversación con IA

### 4. WebSocket Tests
1. Conectar WebSocket
2. Enviar mensaje de prueba
3. Verificar respuesta
4. Desconectar

## Datos de Prueba

### Documentos de Test
- `test_documents/sample.pdf` - PDF de prueba
- `test_documents/sample.txt` - Texto plano
- `test_documents/sample.docx` - Documento Word

### Usuarios de Test
```json
{
  "test_creator": {
    "email": "test.creator@example.com",
    "password": "TestPassword123!",
    "full_name": "Test Creator",
    "company_name": "Test Company"
  }
}
```

## Validaciones Automatizadas

### Response Validation
- Status codes correctos
- Response time < 2s para APIs
- Response time < 5s para AI
- Schema validation con JSON Schema

### Security Tests
- JWT token validation
- Rate limiting verification
- Input sanitization tests
- CORS headers validation

### Performance Tests
- Load testing con múltiples requests
- Concurrent user simulation
- Memory usage monitoring
- Database connection pooling

## Reportes de Tests

### Coverage Reports
Los tests generan reportes de cobertura en:
- `test_endpoints/reports/coverage.html`
- `test_endpoints/reports/performance.json`

### CI/CD Integration
Los tests están configurados para ejecutarse en:
- GitHub Actions
- GitLab CI
- Jenkins
- Local pre-commit hooks

## Troubleshooting

### Errores Comunes
1. **Connection Refused**: Verificar que los servicios estén ejecutándose
2. **401 Unauthorized**: Verificar JWT token válido
3. **429 Rate Limited**: Esperar antes de reintentar
4. **503 Service Unavailable**: Verificar dependencias (DB, Redis, Ollama)

### Debug Mode
Activar logs detallados:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

### Health Check Script
```bash
#!/bin/bash
services=("8001" "8002" "8003" "8004")
for port in "${services[@]}"; do
  echo "Checking service on port $port..."
  curl -f "http://localhost:$port/health" || echo "Service on port $port is down"
done
```