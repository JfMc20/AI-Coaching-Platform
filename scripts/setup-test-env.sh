#!/bin/bash
# Test Environment Setup Script
# Generates secure test secrets and sets up test environment

set -e

echo "🔧 Setting up test environment..."

# Generate secure test JWT secret
TEST_JWT_SECRET=$(openssl rand -base64 32)
export TEST_JWT_SECRET_KEY="$TEST_JWT_SECRET"

echo "✅ Generated secure test JWT secret"

# Create test environment file
cat > .env.test << EOF
# Test Environment Configuration
# Generated on $(date)
# DO NOT COMMIT THIS FILE TO VERSION CONTROL

# Test Database Configuration
TEST_POSTGRES_PASSWORD=postgres
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/ai_platform_test

# Test Redis Configuration  
TEST_REDIS_URL=redis://localhost:6380/0

# Test JWT Configuration (generated)
TEST_JWT_SECRET_KEY=$TEST_JWT_SECRET

# Test Service URLs
TEST_AUTH_SERVICE_URL=http://localhost:8011
TEST_AI_ENGINE_SERVICE_URL=http://localhost:8013
TEST_CREATOR_HUB_SERVICE_URL=http://localhost:8012
TEST_CHANNEL_SERVICE_URL=http://localhost:8014

# Test AI Configuration
TEST_OLLAMA_URL=http://localhost:11435
TEST_CHROMADB_URL=http://localhost:8001

# Test Environment Settings
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=INFO
EOF

echo "✅ Created .env.test file with secure configuration"

# Make sure .env.test is in .gitignore
if ! grep -q ".env.test" .gitignore 2>/dev/null; then
    echo ".env.test" >> .gitignore
    echo "✅ Added .env.test to .gitignore"
fi

echo ""
echo "🚀 Test environment setup complete!"
echo ""
echo "To run tests:"
echo "  1. Source the test environment: source .env.test"
echo "  2. Start test services: docker-compose -f docker-compose.test.yml up -d"
echo "  3. Run tests: make test"
echo ""
echo "⚠️  Remember: .env.test contains generated secrets and should not be committed"