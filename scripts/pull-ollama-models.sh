#!/bin/bash
# Pull Ollama models with retry logic and health checks

set -e

TIMEOUT=600  # 10 minutes for model pulling
RETRY_COUNT=3
RETRY_DELAY=10

echo "📥 Pulling Ollama models..."

# Function to check if Ollama is healthy
check_ollama_health() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec ollama ollama list > /dev/null 2>&1; then
            echo "✅ Ollama is healthy and ready"
            return 0
        fi
        
        echo "⏳ Waiting for Ollama to be ready (attempt $attempt/$max_attempts)..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "❌ Ollama failed to become ready after $max_attempts attempts"
    return 1
}

# Function to pull a model with retry logic
pull_model_with_retry() {
    local model=$1
    local attempt=1
    
    while [ $attempt -le $RETRY_COUNT ]; do
        echo "📥 Pulling $model (attempt $attempt/$RETRY_COUNT)..."
        
        if timeout $TIMEOUT docker-compose exec ollama ollama pull "$model"; then
            echo "✅ Successfully pulled $model"
            return 0
        else
            echo "❌ Failed to pull $model (attempt $attempt/$RETRY_COUNT)"
            if [ $attempt -lt $RETRY_COUNT ]; then
                echo "⏳ Retrying in ${RETRY_DELAY}s..."
                sleep $RETRY_DELAY
            fi
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo "❌ Failed to pull $model after $RETRY_COUNT attempts"
    return 1
}

# Check if Ollama is healthy first
if ! check_ollama_health; then
    echo "❌ Ollama is not healthy, skipping model pulls"
    exit 1
fi

# Models to pull
models=(
    "nomic-embed-text"
    "llama3.2"
)

# Pull each model
success_count=0
for model in "${models[@]}"; do
    if pull_model_with_retry "$model"; then
        success_count=$((success_count + 1))
    else
        echo "⚠️  Failed to pull $model, continuing with other models..."
    fi
done

echo "📊 Model pulling summary: $success_count/${#models[@]} models pulled successfully"

if [ $success_count -eq ${#models[@]} ]; then
    echo "🎉 All models pulled successfully!"
    exit 0
elif [ $success_count -gt 0 ]; then
    echo "⚠️  Some models failed to pull, but continuing..."
    exit 0
else
    echo "❌ No models were pulled successfully"
    exit 1
fi