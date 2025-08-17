# Security Architecture

## Authentication & Authorization

### JWT Implementation
- **Algorithm**: RS256 for asymmetric signing
- **Token Lifecycle**: 15-minute access tokens, 30-day refresh tokens
- **Token Rotation**: Automatic refresh with blacklisting
- **Storage**: Redis-based blacklisting for revoked tokens

### Multi-Factor Authentication (Planned)
- **TOTP**: Time-based one-time passwords
- **SMS**: Backup authentication method
- **Recovery Codes**: Account recovery options

### Role-Based Access Control (RBAC)
- **Roles**: creator, admin, user
- **Permissions**: Granular access control
- **Inheritance**: Role hierarchy and permission inheritance
- **Enforcement**: Decorator-based authorization in endpoints

## Multi-Tenant Security

### Row Level Security (RLS)
- **Database-level isolation**: PostgreSQL RLS policies
- **Automatic filtering**: All queries filtered by creator_id
- **Context management**: Session-based tenant context
- **Policy enforcement**: Prevents cross-tenant data access

### Tenant Isolation
```python
# Required pattern for all database operations
async def get_tenant_session(
    creator_id: str = Depends(get_current_creator_id),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncSession:
    await session.execute(
        text("SET app.current_creator_id = :creator_id"), 
        {"creator_id": creator_id}
    )
    return session
```

## Data Protection

### Password Security
- **Hashing**: Argon2 with configurable parameters
- **Strength validation**: Minimum complexity requirements
- **Breach detection**: Common password filtering
- **Reset flows**: Secure password reset with expiration

### Input Validation
- **Pydantic models**: Type-safe request/response validation
- **SQL injection prevention**: Parameterized queries only
- **XSS protection**: Content Security Policy headers
- **File upload security**: Type validation and malware scanning

### Encryption
- **Data in transit**: TLS 1.3 for all communications
- **Data at rest**: Database-level encryption
- **API keys**: Secure generation and storage
- **Secrets management**: Environment-based configuration

## Rate Limiting & DDoS Protection

### Redis-based Rate Limiting
- **Per-endpoint limits**: Configurable thresholds
- **Per-user limits**: User-specific rate limiting
- **Sliding window**: Precise rate limit calculation
- **Distributed**: Multi-instance rate limit sharing

### Brute Force Protection
- **Login attempts**: Progressive delays and lockouts
- **Account lockout**: Temporary account suspension
- **IP blocking**: Automatic IP-based blocking
- **Monitoring**: Real-time attack detection

## Compliance & Privacy

### GDPR Compliance
- **Data portability**: Export user data in structured format
- **Right to deletion**: Complete data removal
- **Consent management**: Explicit consent tracking
- **Data minimization**: Collect only necessary data

### Audit Logging
- **Comprehensive logging**: All sensitive operations
- **Tamper-evident**: Cryptographic log integrity
- **Retention policies**: Automated log cleanup
- **Correlation IDs**: Request tracing across services

### PII Protection
- **Data classification**: Automatic PII detection
- **Anonymization**: Data anonymization for analytics
- **Access controls**: Strict PII access permissions
- **Retention limits**: Automatic PII data expiration