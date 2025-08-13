#!/bin/bash
# Wait for services to be healthy with timeout and retry logic

set -e

TIMEOUT=300  # 5 minutes
INTERVAL=5   # Check every 5 seconds
ELAPSED=0

echo "⏳ Waiting for services to be healthy (timeout: ${TIMEOUT}s)..."

# Function to check service health
check_service_health() {
    local service=$1
    local health_endpoint=$2
    
    if curl -f -s "$health_endpoint" > /dev/null 2>&1; then
        echo "✅ $service is healthy"
        return 0
    else
        return 1
    fi
}

# Function to check Docker service health
check_docker_service_health() {
    local service=$1
    
    local health_status=$(docker-compose ps -q "$service" | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")
    
    if [ "$health_status" = "healthy" ]; then
        echo "✅ $service is healthy"
        return 0
    elif [ "$health_status" = "none" ]; then
        # No health check defined, check if container is running
        if docker-compose ps "$service" | grep -q "Up"; then
            echo "✅ $service is running (no health check)"
            return 0
        fi
    fi
    
    return 1
}

# Wait for core infrastructure services
services_to_check=(
    "postgres:5432"
    "redis:6379"
    "ollama:11434"
    "chromadb:8000"
)

while [ $ELAPSED -lt $TIMEOUT ]; do
    all_healthy=true
    
    # Check PostgreSQL
    if ! check_docker_service_health "postgres"; then
        all_healthy=false
    fi
    
    # Check Redis
    if ! check_docker_service_health "redis"; then
        all_healthy=false
    fi
    
    # Check Ollama
    if ! check_service_health "Ollama" "http://localhost:11434/api/tags"; then
        all_healthy=false
    fi
    
    # Check ChromaDB
    if ! check_service_health "ChromaDB" "http://localhost:8000/api/v1/heartbeat"; then
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        echo "🎉 All services are healthy!"
        exit 0
    fi
    
    echo "⏳ Some services not ready yet, waiting ${INTERVAL}s... (${ELAPSED}/${TIMEOUT}s)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "❌ Timeout waiting for services to be healthy after ${TIMEOUT}s"
echo "📊 Current service status:"
docker-compose ps
exit 1