#!/bin/bash
# Wait for test services to be healthy with timeout and retry logic

set -e

TIMEOUT=180  # 3 minutes for test services
INTERVAL=3   # Check every 3 seconds
ELAPSED=0

echo "⏳ Waiting for test services to be healthy (timeout: ${TIMEOUT}s)..."

# Function to check Docker service health
check_docker_service_health() {
    local service=$1
    
    local health_status=$(docker-compose -f docker-compose.test.yml ps -q "$service" | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "none")
    
    if [ "$health_status" = "healthy" ]; then
        echo "✅ $service is healthy"
        return 0
    elif [ "$health_status" = "none" ]; then
        # No health check defined, check if container is running
        if docker-compose -f docker-compose.test.yml ps "$service" | grep -q "Up"; then
            echo "✅ $service is running (no health check)"
            return 0
        fi
    fi
    
    return 1
}

# Function to check PostgreSQL specifically
check_postgres_test() {
    if docker-compose -f docker-compose.test.yml exec -T postgres-test pg_isready -U postgres -d ai_platform_test > /dev/null 2>&1; then
        echo "✅ postgres-test is ready"
        return 0
    fi
    return 1
}

# Function to check Redis specifically
check_redis_test() {
    if docker-compose -f docker-compose.test.yml exec -T redis-test redis-cli ping > /dev/null 2>&1; then
        echo "✅ redis-test is ready"
        return 0
    fi
    return 1
}

while [ $ELAPSED -lt $TIMEOUT ]; do
    all_healthy=true
    
    # Check PostgreSQL test instance
    if ! check_postgres_test; then
        all_healthy=false
    fi
    
    # Check Redis test instance
    if ! check_redis_test; then
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        echo "🎉 All test services are healthy!"
        exit 0
    fi
    
    echo "⏳ Test services not ready yet, waiting ${INTERVAL}s... (${ELAPSED}/${TIMEOUT}s)"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "❌ Timeout waiting for test services to be healthy after ${TIMEOUT}s"
echo "📊 Current test service status:"
docker-compose -f docker-compose.test.yml ps
exit 1