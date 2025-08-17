#!/bin/bash
"""
Optimized Docker Image Builder Script
Builds Docker images without cache for clean, consistent builds
Supports individual service building or all services at once
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
BUILDX_CACHE_DIR="/tmp/.buildx-cache"

# Export for Docker BuildKit
export DOCKER_BUILDKIT
export COMPOSE_DOCKER_CLI_BUILD

# Service definitions
declare -A SERVICES=(
    ["auth"]="auth-service"
    ["creator-hub"]="creator-hub-service" 
    ["ai-engine"]="ai-engine-service"
    ["channel"]="channel-service"
    ["all"]="all services"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "🐳 Docker Image Builder - Multi-Channel AI Coaching Platform"
    echo ""
    echo "Usage: $0 [SERVICE] [OPTIONS]"
    echo ""
    echo "Services:"
    echo "  auth        - Build Auth Service only"
    echo "  creator-hub - Build Creator Hub Service only"
    echo "  ai-engine   - Build AI Engine Service only"
    echo "  channel     - Build Channel Service only"
    echo "  all         - Build all services (default)"
    echo ""
    echo "Options:"
    echo "  --parallel  - Build services in parallel (faster)"
    echo "  --clean     - Clean build cache before building"
    echo "  --help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Build all services"
    echo "  $0 auth                     # Build only auth service"
    echo "  $0 all --parallel          # Build all services in parallel"
    echo "  $0 ai-engine --clean       # Clean cache and build AI engine"
    echo ""
}

# Function to clean build cache
clean_cache() {
    print_status "🧹 Cleaning Docker build cache..."
    
    # Remove buildx cache directory
    if [ -d "$BUILDX_CACHE_DIR" ]; then
        rm -rf "$BUILDX_CACHE_DIR"
        print_success "Removed buildx cache directory"
    fi
    
    # Prune Docker builder cache
    docker builder prune -f >/dev/null 2>&1 || true
    print_success "Pruned Docker builder cache"
    
    # Clean up dangling images
    docker image prune -f >/dev/null 2>&1 || true
    print_success "Cleaned dangling images"
}

# Function to setup BuildKit cache
setup_buildkit() {
    print_status "🚀 Setting up BuildKit cache..."
    mkdir -p "$BUILDX_CACHE_DIR"
    print_success "BuildKit cache directory ready"
}

# Function to build a single service
build_service() {
    local service=$1
    local start_time=$(date +%s)
    
    print_status "🔨 Building $service..."
    
    # Build with no-cache for clean build
    if docker-compose build --no-cache "$service" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_success "✅ $service built successfully in ${duration}s"
        return 0
    else
        print_error "❌ Failed to build $service"
        return 1
    fi
}

# Function to build all services
build_all_services() {
    local parallel=$1
    local start_time=$(date +%s)
    local failed_services=()
    
    print_status "🔨 Building all services..."
    
    if [ "$parallel" = "true" ]; then
        print_status "🚀 Building in parallel mode..."
        if docker-compose build --no-cache --parallel 2>&1; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))
            print_success "✅ All services built successfully in ${duration}s"
            return 0
        else
            print_error "❌ Parallel build failed"
            return 1
        fi
    else
        # Sequential build for better error handling
        for service in auth-service creator-hub-service ai-engine-service channel-service; do
            if ! build_service "$service"; then
                failed_services+=("$service")
            fi
        done
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        if [ ${#failed_services[@]} -eq 0 ]; then
            print_success "✅ All services built successfully in ${duration}s"
            return 0
        else
            print_error "❌ Failed services: ${failed_services[*]}"
            return 1
        fi
    fi
}

# Function to validate service name
validate_service() {
    local service=$1
    case $service in
        auth|creator-hub|ai-engine|channel|all)
            return 0
            ;;
        *)
            print_error "Invalid service: $service"
            echo "Valid services: auth, creator-hub, ai-engine, channel, all"
            return 1
            ;;
    esac
}

# Function to check Docker and docker-compose
check_dependencies() {
    print_status "🔍 Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Main function
main() {
    local service="all"
    local parallel=false
    local clean=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_usage
                exit 0
                ;;
            --parallel)
                parallel=true
                shift
                ;;
            --clean)
                clean=true
                shift
                ;;
            auth|creator-hub|ai-engine|channel|all)
                service=$1
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "🐳 Docker Image Builder Started"
    print_status "Service: $service"
    print_status "Parallel: $parallel"
    print_status "Clean cache: $clean"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Clean cache if requested
    if [ "$clean" = "true" ]; then
        clean_cache
        echo ""
    fi
    
    # Setup BuildKit
    setup_buildkit
    echo ""
    
    # Validate service
    if ! validate_service "$service"; then
        exit 1
    fi
    
    # Build based on service selection
    case $service in
        auth)
            build_service "auth-service"
            ;;
        creator-hub)
            build_service "creator-hub-service"
            ;;
        ai-engine)
            build_service "ai-engine-service"
            ;;
        channel)
            build_service "channel-service"
            ;;
        all)
            build_all_services "$parallel"
            ;;
    esac
    
    local exit_code=$?
    echo ""
    
    if [ $exit_code -eq 0 ]; then
        print_success "🎉 Build process completed successfully!"
        print_status "💡 Next steps:"
        print_status "   - Run 'make up' to start services"
        print_status "   - Run 'make health' to check service health"
        print_status "   - Run 'make test' to run tests"
    else
        print_error "💥 Build process failed!"
        print_status "💡 Troubleshooting tips:"
        print_status "   - Check Docker daemon is running: 'docker info'"
        print_status "   - Clean all caches: '$0 --clean'"
        print_status "   - Check logs above for specific errors"
        exit 1
    fi
}

# Run main function
main "$@"