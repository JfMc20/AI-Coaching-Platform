---
inclusion: fileMatch
fileMatchPattern: ['.github/workflows/*.yml', '.github/workflows/*.yaml', 'docker-compose*.yml', 'scripts/*']
---

# GitHub Secrets & CI/CD Configuration

## Required GitHub Secrets

Configure these secrets in Repository Settings → Secrets and variables → Actions:

### Testing Environment Secrets
- **TEST_POSTGRES_PASSWORD**: `postgres` (PostgreSQL test database password)
- **TEST_JWT_SECRET_KEY**: `test-secret-key-for-testing-only` (JWT signing key for tests)

### Production Environment Secrets
- **POSTGRES_PASSWORD**: Strong random password for production database
- **JWT_SECRET_KEY**: Cryptographically secure key (min 256 bits)
- **ENCRYPTION_KEY**: Base64-encoded key for data encryption at rest
- **REDIS_PASSWORD**: Strong password for Redis instances

## CI/CD Security Rules

### Secret Management
- **Never hardcode secrets** in workflow files or docker-compose configurations
- **Use GitHub Secrets** for all sensitive values in CI/CD
- **Reference secrets** using `${{ secrets.SECRET_NAME }}` syntax
- **Rotate secrets monthly** for production environments

### Workflow Security
- **Restrict secret access** to specific branches (main, develop)
- **Use environment protection** rules for production deployments
- **Audit secret usage** through GitHub's audit logs
- **Validate secret presence** before running tests

### Docker Compose Security
- **Use environment variables** for all credentials
- **Provide .env.example** with placeholder values
- **Document required secrets** in README files
- **Never commit .env files** to version control

## Environment Variable Patterns

### Required Format
```yaml
# In GitHub Actions
env:
  POSTGRES_PASSWORD: ${{ secrets.TEST_POSTGRES_PASSWORD }}
  JWT_SECRET_KEY: ${{ secrets.TEST_JWT_SECRET_KEY }}
```

### Docker Compose Integration
```yaml
# In docker-compose files
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
```

## Validation Commands

### Secret Verification
```bash
# Check if secrets are properly configured
make validate-secrets

# Test CI/CD pipeline locally
make ci-test

# Verify no hardcoded credentials
make security-scan
```

### Troubleshooting
- **Case sensitivity**: Secret names must match exactly
- **Branch restrictions**: Secrets may not be available in forked PRs
- **Workflow permissions**: Ensure workflows have secret access
- **Environment context**: Check if secrets are scoped to specific environments