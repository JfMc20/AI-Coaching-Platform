# Security Architecture

## Overview

The security architecture implements defense-in-depth principles to protect creator intellectual property, user personal data, and platform integrity. The design addresses multi-tenant isolation, AI-specific security concerns, and compliance with privacy regulations including GDPR and CCPA.

## Security Principles

### Core Security Principles
1. **Zero Trust Architecture**: Never trust, always verify
2. **Principle of Least Privilege**: Minimal access rights for users and services
3. **Defense in Depth**: Multiple layers of security controls
4. **Data Minimization**: Collect and retain only necessary data
5. **Privacy by Design**: Security and privacy built into system architecture
6. **Fail Secure**: System fails to a secure state when errors occur

## Authentication and Authorization

### Multi-Factor Authentication (MFA)
```python
class MFAService:
    def __init__(self):
        self.totp_generator = TOTPGenerator()
        self.sms_service = SMSService()
        self.email_service = EmailService()
    
    async def setup_mfa(self, user_id: str, method: str) -> MFASetup:
        if method == "totp":
            secret = self.totp_generator.generate_secret()
            qr_code = self.totp_generator.generate_qr_code(secret, user_id)
            return MFASetup(secret=secret, qr_code=qr_code)
        
        elif method == "sms":
            phone_number = await self.get_user_phone(user_id)
            verification_code = self.generate_verification_code()
            await self.sms_service.send_code(phone_number, verification_code)
            return MFASetup(verification_method="sms")
    
    async def verify_mfa(
        self, 
        user_id: str, 
        code: str, 
        method: str
    ) -> bool:
        if method == "totp":
            user_secret = await self.get_user_totp_secret(user_id)
            return self.totp_generator.verify_code(user_secret, code)
        
        elif method == "sms":
            stored_code = await self.get_stored_verification_code(user_id)
            return stored_code == code and not self.is_code_expired(user_id)
```

### JWT Token Management
```python
class JWTManager:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=15)
        self.refresh_token_expire = timedelta(days=7)
    
    def create_access_token(self, user_data: dict) -> str:
        to_encode = user_data.copy()
        expire = datetime.utcnow() + self.access_token_expire
        to_encode.update({"exp": expire, "type": "access"})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        to_encode = {"user_id": user_id, "type": "refresh"}
        expire = datetime.utcnow() + self.refresh_token_expire
        to_encode.update({"exp": expire})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is blacklisted
            if await self.is_token_blacklisted(token):
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### Role-Based Access Control (RBAC)
```python
class RBACManager:
    def __init__(self):
        self.permissions = {
            "creator": [
                "read:own_data", "write:own_data", "delete:own_data",
                "read:own_users", "write:own_users",
                "read:own_analytics", "manage:own_channels"
            ],
            "admin": [
                "read:all_data", "write:all_data", "delete:all_data",
                "manage:users", "manage:system", "read:system_analytics"
            ],
            "support": [
                "read:user_data", "read:creator_data", "write:support_tickets"
            ]
        }
    
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        user_permissions = self.permissions.get(user_role, [])
        return required_permission in user_permissions
    
    def require_permission(self, permission: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                if not self.check_permission(current_user.role, permission):
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
```

## Data Protection

### Encryption at Rest
```python
class DataEncryption:
    def __init__(self):
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt PII and sensitive data before database storage"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt data when retrieving from database"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_file(self, file_path: str) -> str:
        """Encrypt files before storage"""
        with open(file_path, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = self.cipher_suite.encrypt(file_data)
        
        encrypted_file_path = f"{file_path}.encrypted"
        with open(encrypted_file_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)
        
        return encrypted_file_path
```

### Database Security
```sql
-- Row Level Security for multi-tenant isolation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy to ensure users can only access their creator's data
CREATE POLICY user_tenant_isolation ON users
    FOR ALL TO application_role
    USING (creator_id = current_setting('app.current_creator_id')::uuid);

-- Policy for creators to access only their own data
CREATE POLICY creator_data_isolation ON creators
    FOR ALL TO application_role
    USING (id = current_setting('app.current_creator_id')::uuid);

-- Audit logging for sensitive operations
CREATE TABLE security_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
    p_user_id UUID,
    p_action VARCHAR(100),
    p_resource VARCHAR(100),
    p_ip_address INET,
    p_user_agent TEXT,
    p_success BOOLEAN,
    p_details JSONB DEFAULT '{}'
) RETURNS VOID AS $$
BEGIN
    INSERT INTO security_audit_log (
        user_id, action, resource, ip_address, 
        user_agent, success, details
    ) VALUES (
        p_user_id, p_action, p_resource, p_ip_address,
        p_user_agent, p_success, p_details
    );
END;
$$ LANGUAGE plpgsql;
```

### API Security

#### Rate Limiting
```python
class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.limits = {
            "api_calls": {"limit": 1000, "window": 3600},  # 1000 per hour
            "ai_interactions": {"limit": 100, "window": 3600},  # 100 per hour
            "file_uploads": {"limit": 50, "window": 3600}  # 50 per hour
        }
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        action: str, 
        ip_address: str
    ) -> bool:
        if action not in self.limits:
            return True
        
        limit_config = self.limits[action]
        key = f"rate_limit:{action}:{user_id}:{ip_address}"
        
        current_count = await self.redis_client.get(key)
        if current_count is None:
            await self.redis_client.setex(
                key, limit_config["window"], 1
            )
            return True
        
        if int(current_count) >= limit_config["limit"]:
            return False
        
        await self.redis_client.incr(key)
        return True
    
    def rate_limit(self, action: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                user_id = getattr(request.state, "user_id", "anonymous")
                ip_address = request.client.host
                
                if not await self.check_rate_limit(user_id, action, ip_address):
                    raise HTTPException(
                        status_code=429, 
                        detail="Rate limit exceeded"
                    )
                
                return await func(request, *args, **kwargs)
            return wrapper
        return decorator
```

#### Input Validation and Sanitization
```python
class InputValidator:
    def __init__(self):
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)"
        ]
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>"
        ]
    
    def validate_input(self, input_data: str, input_type: str) -> bool:
        """Validate input against common attack patterns"""
        if input_type == "sql":
            return not any(
                re.search(pattern, input_data, re.IGNORECASE) 
                for pattern in self.sql_injection_patterns
            )
        
        elif input_type == "xss":
            return not any(
                re.search(pattern, input_data, re.IGNORECASE) 
                for pattern in self.xss_patterns
            )
        
        return True
    
    def sanitize_input(self, input_data: str) -> str:
        """Sanitize input to prevent XSS attacks"""
        # Remove potentially dangerous HTML tags and attributes
        clean_data = re.sub(r'<script[^>]*>.*?</script>', '', input_data, flags=re.IGNORECASE)
        clean_data = re.sub(r'javascript:', '', clean_data, flags=re.IGNORECASE)
        clean_data = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', clean_data, flags=re.IGNORECASE)
        
        return clean_data
```

## AI-Specific Security

### Content Filtering and Safety
```python
class ContentSafetyFilter:
    def __init__(self):
        self.toxic_classifier = pipeline(
            "text-classification",
            model="unitary/toxic-bert"
        )
        self.nsfw_detector = NSFWDetector()
        self.pii_detector = PIIDetector()
    
    async def filter_content(self, content: str) -> ContentSafetyResult:
        # Check for toxic content
        toxicity_result = self.toxic_classifier(content)
        is_toxic = toxicity_result[0]['label'] == 'TOXIC' and toxicity_result[0]['score'] > 0.7
        
        # Check for NSFW content
        is_nsfw = await self.nsfw_detector.detect(content)
        
        # Check for PII
        pii_detected = self.pii_detector.detect(content)
        
        # Determine if content should be blocked
        should_block = is_toxic or is_nsfw or len(pii_detected) > 0
        
        return ContentSafetyResult(
            is_safe=not should_block,
            toxicity_score=toxicity_result[0]['score'],
            nsfw_detected=is_nsfw,
            pii_detected=pii_detected,
            blocked_reason=self.get_block_reason(is_toxic, is_nsfw, pii_detected)
        )
    
    def get_block_reason(self, is_toxic: bool, is_nsfw: bool, pii_detected: list) -> str:
        reasons = []
        if is_toxic:
            reasons.append("toxic content")
        if is_nsfw:
            reasons.append("inappropriate content")
        if pii_detected:
            reasons.append("personal information detected")
        
        return ", ".join(reasons) if reasons else None
```

### AI Model Security
```python
class AIModelSecurity:
    def __init__(self):
        self.prompt_injection_detector = PromptInjectionDetector()
        self.output_validator = OutputValidator()
    
    async def validate_prompt(self, prompt: str, user_context: dict) -> bool:
        """Validate prompts for injection attacks"""
        # Check for prompt injection patterns
        injection_detected = await self.prompt_injection_detector.detect(prompt)
        
        if injection_detected:
            await self.log_security_event(
                user_id=user_context.get("user_id"),
                event_type="prompt_injection_attempt",
                details={"prompt": prompt[:100]}  # Log first 100 chars only
            )
            return False
        
        return True
    
    async def validate_ai_output(
        self, 
        output: str, 
        original_prompt: str,
        user_context: dict
    ) -> AIOutputValidation:
        """Validate AI output for safety and appropriateness"""
        # Check output against safety filters
        safety_result = await self.content_safety_filter.filter_content(output)
        
        # Validate output relevance to prompt
        relevance_score = await self.calculate_relevance(output, original_prompt)
        
        # Check for data leakage
        data_leakage = await self.detect_data_leakage(output, user_context)
        
        return AIOutputValidation(
            is_safe=safety_result.is_safe and not data_leakage,
            safety_result=safety_result,
            relevance_score=relevance_score,
            data_leakage_detected=data_leakage
        )
```

### Red Flag Detection and Crisis Intervention
```python
class CrisisDetectionSystem:
    def __init__(self):
        self.crisis_keywords = [
            "suicide", "kill myself", "end it all", "not worth living",
            "self harm", "cutting", "overdose", "jump off"
        ]
        self.crisis_classifier = pipeline(
            "text-classification",
            model="mental-health-crisis-detection"
        )
        self.emergency_contacts = EmergencyContactService()
    
    async def detect_crisis(
        self, 
        message: str, 
        user_context: dict,
        conversation_history: list
    ) -> CrisisDetectionResult:
        # Keyword-based detection
        keyword_matches = [
            keyword for keyword in self.crisis_keywords 
            if keyword.lower() in message.lower()
        ]
        
        # ML-based classification
        crisis_classification = self.crisis_classifier(message)
        crisis_probability = crisis_classification[0]['score']
        
        # Analyze conversation pattern
        pattern_analysis = await self.analyze_conversation_pattern(
            conversation_history
        )
        
        # Determine crisis level
        crisis_level = self.determine_crisis_level(
            keyword_matches, crisis_probability, pattern_analysis
        )
        
        if crisis_level == "HIGH":
            await self.trigger_crisis_intervention(user_context, message)
        
        return CrisisDetectionResult(
            crisis_level=crisis_level,
            crisis_probability=crisis_probability,
            keyword_matches=keyword_matches,
            intervention_triggered=crisis_level == "HIGH"
        )
    
    async def trigger_crisis_intervention(
        self, 
        user_context: dict, 
        message: str
    ):
        # Immediately escalate to human
        await self.escalate_to_human(user_context, "CRISIS_DETECTED")
        
        # Send crisis resources to user
        crisis_resources = await self.get_crisis_resources(
            user_context.get("location")
        )
        await self.send_crisis_resources(user_context["user_id"], crisis_resources)
        
        # Alert creator if appropriate
        if user_context.get("creator_id"):
            await self.alert_creator(
                user_context["creator_id"], 
                "Crisis situation detected with user"
            )
        
        # Log crisis event
        await self.log_crisis_event(user_context, message)
```

## Network Security

### API Gateway Security
```python
class APIGatewaySecurity:
    def __init__(self):
        self.waf = WebApplicationFirewall()
        self.ddos_protection = DDoSProtection()
        self.ip_whitelist = IPWhitelist()
    
    async def process_request(self, request: Request) -> SecurityCheckResult:
        client_ip = request.client.host
        
        # Check IP whitelist/blacklist
        if not await self.ip_whitelist.is_allowed(client_ip):
            return SecurityCheckResult(
                allowed=False, 
                reason="IP address blocked"
            )
        
        # DDoS protection
        if not await self.ddos_protection.check_request(request):
            return SecurityCheckResult(
                allowed=False, 
                reason="Rate limit exceeded - potential DDoS"
            )
        
        # WAF checks
        waf_result = await self.waf.analyze_request(request)
        if not waf_result.is_safe:
            return SecurityCheckResult(
                allowed=False, 
                reason=f"WAF blocked: {waf_result.threat_type}"
            )
        
        return SecurityCheckResult(allowed=True)
```

### TLS Configuration
```nginx
# Nginx SSL configuration
server {
    listen 443 ssl http2;
    server_name api.coaching-platform.com;
    
    # SSL certificates
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Compliance and Privacy

### GDPR Compliance
```python
class GDPRCompliance:
    def __init__(self):
        self.data_processor = PersonalDataProcessor()
        self.consent_manager = ConsentManager()
        self.data_retention = DataRetentionManager()
    
    async def handle_data_subject_request(
        self, 
        request_type: str, 
        user_id: str
    ) -> DataSubjectResponse:
        if request_type == "access":
            # Right to access - provide all personal data
            personal_data = await self.data_processor.extract_personal_data(user_id)
            return DataSubjectResponse(
                request_type="access",
                data=personal_data,
                format="JSON"
            )
        
        elif request_type == "portability":
            # Right to data portability
            portable_data = await self.data_processor.export_portable_data(user_id)
            return DataSubjectResponse(
                request_type="portability",
                data=portable_data,
                format="JSON"
            )
        
        elif request_type == "erasure":
            # Right to be forgotten
            await self.data_processor.anonymize_user_data(user_id)
            return DataSubjectResponse(
                request_type="erasure",
                status="completed"
            )
        
        elif request_type == "rectification":
            # Right to rectification - handled through normal update APIs
            return DataSubjectResponse(
                request_type="rectification",
                status="use_update_apis"
            )
    
    async def check_consent(self, user_id: str, purpose: str) -> bool:
        """Check if user has given consent for specific data processing purpose"""
        return await self.consent_manager.has_consent(user_id, purpose)
    
    async def record_consent(
        self, 
        user_id: str, 
        purpose: str, 
        granted: bool
    ):
        """Record user consent for data processing"""
        await self.consent_manager.record_consent(
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            timestamp=datetime.utcnow(),
            ip_address=request.client.host if request else None
        )
```

### Data Retention and Deletion
```python
class DataRetentionManager:
    def __init__(self):
        self.retention_policies = {
            "user_interactions": timedelta(days=730),  # 2 years
            "conversation_history": timedelta(days=365),  # 1 year
            "analytics_data": timedelta(days=1095),  # 3 years
            "audit_logs": timedelta(days=2555),  # 7 years
            "billing_data": timedelta(days=2555)  # 7 years (legal requirement)
        }
    
    async def apply_retention_policies(self):
        """Apply data retention policies and delete expired data"""
        for data_type, retention_period in self.retention_policies.items():
            cutoff_date = datetime.utcnow() - retention_period
            
            if data_type == "user_interactions":
                await self.delete_expired_interactions(cutoff_date)
            elif data_type == "conversation_history":
                await self.archive_old_conversations(cutoff_date)
            elif data_type == "analytics_data":
                await self.aggregate_and_delete_old_analytics(cutoff_date)
    
    async def delete_expired_interactions(self, cutoff_date: datetime):
        """Delete user interactions older than retention period"""
        query = """
        DELETE FROM user_interactions 
        WHERE created_at < %s
        """
        await self.execute_query(query, (cutoff_date,))
    
    async def anonymize_user_data(self, user_id: str):
        """Anonymize user data while preserving analytics value"""
        # Replace PII with anonymized identifiers
        anonymized_id = self.generate_anonymous_id()
        
        # Update user record
        await self.execute_query(
            "UPDATE users SET email = %s, name = %s WHERE id = %s",
            (f"anonymized_{anonymized_id}@deleted.com", "Deleted User", user_id)
        )
        
        # Anonymize conversation content
        await self.execute_query(
            "UPDATE messages SET content = '[DELETED]' WHERE conversation_id IN (SELECT id FROM conversations WHERE user_id = %s)",
            (user_id,)
        )
```

## Security Monitoring and Incident Response

### Security Event Monitoring
```python
class SecurityMonitor:
    def __init__(self):
        self.alert_manager = AlertManager()
        self.incident_response = IncidentResponseSystem()
    
    async def monitor_security_events(self):
        """Continuously monitor for security events"""
        # Monitor failed login attempts
        failed_logins = await self.get_failed_login_attempts()
        if len(failed_logins) > 10:  # Threshold
            await self.alert_manager.send_alert(
                "Multiple failed login attempts detected",
                severity="HIGH"
            )
        
        # Monitor unusual API usage patterns
        api_anomalies = await self.detect_api_anomalies()
        if api_anomalies:
            await self.alert_manager.send_alert(
                f"Unusual API usage detected: {api_anomalies}",
                severity="MEDIUM"
            )
        
        # Monitor for potential data breaches
        data_access_anomalies = await self.detect_data_access_anomalies()
        if data_access_anomalies:
            await self.incident_response.trigger_incident(
                "Potential data breach detected",
                severity="CRITICAL"
            )
    
    async def detect_api_anomalies(self) -> list:
        """Detect unusual API usage patterns"""
        # Implement anomaly detection logic
        # This could use ML models to detect unusual patterns
        pass
```

### Incident Response System
```python
class IncidentResponseSystem:
    def __init__(self):
        self.notification_service = NotificationService()
        self.security_team = SecurityTeam()
    
    async def trigger_incident(self, description: str, severity: str):
        """Trigger security incident response"""
        incident_id = self.generate_incident_id()
        
        # Log incident
        await self.log_incident(incident_id, description, severity)
        
        # Notify security team
        await self.notification_service.notify_security_team(
            incident_id, description, severity
        )
        
        # Auto-remediation for certain incident types
        if severity == "CRITICAL":
            await self.auto_remediate(incident_id, description)
    
    async def auto_remediate(self, incident_id: str, description: str):
        """Automatic remediation for critical incidents"""
        if "data breach" in description.lower():
            # Immediately revoke all active sessions
            await self.revoke_all_sessions()
            
            # Enable enhanced monitoring
            await self.enable_enhanced_monitoring()
            
            # Notify affected users
            await self.notify_affected_users()
```

This comprehensive security architecture provides multiple layers of protection while maintaining usability and compliance with privacy regulations. The implementation focuses on proactive threat detection, automated response capabilities, and robust data protection measures.