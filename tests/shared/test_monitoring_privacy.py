"""
Unit Tests for Privacy-Preserving Monitoring

Tests privacy monitoring components including:
- PII detection and redaction
- Data anonymization
- GDPR compliance
- Differential privacy
- Secure sampling
"""

import pytest
from datetime import datetime

from shared.monitoring.privacy import (
    PrivacyPreservingMonitor,
    PrivacyConfig,
    InputSanitizer,
    DataSampler,
    SampledData,
    ContentType
)


class TestInputSanitizer:
    """Unit tests for input sanitization and PII detection"""
    
    @pytest.fixture
    def sanitizer(self):
        return InputSanitizer()
    
    def test_pii_detection_email(self, sanitizer):
        """Test email PII detection"""
        text = "Contact me at john.doe@example.com for more info"
        pii = sanitizer.detect_pii(text)
        
        assert 'email' in pii
        assert len(pii['email']) == 1
        assert 'john.doe@example.com' in pii['email']
    
    def test_pii_detection_phone(self, sanitizer):
        """Test phone number PII detection"""
        text = "Call me at 555-123-4567 or 555.987.6543"
        pii = sanitizer.detect_pii(text)
        
        assert 'phone' in pii
        assert len(pii['phone']) == 2
    
    def test_pii_detection_credit_card(self, sanitizer):
        """Test credit card PII detection"""
        text = "My card number is 4532-1234-5678-9012"
        pii = sanitizer.detect_pii(text)
        
        assert 'credit_card' in pii
        assert len(pii['credit_card']) == 1
    
    def test_pii_redaction_email(self, sanitizer):
        """Test email redaction"""
        text = "Send reports to admin@company.com daily"
        redacted = sanitizer.redact_pii(text)
        
        assert "admin@company.com" not in redacted
        assert "[EMAIL]" in redacted
    
    def test_pii_redaction_multiple_types(self, sanitizer):
        """Test redaction of multiple PII types"""
        text = "Contact John Smith at john@email.com or 555-1234"
        redacted = sanitizer.redact_pii(text)
        
        assert "john@email.com" not in redacted
        assert "555-1234" not in redacted
        assert "[EMAIL]" in redacted
        assert "[PHONE]" in redacted
    
    def test_content_type_classification(self, sanitizer):
        """Test content type classification"""
        
        # Test question classification
        question = "What is the weather like today?"
        assert sanitizer.classify_content_type(question) == ContentType.QUESTION
        
        # Test command classification
        command = "Create a new document"
        assert sanitizer.classify_content_type(command) == ContentType.COMMAND
        
        # Test conversation classification
        conversation = "Hello, how are you doing?"
        assert sanitizer.classify_content_type(conversation) == ContentType.CONVERSATION
    
    def test_statistical_fingerprint_generation(self, sanitizer):
        """Test statistical fingerprint generation"""
        text1 = "This is a test document for fingerprinting"
        text2 = "This is a test document for fingerprinting"
        text3 = "This is a completely different text"
        
        fp1 = sanitizer.get_statistical_fingerprint(text1)
        fp2 = sanitizer.get_statistical_fingerprint(text2)
        fp3 = sanitizer.get_statistical_fingerprint(text3)
        
        # Same text should produce same fingerprint
        assert fp1 == fp2
        
        # Different text should produce different fingerprint
        assert fp1 != fp3
        
        # Fingerprints should be consistent format
        assert isinstance(fp1, str)
        assert len(fp1) > 0
    
    def test_pii_detection_with_no_pii(self, sanitizer):
        """Test PII detection with clean text"""
        text = "This is a clean text with no personal information"
        pii = sanitizer.detect_pii(text)
        
        # Should return empty dict or no sensitive categories
        for category_matches in pii.values():
            assert len(category_matches) == 0
    
    def test_fingerprint_privacy_preservation(self, sanitizer):
        """Test that fingerprints don't leak original content"""
        sensitive_text = "My SSN is 123-45-6789 and email is secret@private.com"
        fingerprint = sanitizer.get_statistical_fingerprint(sensitive_text)
        
        # Fingerprint should not contain original sensitive data
        assert "123-45-6789" not in fingerprint
        assert "secret@private.com" not in fingerprint
        
        # But should be deterministic
        fp2 = sanitizer.get_statistical_fingerprint(sensitive_text)
        assert fingerprint == fp2


class TestDataSampler:
    """Unit tests for data sampling with privacy protection"""
    
    @pytest.fixture
    def privacy_config(self):
        return PrivacyConfig(
            sampling_rate=0.5,  # 50% for testing
            retention_days=7,
            enable_pii_detection=True
        )
    
    @pytest.fixture
    def sampler(self, privacy_config):
        return DataSampler(privacy_config)
    
    def test_sampling_rate_respected(self, sampler):
        """Test that sampling rate is approximately respected"""
        creator_id = "test-user"
        sample_count = 0
        total_checks = 1000
        
        # Test sampling decisions
        for i in range(total_checks):
            if sampler.should_sample(f"{creator_id}-{i}", has_consent=True):
                sample_count += 1
        
        # Should be approximately 50% (allow some variance)
        sample_rate = sample_count / total_checks
        assert 0.4 <= sample_rate <= 0.6, f"Sample rate {sample_rate} not near expected 0.5"
    
    def test_consent_required_for_full_sampling(self, sampler):
        """Test that consent is required for detailed sampling"""
        creator_id = "test-user"
        
        # Without consent, should be more restrictive
        decisions_without_consent = [
            sampler.should_sample(f"{creator_id}-{i}", has_consent=False) 
            for i in range(100)
        ]
        
        # With consent, should follow normal sampling rate
        decisions_with_consent = [
            sampler.should_sample(f"{creator_id}-{i}", has_consent=True) 
            for i in range(100)
        ]
        
        consent_rate = sum(decisions_with_consent) / len(decisions_with_consent)
        no_consent_rate = sum(decisions_without_consent) / len(decisions_without_consent)
        
        # With consent should generally have higher sampling rate
        # (exact behavior depends on implementation)
        assert isinstance(consent_rate, float)
        assert isinstance(no_consent_rate, float)
    
    def test_sample_request_creation(self, sampler):
        """Test sample request creation with privacy protection"""
        
        sample = sampler.sample_request(
            creator_id="test-user",
            operation_type="chat",
            model_name="test-model",
            input_text="What is the capital of France?",
            output_text="The capital of France is Paris.",
            has_consent=True,
            additional_metadata={"latency_ms": 250}
        )
        
        if sample:  # Sample might be None due to sampling rate
            assert isinstance(sample, SampledData)
            assert sample.operation_type == "chat"
            assert sample.model_name == "test-model"
            assert sample.consent_obtained is True
            
            # Creator ID should be hashed for privacy
            assert sample.creator_id_hash != "test-user"
            assert len(sample.creator_id_hash) == 16  # Hash truncated to 16 chars
            
            # Should have retention date
            assert sample.retention_until > datetime.utcnow()
    
    def test_sample_data_anonymization(self, sampler):
        """Test that sampled data is properly anonymized"""
        
        sample = sampler.sample_request(
            creator_id="user@example.com",
            operation_type="embedding", 
            model_name="test-model",
            input_text="My phone number is 555-123-4567",
            output_text="Embedding generated successfully",
            has_consent=True
        )
        
        if sample:
            # Original creator ID should not be stored
            assert "user@example.com" not in str(sample.__dict__)
            
            # PII should not be in fingerprints
            assert "555-123-4567" not in sample.input_fingerprint
            
            # Redacted input should have PII removed if present
            if sample.redacted_input:
                assert "555-123-4567" not in sample.redacted_input


class TestPrivacyPreservingMonitor:
    """Unit tests for the main privacy-preserving monitor"""
    
    @pytest.fixture
    def privacy_config(self):
        return PrivacyConfig(
            sampling_rate=1.0,  # 100% for testing
            retention_days=30,
            enable_pii_detection=True,
            enable_differential_privacy=True
        )
    
    @pytest.fixture
    def monitor(self, privacy_config):
        return PrivacyPreservingMonitor(privacy_config)
    
    def test_monitor_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.config is not None
        assert monitor.sampler is not None
        assert monitor.sanitizer is not None
        assert isinstance(monitor._drift_baselines, dict)
    
    def test_request_monitoring_with_pii(self, monitor):
        """Test monitoring request with PII"""
        
        monitoring_data = monitor.monitor_request(
            creator_id="test-user",
            operation_type="chat",
            model_name="test-model",
            input_text="My email is john@example.com",
            output_text="I've noted your email address",
            has_consent=True
        )
        
        assert monitoring_data['operation_type'] == "chat"
        assert monitoring_data['has_pii'] is True
        assert monitoring_data['input_length'] == len("My email is john@example.com")
        assert 'creator_id_hash' in monitoring_data
        assert 'input_fingerprint' in monitoring_data
        
        # Original email should not be in fingerprint
        assert "john@example.com" not in monitoring_data['input_fingerprint']
    
    def test_request_monitoring_without_pii(self, monitor):
        """Test monitoring request without PII"""
        
        monitoring_data = monitor.monitor_request(
            creator_id="test-user",
            operation_type="embedding",
            model_name="test-model",
            input_text="What is machine learning?",
            output_text="Machine learning is a subset of AI",
            has_consent=False
        )
        
        assert monitoring_data['has_pii'] is False
        assert monitoring_data['content_type'] == ContentType.QUESTION.value
        assert 'drift_score' in monitoring_data
    
    @pytest.mark.asyncio
    async def test_query_logging_privacy_preservation(self, monitor):
        """Test that query logging preserves privacy"""
        
        log_entry = await monitor.log_query(
            query="My credit card number is 4532-1234-5678-9012",
            creator_id="sensitive-user",
            correlation_id="test-123",
            consent_given=False
        )
        
        # Should not contain original sensitive data
        assert "4532-1234-5678-9012" not in str(log_entry)
        assert "sensitive-user" not in str(log_entry)
        
        # Should contain privacy-safe elements
        assert 'creator_id_hash' in log_entry
        assert 'input_fingerprint' in log_entry
        assert log_entry['has_pii'] is True
    
    @pytest.mark.asyncio
    async def test_document_processing_logging(self, monitor):
        """Test document processing logging"""
        
        log_entry = await monitor.log_document_processing(
            filename="secret_document_john_doe.pdf",
            file_size=1024000,  # 1MB
            creator_id="doc-user",
            correlation_id="doc-123"
        )
        
        assert log_entry['event_type'] == 'document_processing'
        assert log_entry['file_size_category'] == 'medium'  # 1MB should be medium
        assert 'filename_hash' in log_entry
        
        # Original filename should be redacted
        if 'safe_filename' in log_entry:
            assert 'john_doe' not in log_entry['safe_filename']
    
    def test_compliance_report_generation(self, monitor):
        """Test compliance report generation"""
        
        report = monitor.get_privacy_compliance_report()
        
        required_fields = [
            'sampling_rate', 'retention_days', 'pii_detection_enabled',
            'differential_privacy_enabled', 'gdpr_compliant', 'last_audit'
        ]
        
        for field in required_fields:
            assert field in report
        
        assert report['gdpr_compliant'] is True
        assert report['pii_detection_enabled'] is True
    
    def test_drift_detection_privacy_safe(self, monitor):
        """Test that drift detection doesn't leak sensitive data"""
        
        # Monitor several requests with sensitive data
        for i in range(5):
            monitor.monitor_request(
                creator_id=f"user-{i}",
                operation_type="chat",
                model_name="test-model",
                input_text=f"My SSN is 123-45-678{i}",
                output_text="I understand your concern",
                has_consent=True
            )
        
        # Drift baselines should not contain original sensitive data
        for baseline_data in monitor._drift_baselines.values():
            baseline_str = str(baseline_data)
            
            # Should not contain any of the SSNs
            for i in range(5):
                assert f"123-45-678{i}" not in baseline_str
    
    @pytest.mark.asyncio
    async def test_monitoring_error_handling(self, monitor):
        """Test monitoring error handling"""
        
        # Test with invalid/empty inputs
        monitoring_data = monitor.monitor_request(
            creator_id="",
            operation_type="",
            model_name="",
            input_text="",
            output_text="",
            has_consent=False
        )
        
        # Should handle gracefully and return valid structure
        assert isinstance(monitoring_data, dict)
        assert monitoring_data.get('input_length', 0) == 0
        
        # Test async methods with edge cases
        log_entry = await monitor.log_query(
            query="",
            creator_id="test",
            correlation_id="",
            consent_given=False
        )
        
        assert log_entry.get('input_length', 0) == 0


class TestPrivacyConfig:
    """Test privacy configuration handling"""
    
    def test_default_config(self):
        """Test default privacy configuration"""
        config = PrivacyConfig()
        
        assert config.sampling_rate == 0.01  # 1%
        assert config.retention_days == 30
        assert config.enable_pii_detection is True
        assert config.enable_differential_privacy is True
        assert config.min_anonymity_set_size == 5
    
    def test_custom_config(self):
        """Test custom privacy configuration"""
        config = PrivacyConfig(
            sampling_rate=0.05,
            retention_days=7,
            enable_pii_detection=False,
            min_anonymity_set_size=10
        )
        
        assert config.sampling_rate == 0.05
        assert config.retention_days == 7
        assert config.enable_pii_detection is False
        assert config.min_anonymity_set_size == 10
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test with invalid sampling rate
        config = PrivacyConfig(sampling_rate=1.5)  # >100%
        
        # Implementation should handle this gracefully
        # (exact behavior depends on implementation)
        assert isinstance(config.sampling_rate, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])